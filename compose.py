#!/usr/bin/env python3
"""Compose the news-image-20261117 entry: a 1024x1024 newspaper front page.

Layout (all px, canvas 1024x1024, white background):
  masthead black band ......... 104 (y 0..104)
  photo grid, 2x2 ............. y 104..968 (rows of 428, 8px gutter between rows;
                                8px side margins, 8px column gutter;
                                grid sits flush against masthead/footer so the
                                specified photo 500x356 and caption 72px sizes
                                fit exactly: 104 + 428 + 8 + 428 + 56 = 1024)
  footer ticker black band .... 56  (y 968..1024)
Each cell: photo 500x356 (centre-cropped source) + caption bar 72px below it.

Output is JPEG bytes written to a file named entry.png (the competition
accepts JPEG bytes under that name), at most 1,048,576 bytes.
"""

import io
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PANELS_DIR = os.path.join(HERE, "panels")
OUT_PATH = os.path.join(HERE, "entry.png")

W, H = 1024, 1024
MASTHEAD_H = 104
FOOTER_H = 56
MARGIN = 8
CELL_W = 500
PHOTO_H = 356
CAPTION_H = 72
ROW_H = PHOTO_H + CAPTION_H  # 428
GUTTER = 8

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GOLD = (232, 179, 60)   # #E8B33C
RED = (192, 57, 43)     # #C0392B

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

PANELS = [
    {
        "file": "media-generation-panel-crimea-bridge-0-666e66e5-1366-452d-baea-9108d5e479d8.png",
        "kicker": "UKRAINE · WAR",
        "headline": "Ukraine strikes Crimea bridge; Russia hits Kyiv bridges",
    },
    {
        "file": "media-generation-panel-hormuz-tanker-0-6baac136-3b2d-444e-8b14-89558850db6e.png",
        "kicker": "MIDDLE EAST · GULF",
        "headline": "Iran drones target U.S. base in Bahrain; tankers mined off Hormuz",
    },
    {
        "file": "media-generation-panel-shenzhen-summit-0-2bba2baf-bb29-42a7-a370-de6095d60c1e.png",
        "kicker": "DIPLOMACY · ASIA",
        "headline": "Xi, Trump and Putin to meet Thursday in Shenzhen",
    },
    {
        "file": "media-generation-panel-vulcan-rocket-0-08e1f691-99d6-438e-9d13-e51048e2b43c.png",
        "kicker": "SPACE · BUSINESS",
        "headline": "Vulcan rocket fails; 40 Amazon satellites lost",
    },
]

TICKER = "ALSO: CYBERATTACK HITS BBC, CNN AND 178 SITES  \u2022  U.S. LOSES MEASLES-FREE STATUS AFTER 30 YEARS"


def font(path, size):
    return ImageFont.truetype(path, size)


def centre_crop_resize(img, w, h):
    """Centre-crop to the target aspect ratio, then resize to (w, h)."""
    sw, sh = img.size
    target = w / h
    src = sw / sh
    if src > target:  # too wide: crop sides
        nw = int(sh * target)
        x0 = (sw - nw) // 2
        img = img.crop((x0, 0, x0 + nw, sh))
    else:  # too tall: crop top/bottom
        nh = int(sw / target)
        y0 = (sh - nh) // 2
        img = img.crop((0, y0, sw, y0 + nh))
    return img.resize((w, h), Image.LANCZOS)


def wrap_text(draw, text, fnt, max_width, max_lines=2):
    """Greedy word wrap; returns a list of at most max_lines lines."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def fit_font(draw, text, path, start_size, max_width, min_size=14):
    """Largest font size (<= start_size) at which text fits max_width."""
    size = start_size
    while size > min_size:
        fnt = font(path, size)
        if draw.textlength(text, font=fnt) <= max_width:
            return fnt
        size -= 1
    return font(path, min_size)


def draw_centred(draw, y, text, fnt, fill, letter_spacing=0):
    """Draw text centred horizontally at y; optional extra px between chars."""
    if letter_spacing <= 0:
        w = draw.textlength(text, font=fnt)
        draw.text(((W - w) / 2, y), text, font=fnt, fill=fill)
        return
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + letter_spacing * (len(text) - 1)
    x = (W - total) / 2
    for ch, cw in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += cw + letter_spacing


def compose():
    canvas = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(canvas)

    # --- masthead: black band, date line + gold strapline ---
    draw.rectangle([0, 0, W, MASTHEAD_H], fill=BLACK)
    date_font = fit_font(draw, "TUESDAY, 17 NOVEMBER 2026", BOLD, 52, W - 40)
    draw_centred(draw, 14, "TUESDAY, 17 NOVEMBER 2026", date_font, WHITE)
    strap_font = font(BOLD, 26)
    draw_centred(draw, 68, "THE WORLD IN ONE DAY", strap_font, GOLD, letter_spacing=6)

    # --- 2x2 photo grid ---
    for i, panel in enumerate(PANELS):
        col, row = i % 2, i // 2
        x0 = MARGIN + col * (CELL_W + GUTTER)
        y0 = MASTHEAD_H + row * (ROW_H + GUTTER)

        src = Image.open(os.path.join(PANELS_DIR, panel["file"])).convert("RGB")
        canvas.paste(centre_crop_resize(src, CELL_W, PHOTO_H), (x0, y0))

        # caption bar: kicker (red bold) + headline (black bold, max 2 lines).
        # Both headline lines must fit inside the 72px bar: kicker 18px at
        # +2, headline 23px starting at +24 with a 24px line pitch, so the
        # second line ends at ~71px instead of overflowing into the next row.
        cap_y = y0 + PHOTO_H
        pad = 12
        kicker_font = font(BOLD, 18)
        draw.text((x0 + pad, cap_y + 2), panel["kicker"], font=kicker_font, fill=RED)
        head_font = font(BOLD, 23)
        max_w = CELL_W - 2 * pad
        lines = wrap_text(draw, panel["headline"], head_font, max_w)
        size = 23
        while len(lines) > 2 and size > 18:
            size -= 1
            head_font = font(BOLD, size)
            lines = wrap_text(draw, panel["headline"], head_font, max_w)
        ly = cap_y + 24
        for line in lines:
            draw.text((x0 + pad, ly), line, font=head_font, fill=BLACK)
            ly += size + 1

    # --- footer ticker: black band, centred white text ---
    fy = H - FOOTER_H
    draw.rectangle([0, fy, W, H], fill=BLACK)
    ticker_font = fit_font(draw, TICKER, REGULAR, 23, W - 32, min_size=14)
    # vertically centre the single line in the 56px band
    bbox = draw.textbbox((0, 0), TICKER, font=ticker_font)
    th = bbox[3] - bbox[1]
    draw_centred(draw, fy + (FOOTER_H - th) / 2 - bbox[1], TICKER, ticker_font, WHITE)

    return canvas


def main():
    canvas = compose()
    assert canvas.size == (W, H), canvas.size
    # JPEG bytes under the name entry.png; lower quality until under the limit.
    for quality in (85, 82, 80, 78, 75):
        buf = io.BytesIO()
        canvas.save(buf, format="JPEG", quality=quality)
        data = buf.getvalue()
        if len(data) <= 1_048_576:
            break
    with open(OUT_PATH, "wb") as fh:
        fh.write(data)
    print(f"wrote {OUT_PATH}: {len(data)} bytes, quality={quality}, size={canvas.size}")


if __name__ == "__main__":
    main()
