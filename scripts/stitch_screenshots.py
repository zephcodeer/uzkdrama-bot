import os
from PIL import Image

screenshots_dir = r"C:\Users\MuhammadSodiq\Pictures\Screenshots"
temp_dir = r"E:\Agent\Drama Bot\temp_screenshots"
os.makedirs(temp_dir, exist_ok=True)

files = sorted([f for f in os.listdir(screenshots_dir) if f.startswith("Screenshot 2026-10-26 235")])
print(f"Total files: {len(files)}")

# Group into batches of 6
batch_size = 6
batches = [files[i:i + batch_size] for i in range(0, len(files), batch_size)]

for b_idx, batch in enumerate(batches, 1):
    imgs = [Image.open(os.path.join(screenshots_dir, f)) for f in batch]
    max_w = max(im.width for im in imgs)
    total_h = sum(im.height for im in imgs)
    
    combined = Image.new("RGBA", (max_w, total_h))
    y = 0
    for im in imgs:
        combined.paste(im, (0, y))
        y += im.height
        
    out_path = os.path.join(temp_dir, f"batch_{b_idx}.png")
    combined.save(out_path)
    print(f"Saved {out_path}: {combined.size}")
