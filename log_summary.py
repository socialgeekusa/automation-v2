import os
import re
from datetime import datetime
from collections import defaultdict

LOG_DIR = os.path.join("Logs")
WARMUP_LOG = os.path.join(LOG_DIR, "warmup_log.txt")
POST_LOG = os.path.join(LOG_DIR, "post_log.txt")

TIME_FORMAT = "%a %b %d %H:%M:%S %Y"

def parse_time(timestr):
    try:
        return datetime.strptime(timestr, TIME_FORMAT)
    except Exception:
        return None

def accumulate_logs():
    counts = defaultdict(lambda: {"likes":0, "follows":0, "comments":0, "shares":0, "posts":0})
    start_time = None
    end_time = None

    action_map = {
        "LIKE": "likes",
        "FOLLOW": "follows",
        "COMMENT": "comments",
        "SHARE": "shares",
    }

    if os.path.exists(WARMUP_LOG):
        with open(WARMUP_LOG, "r") as f:
            for line in f:
                m = re.match(r"(?:\[(?P<prefix>[^\]]+)\]\s+)?(?P<ts>[A-Z][a-z]{2} [A-Z][a-z]{2}\s+\d+ \d+:\d+:\d+ \d{4}): Warmup (\w+) .* on (\S+)", line)
                if not m:
                    continue
                ts = parse_time(m.group('ts'))
                action = m.group(3).upper()
                device = m.group('prefix') or m.group(4)
                metric = action_map.get(action)
                if metric:
                    counts[device][metric] += 1
                if ts:
                    if start_time is None or ts < start_time:
                        start_time = ts
                    if end_time is None or ts > end_time:
                        end_time = ts

    if os.path.exists(POST_LOG):
        with open(POST_LOG, "r") as f:
            for line in f:
                m = re.match(r"(?:\[(?P<prefix>[^\]]+)\]\s+)?(?P<ts>[A-Z][a-z]{2} [A-Z][a-z]{2}\s+\d+ \d+:\d+:\d+ \d{4}): SUCCESS post \w+ \S+ on (\S+)", line)
                if not m:
                    continue
                ts = parse_time(m.group('ts'))
                device = m.group('prefix') or m.group(3)
                counts[device]["posts"] += 1
                if ts:
                    if start_time is None or ts < start_time:
                        start_time = ts
                    if end_time is None or ts > end_time:
                        end_time = ts

    return counts, start_time, end_time

def format_duration(start, end):
    if not start or not end:
        return "N/A"
    delta = end - start
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if hours or minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)

def print_summary():
    counts, start, end = accumulate_logs()
    if not counts:
        print("No logs found.")
        return

    header = f"{'Device':<15}{'Likes':>6}{'Follows':>8}{'Comments':>10}{'Shares':>8}{'Posts':>7}"
    print(header)
    print("-" * len(header))
    for device, data in counts.items():
        print(f"{device:<15}{data['likes']:>6}{data['follows']:>8}{data['comments']:>10}{data['shares']:>8}{data['posts']:>7}")

    duration = format_duration(start, end)
    print(f"\nSession duration: {duration}")

if __name__ == "__main__":
    print_summary()
