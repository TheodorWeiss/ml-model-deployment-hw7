"""
Генератор нагрузки для /predict.
Шлёт N запросов со случайными iris-сэмплами.
"""
import json
import random
import sys
import time
import urllib.request

URL = "http://localhost:8090/predict"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 500
DELAY = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1  # 10 req/s по умолчанию

SAMPLES = [
    [5.1, 3.5, 1.4, 0.2],  # setosa
    [4.9, 3.0, 1.4, 0.2],  # setosa
    [7.0, 3.2, 4.7, 1.4],  # versicolor
    [6.4, 3.2, 4.5, 1.5],  # versicolor
    [6.3, 3.3, 6.0, 2.5],  # virginica
    [5.8, 2.7, 5.1, 1.9],  # virginica
]

start = time.time()
for i in range(N):
    x = random.choice(SAMPLES)
    data = json.dumps({"x": x}).encode()
    req = urllib.request.Request(
        URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            r.read()
    except Exception as e:
        print(f"[{i+1}/{N}] error: {e}")
    if (i + 1) % 50 == 0:
        elapsed = time.time() - start
        rate = (i + 1) / elapsed
        print(f"[{i+1}/{N}] elapsed {elapsed:.1f}s, rate {rate:.1f} req/s")
    if DELAY > 0:
        time.sleep(DELAY)

print(f"Done. Sent {N} predictions in {time.time() - start:.1f}s")