import os
from PIL import Image, ImageOps

src = r"C:\Users\MuhammadSodiq\Downloads\CleanMedia\salomtv.uz\Images\image.jpg"
img = Image.open(src)
print("Original size:", img.size)

# Fit directly to 500x750
fitted = ImageOps.fit(img, (500, 750), method=Image.Resampling.LANCZOS)
fitted.save(r"E:\Agent\Drama Bot\posters\code_480_preview.jpg", "JPEG", quality=92)
print("Saved preview to code_480_preview.jpg")
