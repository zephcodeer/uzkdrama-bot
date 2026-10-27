import urllib.request
import ssl
import time
import concurrent.futures
import os
import math

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://v.mover.uz/uGmXQUji_h.mp4"
total_test = 50 * 1024 * 1024 # 50 MB
num_threads = 8
chunk_size = math.ceil(total_test / num_threads)

def dl_part(idx, start, end):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://mover.uz/',
        'Range': f'bytes={start}-{end}'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return len(r.read())

t0 = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as ex:
    futs = []
    for i in range(num_threads):
        s = i * chunk_size
        e = min(s + chunk_size - 1, total_test - 1)
        futs.append(ex.submit(dl_part, i, s, e))
    tot = sum(f.result() for f in futs)

dt = time.time() - t0
spd = (tot / (1024*1024)) / dt
print(f"Downloaded {tot / (1024*1024):.1f} MB with {num_threads} threads in {dt:.2f}s -> Speed: {spd:.2f} MB/s")
