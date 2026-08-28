# -*- coding: utf-8 -*-
"""Generate a Windows .ico for CodePlot from an emoji."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
EMOJI = "📊"  # bar chart, best fits a plotting tool
SIZE = 256

font = None
for font_path in [
    r"C:\Windows\Fonts\seguiemj.ttf",   # Segoe UI Emoji
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\msyh.ttc",
]:
    try:
        font = ImageFont.truetype(font_path, int(SIZE * 0.7))
        break
    except Exception:
        continue
if font is None:
    font = ImageFont.load_default()

img = Image.new("RGBA", (SIZE, SIZE), (240, 245, 255, 0))
draw = ImageDraw.Draw(img)
bbox = draw.textbbox((0, 0), EMOJI, font=font)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
x = (SIZE - w) / 2 - bbox[0]
y = (SIZE - h) / 2 - bbox[1]
draw.text((x, y), EMOJI, font=font, embedded_color=True)

# Save as single 256x256 ICO; Windows scales it for smaller sizes.
img.save(OUT, format="ICO", sizes=[(SIZE, SIZE)])
print("Saved icon:", OUT)
