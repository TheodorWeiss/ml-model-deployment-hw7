"""
Проверка распределения трафика между версиями сервиса.
Шлёт N запросов на /health и считает, сколько ответов от какой версии пришло.
"""
import json
import sys
import urllib.request
from collections import Counter

URL = "http://localhost:8090/health"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 50

versions = Counter()
errors = 0

for i in range(N):
    try:
        with urllib.request.urlopen(URL, timeout=5) as r:
            data = json.loads(r.read())
        version = data.get("version", "unknown")
        versions[version] += 1
    except Exception as e:
        errors += 1
        print(f"[{i+1:3d}/{N}] ERROR: {e}")

print(f"\n=== Распределение трафика ({N} запросов) ===")
total = sum(versions.values())
for v, count in versions.most_common():
    pct = count / total * 100 if total else 0
    bar = "█" * int(pct / 2)
    print(f"  {v}: {count:3d} ({pct:5.1f}%) {bar}")
if errors:
    print(f"  ERRORS: {errors}")