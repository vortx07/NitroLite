import os
from PIL import Image, ImageDraw

assets_dir = r"C:\Users\arifs\.gemini\antigravity\scratch\NitroLite\assets"
os.makedirs(assets_dir, exist_ok=True)
ico_path = os.path.join(assets_dir, "icon.ico")

sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
images = []

for s in sizes:
    w, h = s
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    pad = max(1, w // 16)
    draw.ellipse((pad, pad, w - pad, h - pad), fill=(24, 28, 36, 255), outline=(255, 51, 75, 255), width=max(1, w // 18))
    
    p = [
        (int(w * 0.30), int(h * 0.74)),
        (int(w * 0.30), int(h * 0.26)),
        (int(w * 0.42), int(h * 0.26)),
        (int(w * 0.60), int(h * 0.58)),
        (int(w * 0.60), int(h * 0.26)),
        (int(w * 0.70), int(h * 0.26)),
        (int(w * 0.70), int(h * 0.74)),
        (int(w * 0.58), int(h * 0.74)),
        (int(w * 0.40), int(h * 0.42)),
        (int(w * 0.40), int(h * 0.74)),
    ]
    draw.polygon(p, fill=(255, 51, 75, 255))
    images.append(im)

images[-1].save(ico_path, format="ICO", sizes=[(im.width, im.height) for im in images])
print("Generated icon at:", ico_path)
