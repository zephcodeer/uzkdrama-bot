import urllib.request
import ssl
import subprocess
import speech_recognition as sr
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://v.mover.uz/uGmXQUji_h.mp4"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://mover.uz/',
    'Range': 'bytes=0-15728640' # 15 MB
})

print("Downloading 15MB sample from mover.uz...")
sample_file = "E:/Agent/Drama Bot/mover_sample.mp4"
with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
    data = r.read()
open(sample_file, "wb").write(data)
print(f"Downloaded {len(data)} bytes.")

# Extract audio segments
r_rec = sr.Recognizer()
for start in [0, 20, 45, 60]:
    wav_p = f"E:/Agent/Drama Bot/mover_audio_{start}.wav"
    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-t", "25",
        "-i", sample_file, "-vn", "-acodec", "pcm_s16le", wav_p
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(wav_p):
        try:
            with sr.AudioFile(wav_p) as src:
                aud = r_rec.record(src)
            text = r_rec.recognize_google(aud, language='uz-UZ')
            print(f"[{start}s - {start+25}s]: {text}")
        except Exception as e:
            print(f"[{start}s - {start+25}s]: [No speech or error: {e}]")
        try:
            os.remove(wav_p)
        except Exception:
            pass

try:
    os.remove(sample_file)
except Exception:
    pass
