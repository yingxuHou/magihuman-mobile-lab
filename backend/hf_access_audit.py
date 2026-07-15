import argparse
import json
import os
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


HUGGINGFACE_TOKEN_NAMES = ["HF_TOKEN", "HUGGINGFACE_HUB_TOKEN"]

PROFILE_PROBES = {
    "p01": [
        {
            "repo_id": "GAIR/daVinci-MagiHuman",
            "probe_path": "base/model-00003-of-00007.safetensors",
            "gate": "none",
            "purpose": "P01 base checkpoint access",
        },
        {
            "repo_id": "GAIR/daVinci-MagiHuman",
            "probe_path": "turbo_vae/checkpoint-340000.ckpt",
            "gate": "none",
            "purpose": "P01 VAE checkpoint access",
        },
        {
            "repo_id": "google/t5gemma-9b-9b-ul2",
            "probe_path": "model-00007-of-00009.safetensors",
            "gate": "manual",
            "purpose": "text encoder gated access",
        },
        {
            "repo_id": "stabilityai/stable-audio-open-1.0",
            "probe_path": "model.ckpt",
            "gate": "auto",
            "purpose": "audio model gated access",
        },
        {
            "repo_id": "Wan-AI/Wan2.2-TI2V-5B",
            "probe_path": "models_t5_umt5-xxl-enc-bf16.pth",
            "gate": "none",
            "purpose": "Wan VAE access",
        },
    ],
}

PROFILE_PROBES["required_suite"] = PROFILE_PROBES["p01"] + [
    {
        "repo_id": "GAIR/daVinci-MagiHuman",
        "probe_path": "540p_sr/model-00013-of-00013.safetensors",
        "gate": "none",
        "purpose": "540p SR checkpoint access",
    },
    {
        "repo_id": "GAIR/daVinci-MagiHuman",
        "probe_path": "1080p_sr/model-00006-of-00013.safetensors",
        "gate": "none",
        "purpose": "1080p SR checkpoint access",
    },
]

PROFILE_PROBES["complete"] = PROFILE_PROBES["required_suite"] + [
    {
        "repo_id": "GAIR/daVinci-MagiHuman",
        "probe_path": "distill/model-00012-of-00013.safetensors",
        "gate": "none",
        "purpose": "distill checkpoint access",
    },
]


def token_from_env(env=None):
    env = env if env is not None else os.environ
    for name in HUGGINGFACE_TOKEN_NAMES:
        token = env.get(name)
        if token:
            return token, name
    return None, None


def token_from_cache(home=None):
    home = Path(home) if home is not None else Path.home()
    token_path = home / ".cache" / "huggingface" / "token"
    if not token_path.is_file():
        return None, None
    token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        return None, None
    return token, "huggingface_token_cache"


def resolve_token(token=None, env=None, home=None):
    if token:
        return token, "argument"
    env_token, env_source = token_from_env(env=env)
    if env_token:
        return env_token, env_source
    return token_from_cache(home=home)


def hf_resolve_url(repo_id, probe_path, revision="main"):
    repo = urllib.parse.quote(repo_id, safe="/")
    path = urllib.parse.quote(probe_path, safe="/")
    rev = urllib.parse.quote(revision, safe="")
    return "https://huggingface.co/{}/resolve/{}/{}".format(repo, rev, path)


def build_head_request(url, token=None):
    request = urllib.request.Request(url, method="HEAD")
    request.add_header("User-Agent", "magihuman-mobile-lab-hf-access-audit")
    if token:
        request.add_header("Authorization", "Bearer {}".format(token))
    return request


def error_detail(error):
    reason = getattr(error, "reason", None) or getattr(error, "msg", "")
    if reason:
        return "HTTP {} {}".format(error.code, reason)
    return "HTTP {}".format(error.code)


def check_probe(probe, token=None, opener=None, timeout=20):
    repo_id = probe["repo_id"]
    probe_path = probe["probe_path"]
    gate = probe.get("gate", "none")
    url = hf_resolve_url(repo_id, probe_path)

    base = {
        "repo_id": repo_id,
        "probe_path": probe_path,
        "gate": gate,
        "purpose": probe.get("purpose", ""),
        "url": url,
    }

    if gate != "none" and not token:
        return {
            **base,
            "ok": False,
            "status": "missing_token",
            "http_status": None,
            "detail": "set HF_TOKEN, HUGGINGFACE_HUB_TOKEN, or run huggingface-cli login",
        }

    opener = opener or urllib.request.urlopen
    request = build_head_request(url, token=token)
    try:
        with opener(request, timeout=timeout) as response:
            return {
                **base,
                "ok": True,
                "status": "accessible",
                "http_status": response.getcode(),
                "detail": "HEAD request succeeded",
            }
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            status = "auth_required_or_forbidden"
            detail = "{}; accept model terms or use a token with access".format(error_detail(error))
        elif error.code == 404:
            status = "not_found_or_no_access"
            detail = "{}; check repository, filename, or token scope".format(error_detail(error))
        elif error.code == 429:
            status = "rate_limited"
            detail = "{}; retry later or use an authenticated token".format(error_detail(error))
        else:
            status = "http_error"
            detail = error_detail(error)
        return {
            **base,
            "ok": False,
            "status": status,
            "http_status": error.code,
            "detail": detail,
        }
    except (TimeoutError, socket.timeout, urllib.error.URLError, ssl.SSLError) as error:
        return {
            **base,
            "ok": False,
            "status": "network_error",
            "http_status": None,
            "detail": str(error),
        }


def build_access_audit(profile="p01", token=None, env=None, home=None, opener=None, timeout=20):
    if profile not in PROFILE_PROBES:
        raise ValueError("unknown Hugging Face access profile: {}".format(profile))
    resolved_token, token_source = resolve_token(token=token, env=env, home=home)
    checks = [
        check_probe(probe, token=resolved_token, opener=opener, timeout=timeout)
        for probe in PROFILE_PROBES[profile]
    ]
    failures = [check for check in checks if not check["ok"]]
    return {
        "status": "ready" if not failures else "not_ready",
        "profile": profile,
        "token_present": bool(resolved_token),
        "token_source": token_source or "missing",
        "checks": checks,
        "failures": failures,
    }


def markdown_access_audit(report):
    lines = [
        "# Hugging Face Access Audit",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Profile: `{}`".format(report["profile"]),
        "- Token present: {}".format("yes" if report["token_present"] else "no"),
        "- Token source: `{}`".format(report["token_source"]),
        "",
        "| Repo | Probe file | Gate | Status | HTTP | Detail |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for check in report["checks"]:
        http_status = check["http_status"] if check["http_status"] is not None else ""
        lines.append(
            "| {repo} | `{path}` | {gate} | `{status}` | {http} | {detail} |".format(
                repo=check["repo_id"],
                path=check["probe_path"],
                gate=check["gate"],
                status=check["status"],
                http=http_status,
                detail=check["detail"],
            )
        )
    return "\n".join(lines)


def write_output(text, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Check Hugging Face model repository access before checkpoint download")
    parser.add_argument("--profile", choices=sorted(PROFILE_PROBES), default="p01")
    parser.add_argument("--token", help="Optional token override. Prefer environment variables to avoid shell history.")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when any required HF probe fails.")
    args = parser.parse_args()

    report = build_access_audit(profile=args.profile, token=args.token, timeout=args.timeout)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_access_audit(report)
    if args.output:
        write_output(text, args.output)
    print(text)
    if args.strict and report["status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
