import argparse
import json
from pathlib import Path

from backend.experiment_suite import REQUIRED_CASE_IDS


SCORE_FIELDS = [
    "audio_video_sync_score",
    "face_quality_score",
    "motion_naturalness_score",
    "speech_intelligibility_score",
    "artifact_free_score",
]

MIN_PASSING_SCORE = 3


def build_review_template(case_ids=None):
    case_ids = case_ids or REQUIRED_CASE_IDS
    return {
        "review_version": "1",
        "reviewer": "",
        "reviewed_at": "",
        "scale": "1=unusable, 2=poor, 3=demo acceptable, 4=good, 5=excellent",
        "minimum_passing_score": MIN_PASSING_SCORE,
        "case_reviews": [
            {
                "case_id": case_id,
                "sample_path": "outputs/experiment-results/{}.mp4".format(case_id),
                "playable_on_phone": None,
                "audio_video_sync_score": None,
                "face_quality_score": None,
                "motion_naturalness_score": None,
                "speech_intelligibility_score": None,
                "artifact_free_score": None,
                "notes": "",
            }
            for case_id in case_ids
        ],
    }


def load_review(path):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def score_status(value, min_score=MIN_PASSING_SCORE):
    if value is None:
        return "missing"
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "invalid"
    if value < 1 or value > 5:
        return "invalid"
    if value < min_score:
        return "failed"
    return "passed"


def evaluate_case_review(review, min_score=MIN_PASSING_SCORE):
    missing = []
    invalid = []
    failures = []

    phone_value = review.get("playable_on_phone")
    if phone_value is None:
        missing.append("playable_on_phone")
    elif not isinstance(phone_value, bool):
        invalid.append("playable_on_phone")
    elif not phone_value:
        failures.append("playable_on_phone")

    score_results = {}
    for field in SCORE_FIELDS:
        status = score_status(review.get(field), min_score=min_score)
        score_results[field] = status
        if status == "missing":
            missing.append(field)
        elif status == "invalid":
            invalid.append(field)
        elif status == "failed":
            failures.append(field)

    if invalid:
        status = "invalid"
    elif missing:
        status = "incomplete"
    elif failures:
        status = "failed"
    else:
        status = "passed"

    return {
        "case_id": review.get("case_id"),
        "sample_path": review.get("sample_path"),
        "status": status,
        "missing_fields": missing,
        "invalid_fields": invalid,
        "failed_fields": failures,
        "score_results": score_results,
        "notes": review.get("notes", ""),
    }


def build_quality_report(review_path=None, case_ids=None):
    case_ids = case_ids or REQUIRED_CASE_IDS
    if not review_path:
        return {
            "status": "missing_quality_review",
            "review_path": None,
            "case_ids": list(case_ids),
            "rows": [],
            "summary": "No quality review file was provided.",
        }

    path = Path(review_path)
    if not path.exists():
        return {
            "status": "missing_quality_review",
            "review_path": str(path),
            "case_ids": list(case_ids),
            "rows": [],
            "summary": "Quality review file is missing: {}".format(path),
        }

    review = load_review(path)
    min_score = review.get("minimum_passing_score", MIN_PASSING_SCORE)
    reviews_by_id = {item.get("case_id"): item for item in review.get("case_reviews", [])}
    rows = []
    for case_id in case_ids:
        case_review = reviews_by_id.get(case_id)
        if not case_review:
            rows.append(
                {
                    "case_id": case_id,
                    "sample_path": None,
                    "status": "missing_review",
                    "missing_fields": ["case_review"],
                    "invalid_fields": [],
                    "failed_fields": [],
                    "score_results": {},
                    "notes": "",
                }
            )
        else:
            rows.append(evaluate_case_review(case_review, min_score=min_score))

    row_statuses = {row["status"] for row in rows}
    if row_statuses == {"passed"}:
        status = "quality_review_passed"
        summary = "All required samples passed quality review."
    elif "failed" in row_statuses:
        status = "quality_review_failed"
        summary = "One or more required samples failed quality review."
    else:
        status = "incomplete_quality_review"
        summary = "Quality review is missing or incomplete for required samples."

    return {
        "status": status,
        "review_path": str(path),
        "case_ids": list(case_ids),
        "rows": rows,
        "summary": summary,
    }


def markdown_quality_report(report):
    lines = [
        "# Quality Review",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Summary: {}".format(report["summary"]),
        "- Review file: {}".format(report["review_path"] or "-"),
        "",
        "| Case | Status | Sample | Missing | Invalid | Failed |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    if not report["rows"]:
        lines.append("| - | `{}` | - | - | - | - |".format(report["status"]))
        return "\n".join(lines)

    for row in report["rows"]:
        lines.append(
            "| {case} | `{status}` | {sample} | {missing} | {invalid} | {failed} |".format(
                case=row["case_id"],
                status=row["status"],
                sample=row.get("sample_path") or "-",
                missing=", ".join(row["missing_fields"]) if row["missing_fields"] else "-",
                invalid=", ".join(row["invalid_fields"]) if row["invalid_fields"] else "-",
                failed=", ".join(row["failed_fields"]) if row["failed_fields"] else "-",
            )
        )
    return "\n".join(lines)


def write_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create or summarize MagiHuman sample quality reviews")
    parser.add_argument("--review")
    parser.add_argument("--create-template", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    if args.create_template:
        body = build_review_template()
        text = json.dumps(body, ensure_ascii=False, indent=2)
        if args.output:
            write_json(body, args.output)
        print(text)
        return

    report = build_quality_report(args.review)
    if args.format == "json":
        text = json.dumps(report, ensure_ascii=False, indent=2)
    else:
        text = markdown_quality_report(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
