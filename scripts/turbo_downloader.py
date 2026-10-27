import os
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

def parallel_download(url: str, dest_path: Path, referer: str = "", num_workers: int = 16):
    """
    IDM-darajasidagi ko'p tarmoqli (multi-segmented Range) parallel yuklovchi.
    Har bir qism alohida TCP oqimda yuklanadi, server cheklovini aylanib o'tadi.
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(exist_ok=True, parents=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if referer:
        headers["Referer"] = referer

    # 1. Umumiy hajmni aniqlash
    req = urllib.request.Request(url, headers={**headers, "Range": "bytes=0-0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        cr = r.headers.get("Content-Range")
        if cr:
            total_size = int(cr.split("/")[-1])
        else:
            total_size = int(r.headers.get("Content-Length", 0))

    if total_size <= 0:
        raise ValueError(f"Hajmni aniqlab bo'lmadi: {url}")

    print(f"\n🚀 TURBO MULTI-SEGMENT YUKLASH: {total_size / (1024*1024):.1f} MB ({num_workers} ta oqimda)")

    # 2. Fayl joyini bo'shatish (pre-allocate)
    with open(dest_path, "wb") as f:
        f.seek(total_size - 1)
        f.write(b"\0")

    # 3. Bo'laklarni hisoblash
    chunk_size = total_size // num_workers
    ranges = []
    for i in range(num_workers):
        start = i * chunk_size
        end = total_size - 1 if i == num_workers - 1 else (start + chunk_size - 1)
        ranges.append((i, start, end))

    downloaded = 0
    lock = None
    import threading
    progress_lock = threading.Lock()
    t0 = time.time()

    def download_range(worker_id, start, end):
        nonlocal downloaded
        w_headers = dict(headers)
        w_headers["Range"] = f"bytes={start}-{end}"
        req = urllib.request.Request(url, headers=w_headers)
        
        # Retry logic
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=25) as resp:
                    cur = start
                    while True:
                        buf = resp.read(64 * 1024)
                        if not buf:
                            break
                        with open(dest_path, "r+b") as out_f:
                            out_f.seek(cur)
                            out_f.write(buf)
                        cur += len(buf)
                        with progress_lock:
                            downloaded += len(buf)
                            pct = downloaded / total_size * 100
                            mb = downloaded / (1024 * 1024)
                            tot_mb = total_size / (1024 * 1024)
                            elapsed = time.time() - t0
                            speed = (downloaded / (1024 * 1024)) / max(elapsed, 0.1)
                            sys.stdout.write(f"\r   ⚡️ [SPEED: {speed:4.2f} MB/s | {pct:5.1f}%] {mb:5.1f} MB / {tot_mb:5.1f} MB (Oqimlar: {num_workers})")
                            sys.stdout.flush()
                return True
            except Exception as e:
                time.sleep(1 + attempt)
                if attempt == 3:
                    raise e
        return False

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(download_range, wid, s, e) for wid, s, e in ranges]
        for f in as_completed(futures):
            f.result()

    elapsed = time.time() - t0
    avg_speed = (total_size / (1024 * 1024)) / max(elapsed, 0.1)
    print(f"\n   ✅ TURBO YUKLASH YAKUNLANDI: {total_size / (1024*1024):.1f} MB | Vaqt: {elapsed:.1f}s | O'rtacha tezlik: {avg_speed:.2f} MB/s")
    return dest_path


if __name__ == "__main__":
    test_url = "https://sherlar.net/serial/doktorx/4.mp4"
    out = Path(r"E:\Agent\Drama Bot\temp_downloads\test_ep4.mp4")
    parallel_download(test_url, out, referer="https://uzmovi.me/", num_workers=16)
