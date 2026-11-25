"""Contact sheet: python3 tools/sheet.py out.png cols img1 img2 ..."""
import sys
from PIL import Image, ImageDraw
out, cols, ims = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
imgs = [Image.open(p).convert("RGB") for p in ims]
w, h = imgs[0].size
rows = (len(imgs) + cols - 1) // cols
sheet = Image.new("RGB", (w * cols, h * rows), (20, 20, 20))
for i, (p, im) in enumerate(zip(ims, imgs)):
    x, y = (i % cols) * w, (i // cols) * h
    sheet.paste(im, (x, y))
    d = ImageDraw.Draw(sheet)
    d.text((x + 4, y + 4), p.split("_")[-1].split(".")[0], fill=(255, 255, 0))
sheet.save(out)
