import os
from PIL import Image

src = r"C:\Users\MuhammadSodiq\Downloads\CleanMedia\salomtv.uz\Images\image.jpg"
print("Exists:", os.path.exists(src))
if os.path.exists(src):
    print("Size bytes:", os.path.getsize(src))
    with Image.open(src) as img:
        print("Format:", img.format, "Size:", img.size, "Mode:", img.mode)
