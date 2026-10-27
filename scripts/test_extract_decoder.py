import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://doramalar.net/assets/dorama/pleyer/vendor.js", headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    js = resp.read().decode('utf-8', errors='ignore')

idx = js.find('#2")!==0')
if idx != -1:
    print(js[max(0, idx - 500):idx + 1000])
else:
    print("Not found")
