#!/usr/bin/env python3
import sys
import os
from PIL import Image, ImageDraw, ImageFont

CELL = 12
GRID_W = 32
GRID_H = 8
PREFIX = "unicode_page"
SAVE_DIR = "./unicode_pages"
FONT_PATH = "NotoSansCJK-Regular.ttc"
FONT_SIZE = 12
SMOOTH = True
COLOR = (255,255,255,255)  # default white

# --- shift オプション追加 ---
SHIFT_X = 0
SHIFT_Y = 0

HELP_TEXT = """
Usage:
  python font2unimg.py [options]

Options:
  -cell=<px>          1セルのサイズ(px)。0〜24。デフォルト: 12
  -page=<W>x<H>       グリッド数（横x縦）。デフォルト: 32x8
  -prefix=<name>      出力ファイル名のプリフィックス。デフォルト: unicode_page
  -save=<path>        保存先ディレクトリ
  -font=<path>        使用するフォントファイル
  -size=<px>          フォントサイズ(px)。デフォルト: 12
  -smooth=on/off      アンチエイリアスの有無
  -color=w/b          文字色（white / black）
  -shift=x,y          描画位置の補正(px)
"""

def parse_args():
    global CELL, GRID_W, GRID_H, PREFIX, SAVE_DIR, FONT_PATH, FONT_SIZE, SMOOTH, COLOR
    global SHIFT_X, SHIFT_Y

    if len(sys.argv) == 1:
        print(HELP_TEXT)
        sys.exit(0)

    for arg in sys.argv[1:]:
        if arg.startswith("-cell="):
            CELL = int(arg.split("=")[1])
            CELL = max(1, min(CELL, 24))

        elif arg.startswith("-page="):
            w, h = arg.split("=")[1].lower().split("x")
            GRID_W = int(w)
            GRID_H = int(h)

        elif arg.startswith("-prefix="):
            PREFIX = arg.split("=")[1]

        elif arg.startswith("-save="):
            SAVE_DIR = arg.split("=")[1]

        elif arg.startswith("-font="):
            FONT_PATH = arg.split("=")[1]

        elif arg.startswith("-size="):
            FONT_SIZE = int(arg.split("=")[1])

        elif arg.startswith("-smooth="):
            SMOOTH = (arg.split("=")[1].lower() == "on")

        elif arg.startswith("-color="):
            val = arg.split("=")[1].lower()
            if val == "w":
                COLOR = (255,255,255,255)
            elif val == "b":
                COLOR = (0,0,0,255)
            else:
                print("Invalid -color (use w or b)")
                sys.exit(1)

        # --- shift オプション追加 ---
        elif arg.startswith("-shift="):
            xy = arg.split("=")[1]
            if "," in xy:
                sx, sy = xy.split(",")
                SHIFT_X = int(sx)
                SHIFT_Y = int(sy)
            else:
                print("Invalid -shift (use -shift=x,y)")
                sys.exit(1)

        else:
            print(f"Unknown option: {arg}")
            print(HELP_TEXT)
            sys.exit(1)

    os.makedirs(SAVE_DIR, exist_ok=True)
    

def render_glyph(ch, font, cell, smooth):
    if cell < 16:
        BIG = cell * 4
        big_font = ImageFont.truetype(FONT_PATH, BIG)

        big = Image.new("L", (BIG * 2, BIG * 2), 0)
        bdraw = ImageDraw.Draw(big)
        bdraw.text((0, 0), ch, fill=255, font=big_font)

        bbox = big.getbbox()
        if bbox is None:
            return Image.new("L", (cell, cell), 0)

        glyph = big.crop(bbox)

        if smooth:
            glyph = glyph.resize((cell, cell), Image.LANCZOS)
        else:
            glyph = glyph.resize((cell, cell), Image.NEAREST)

        return glyph

    else:
        mask = font.getmask(ch)
        w, h = mask.size
        glyph = Image.new("L", (w, h), 0)
        glyph.putdata(list(mask))
        return glyph


def draw_page(page, font):
    img_w = CELL * GRID_W
    img_h = CELL * GRID_H

    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))

    ascent, descent = font.getmetrics()

    for index in range(256):
        codepoint = page * 256 + index
        ch = chr(codepoint)

        col = index % GRID_W
        row = index // GRID_W

        x = col * CELL
        y = row * CELL

        glyph = render_glyph(ch, font, CELL, SMOOTH)

        w, h = glyph.size

        dx = (CELL - w) // 2
        dy = (CELL - ascent) // 2

        # --- shift オプション適用 ---
        dx += SHIFT_X
        dy += SHIFT_Y
        
        g_rgba = Image.new("RGBA", (w, h), COLOR)
        g_rgba.putalpha(glyph)

        img.paste(g_rgba, (x + dx, y + dy), g_rgba)

    filename = os.path.join(SAVE_DIR, f"{PREFIX}_{page:02x}.png")
    img.save(filename)
    print("saved", filename)


def main():
    parse_args()

    print(f"Cell={CELL}  Smooth={'on' if SMOOTH else 'off'}  Color={COLOR}")

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    for page in range(256):
        draw_page(page, font)


if __name__ == "__main__":
    main()
