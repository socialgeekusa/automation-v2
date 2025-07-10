import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import log_summary


def test_accumulate_logs_by_account(tmp_path):
    log_dir = tmp_path / "Logs"
    log_dir.mkdir()
    log_file = log_dir / "automation_log.txt"
    lines = [
        "[dev1] Mon Jan 01 00:00:00 2024: LIKE TikTok user1 on dev1\n",
        "[dev1] Mon Jan 01 00:01:00 2024: Warmup FOLLOW TikTok user1 on dev1\n",
        "[dev2] Mon Jan 01 00:02:00 2024: COMMENT Instagram user2 on dev2\n",
        "[dev1] Mon Jan 01 00:03:00 2024: SUCCESS post TikTok user1 on dev1\n",
    ]
    log_file.write_text("".join(lines))
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        counts, start, end = log_summary.accumulate_logs_by_account()
    finally:
        os.chdir(cwd)

    assert counts["user1"]["likes"] == 1
    assert counts["user1"]["follows"] == 1
    assert counts["user1"]["posts"] == 1
    assert counts["user2"]["comments"] == 1
