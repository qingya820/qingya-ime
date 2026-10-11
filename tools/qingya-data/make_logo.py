#!/usr/bin/env python3
# 把水墨青崖 logo（任意比例 JPG/PNG）补成正方形 1024 PNG，供 bundle.sh 生成 .icns。
# 用法：python3 make_logo.py 源图.jpg [目标 logo.png]
# 补边色取四角平均（宣纸底色），避免拉伸变形。需要 Pillow。
import sys
from pathlib import Path
from PIL import Image

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "Pictures/青崖logo.jpg"))
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else \
    Path(__file__).resolve().parents[2] / "assets/icon/logo.png"
SIZE = 1024

im = Image.open(SRC).convert("RGB")
w, h = im.size
scale = min(SIZE / w, SIZE / h)
nw, nh = round(w * scale), round(h * scale)
im = im.resize((nw, nh), Image.LANCZOS)

px = im.load()
corners = [px[2, 2], px[nw - 3, 2], px[2, nh - 3], px[nw - 3, nh - 3]]
bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))

canvas = Image.new("RGB", (SIZE, SIZE), bg)
canvas.paste(im, ((SIZE - nw) // 2, (SIZE - nh) // 2))
canvas.save(DST, "PNG")
print("saved", DST, canvas.size, "bg=", bg)
