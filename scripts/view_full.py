from PIL import Image

src = r"C:\Users\MuhammadSodiq\Downloads\CleanMedia\salomtv.uz\Images\image.jpg"
img = Image.open(src)
# resize to 960x540 for inspection
resized = img.resize((960, 540), Image.Resampling.LANCZOS)
resized.save(r"E:\Agent\Drama Bot\posters\code_480_full_preview.jpg", "JPEG", quality=85)
