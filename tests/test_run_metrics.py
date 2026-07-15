import json
import tempfile
import unittest
from pathlib import Path

from backend.run_metrics import (
    parse_elapsed_seconds,
    parse_ffprobe_json_text,
    parse_nvidia_smi_csv_text,
    parse_time_v_log,
    parse_time_v_text,
)


class RunMetricsTest(unittest.TestCase):
    def test_parse_nvidia_smi_csv_text(self):
        text = (
            "timestamp, name, memory.used [MiB], memory.total [MiB], utilization.gpu [%]\n"
            "2026/07/15 12:00:00.000, NVIDIA H100, 1024 MiB, 81559 MiB, 90 %\n"
            "2026/07/15 12:00:01.000, NVIDIA H100, 2048 MiB, 81559 MiB, 80 %\n"
        )
        metrics = parse_nvidia_smi_csv_text(text)
        self.assertEqual(metrics["samples"], 2)
        self.assertEqual(metrics["gpu_names"], ["NVIDIA H100"])
        self.assertEqual(metrics["peak_memory_used_mib"], 2048)
        self.assertEqual(metrics["memory_total_mib"], 81559)
        self.assertEqual(metrics["average_gpu_utilization_percent"], 85)

    def test_parse_elapsed_seconds(self):
        self.assertEqual(parse_elapsed_seconds("1:02.50"), 62.5)
        self.assertEqual(parse_elapsed_seconds("2:01:02.50"), 7262.5)
        self.assertEqual(parse_elapsed_seconds("12.5"), 12.5)

    def test_parse_time_v_text(self):
        text = (
            "User time (seconds): 10.20\n"
            "System time (seconds): 1.30\n"
            "Elapsed (wall clock) time (h:mm:ss or m:ss): 1:02.50\n"
            "Maximum resident set size (kbytes): 123456\n"
            "Exit status: 0\n"
        )
        metrics = parse_time_v_text(text)
        self.assertEqual(metrics["wall_time_seconds"], 62.5)
        self.assertEqual(metrics["max_resident_set_kbytes"], 123456)
        self.assertEqual(metrics["user_seconds"], 10.2)
        self.assertEqual(metrics["system_seconds"], 1.3)
        self.assertEqual(metrics["exit_status"], 0)

    def test_parse_time_v_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.log"
            path.write_text("Elapsed (wall clock) time (h:mm:ss or m:ss): 0:03.00\n", encoding="utf-8")
            self.assertEqual(parse_time_v_log(path)["wall_time_seconds"], 3.0)

    def test_parse_ffprobe_json_text(self):
        payload = {
            "streams": [
                {"codec_type": "video", "width": 448, "height": 256, "duration": "5.000000"},
                {"codec_type": "audio", "duration": "5.000000"},
            ],
            "format": {"duration": "5.000000", "size": "12345", "format_name": "mov,mp4,m4a,3gp,3g2,mj2"},
        }
        metrics = parse_ffprobe_json_text(json.dumps(payload))
        self.assertEqual(metrics["duration_seconds"], 5.0)
        self.assertTrue(metrics["has_video"])
        self.assertTrue(metrics["has_audio"])
        self.assertEqual(metrics["width"], 448)
        self.assertEqual(metrics["height"], 256)
        self.assertEqual(metrics["size_bytes"], 12345)


if __name__ == "__main__":
    unittest.main()

