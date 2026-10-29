from PIL import Image
import os

p = r"E:\Agent\Drama Bot\posters\men-bugundan-insonman-65.jpg"
im = Image.open(p)
w, h = im.size
print("Original size:", w, h)

# Crop to 2:3 vertical (w = h * 0.7)
target_w = int(h * 0.68)
left = (w - target_w) // 2
right = left + target_w
crop_im = im.crop((left, 0, right, h))
print("Cropped size:", crop_im.size)
crop_im.save(p, "JPEG", quality=95)
print("Saved cropped portrait poster successfully!")
