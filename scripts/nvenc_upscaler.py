import os
import sys
import subprocess
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def is_nvenc_available() -> bool:
    """NVIDIA RTX GPU va NVENC drayveri mavjudligini tekshirish."""
    try:
        res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=5)
        return "h264_nvenc" in res.stdout
    except Exception:
        return False


def upscale_to_1080p(input_path: Path, output_path: Path, use_nvenc: bool = True) -> Path:
    """
    Videoni 1920x1080 Full HD ga Lanczos filtri va NVENC apparat tezlatgichi bilan konvertatsiya qilish.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True, parents=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Kirish fayli topilmadi: {input_path}")

    t0 = time.time()
    print(f"\n🎬 1080p FULL HD UPSCALER ISHGA TUSHDI: {input_path.name}")

    nvenc = use_nvenc and is_nvenc_available()
    if nvenc:
        print("   ⚡️ NVIDIA GeForce RTX 3060 NVENC apparat tezlatgichi ishlatilmoqda!")
        # RTX 3060 p5 sifat profili, yuqori b-frame va lanczos filtri
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", "scale=1920:1080:flags=lanczos,unsharp=5:5:0.6:3:3:0.3",
            "-c:v", "h264_nvenc",
            "-preset", "p5",
            "-tune", "hq",
            "-rc", "vbr",
            "-b:v", "2800k",
            "-maxrate", "4500k",
            "-bufsize", "6000k",
            "-c:a", "copy",
            str(output_path)
        ]
    else:
        print("   ⚙️ CPU x264 ishlatilmoqda (NVENC topilmadi)...")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "21",
            "-c:a", "copy",
            str(output_path)
        ]

    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg xatoligi: {res.stderr[-400:]}")

    elapsed = time.time() - t0
    orig_mb = os.path.getsize(input_path) / (1024 * 1024)
    out_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   ✅ 1080p FULL HD TAYYOR! ({orig_mb:.1f} MB ➡️ {out_mb:.1f} MB) | Vaqt: {elapsed:.1f}s")

    return output_path


if __name__ == "__main__":
    print("NVENC mavjudmi:", is_nvenc_available())
