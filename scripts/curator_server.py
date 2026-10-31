import http.server
import socketserver
import os
import sys
import json
import sqlite3
import urllib.request
import webbrowser
from PIL import Image
import io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PORT = 8765
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "doramas.db")
POSTERS_DIR = os.path.join(BASE_DIR, "posters")

def slugify(text):
    clean = ""
    for c in text.lower().strip():
        if c.isalnum() or c in (" ", "-", "_"):
            clean += c
    return "-".join(clean.split())[:40] or "poster"

class CuratorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/save":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(post_data)
                selections = payload.get("selections", {})
                
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                updated = 0

                for code_str, sel in selections.items():
                    code = int(code_str)
                    choice = sel.get("choice")
                    url = sel.get("url")
                    
                    if choice in ("B", "CUSTOM") and url and url.startswith("http"):
                        try:
                            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                            with urllib.request.urlopen(req, timeout=12) as resp:
                                img_data = resp.read()
                            
                            img = Image.open(io.BytesIO(img_data))
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            
                            c.execute("SELECT title FROM doramas WHERE code = ?", (code,))
                            r = c.fetchone()
                            title = r[0] if r else f"dorama_{code}"
                            slug = slugify(title)
                            fname = f"{code}_{slug}.jpg"
                            local_dest = os.path.join(POSTERS_DIR, fname)
                            img.save(local_dest, "JPEG", quality=92)
                            
                            db_rel = f"posters/{fname}".replace("\\", "/")
                            c.execute("UPDATE doramas SET poster_url = ? WHERE code = ?", (db_rel, code))
                            conn.commit()
                            updated += 1
                        except Exception as e:
                            print(f"[XATO] #{code} yuklanmadi: {e}")

                conn.close()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "updated": updated}).encode("utf-8"))
            except Exception as ex:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(ex)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    os.chdir(BASE_DIR)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CuratorHandler) as httpd:
        print(f"==================================================")
        print(f"POSTER CURATOR STUDIO ISHLAMOQDA!")
        print(f"URL: http://localhost:{PORT}/poster_curator.html")
        print(f"==================================================")
        sys.stdout.flush()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer to'xtatildi.")

if __name__ == "__main__":
    run_server()
