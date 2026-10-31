from PIL import Image

src = r"C:\Users\MuhammadSodiq\Downloads\CleanMedia\salomtv.uz\Images\image.jpg"
img = Image.open(src)
W, H = img.size

# Actor is centered around x = 1480
# 2:3 aspect ratio -> target width for H=1080 is 1080 * 2 / 3 = 720
crop_w = int(H * 2 / 3) # 720
left = 1120
right = left + crop_w
top = 0
bottom = H

cropped = img.crop((left, top, right, bottom))
fitted = cropped.resize((500, 750), Image.Resampling.LANCZOS)
fitted.save(r"E:\Agent\Drama Bot\posters\code_480.jpg", "JPEG", quality=95)
print(f"Saved cropped poster to code_480.jpg from box ({left}, {top}, {right}, {bottom})")
