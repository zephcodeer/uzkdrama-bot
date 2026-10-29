import urllib.request
import re
from PIL import Image
import io

urls = [
    "https://m.media-amazon.com/images/M/MV5BMDk5ZTY1ZWMtYzY0MC00MmRkLTlmYjYtZTA4ZDYxNWNjZDVkXkEyXkFqcGc@._V1_QL75_UY562_CR1,0,380,562_.jpg",
    "https://m.media-amazon.com/images/M/MV5BMTg5Y2VjYzAtOGE4OC00MWU1LWI1YzktZWY1ZGEwMDVjODY1XkEyXkFqcGc@._V1_SX300.jpg",
    "https://m.media-amazon.com/images/M/MV5BMTc5MDE2ODcwNV5BMl5BanBnXkFtZTgwMzI2NzQ2NzM@._V1_QL75_UX380_CR0,0,380,562_.jpg"
]

for u in urls:
    # Original full resolution url:
    # replace ._V1_... with ._V1_.jpg or ._V1_FMjpg_UX1000_.jpg
    orig_url = re.sub(r'\._V1_.*\.jpg$', '._V1_.jpg', u)
    req = urllib.request.Request(orig_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        im = Image.open(io.BytesIO(data))
        print("Original URL:", orig_url, "-> Size:", im.size, "Bytes:", len(data))
    except Exception as e:
        print("Error for", orig_url, e)
