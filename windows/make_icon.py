# Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin. Copyright (c) 2026 The_Mead_Maker & Odin. MIT License.
"""Draws the Theme Studio icon: the Kenaz rune (torch, creativity) in gold on a dark rounded square with a gold rim,
matching Valhalla's Othala icon. Writes studio.png (1024 px) and studio.ico (16-256 px). Needs Pillow (build time only)."""
import math, os
from PIL import Image, ImageDraw

GOLD, NIGHT = (212, 166, 74, 255), (11, 15, 23, 255)
S, K = 1024, 4   # draw 4x bigger, then shrink for smooth edges
here = os.path.dirname(os.path.abspath(__file__))

def stroke(d, a, b, w):
    (x1, y1), (x2, y2) = a, b
    l = math.hypot(x2 - x1, y2 - y1); nx, ny = -(y2 - y1) / l * w / 2, (x2 - x1) / l * w / 2
    d.polygon([(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)], fill=GOLD)

def draw():
    big = Image.new("RGBA", (S * K, S * K), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    m, rim, r = 40 * K, 36 * K, 200 * K
    d.rounded_rectangle((m, m, S * K - m - 1, S * K - m - 1), radius=r, fill=GOLD)
    d.rounded_rectangle((m + rim, m + rim, S * K - m - rim - 1, S * K - m - rim - 1), radius=r - rim, fill=NIGHT)
    w = 70 * K                                    # same stroke weight as Valhalla's rune
    top, tip, bot = (680 * K, 196 * K), (356 * K, 512 * K), (680 * K, 828 * K)   # Kenaz: an open angle, point to the left
    stroke(d, top, tip, w); stroke(d, tip, bot, w)
    d.ellipse((tip[0] - w / 2, tip[1] - w / 2, tip[0] + w / 2, tip[1] + w / 2), fill=GOLD)   # rounded point, like Valhalla's
    return big.resize((S, S), Image.LANCZOS)

if __name__ == "__main__":
    im = draw()
    im.save(os.path.join(here, "studio.png"))
    im.save(os.path.join(here, "studio.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote studio.png and studio.ico")
