#!/usr/bin/env python3
import sys
import os
import json
from PIL import Image, ImageDraw, ImageFont

# --- デフォルト設定 ---
CONFIG = {
    "width": 12,           # 1セルの幅(px)
    "grid_w": 32,
    "grid_h": 8,
    "prefix": "unicode_page",
    "save_dir": "./unicode_pages",
    "load_path": "",
    "height": 12,          # フォントの高さ(px)
    "smooth": True,
    "color": (255, 255, 255, 255),
    "shift_x": 0,
    "shift_y": 0,
    "threshold": -1,
    "upscale": 1,          # 超解像倍率
    "auto_crop": True,
    "auto_padding": True
}

HELP_TEXT = """
Usage:
  python font2unimg.py [options]

Options:
  -config=<path.json> 設定ファイルを読み込み（引数指定が優先）
  -width=<px>         1セルのサイズ。デフォルト: 12
  -page=<W>x<H>       グリッド数（横x縦）。デフォルト: 32x8
  -prefix=<name>      出力名の接頭辞
  -save=<path>        保存先ディレクトリ
  -load=<path>        フォントファイルへのパス
  -height=<px>        フォントサイズ。デフォルト: 12
  -smooth=on/off      アンチエイリアスの有無
  -color=w/b          文字色（white / black）
  -shift="x,y"        描画位置の補正(px)
  -threshold="x"      2値化の閾値(0-255, -1で無効)
  -upscale=<N>        超解像倍率(1, 2, 4...)
  -crop=on/off        自動クロップの有無
  -padding=on/off     自動パディングの有無
"""

def parse_args():
    global CONFIG

    # 1. 予備スキャン: configファイルの読み込み
    for arg in sys.argv[1:]:
        if arg.startswith("-config="):
            conf_path = arg.split("=", 1)[1]
            print(f"[*] Attempting to load config: {conf_path}") # 読み込み開始を表示
            
            if os.path.exists(conf_path):
                try:
                    with open(conf_path, 'r', encoding='utf-8') as f:
                        file_conf = json.load(f)
                        CONFIG.update(file_conf)
                        print(f"[*] Successfully loaded config: {conf_path}")
                except json.JSONDecodeError as e:
                    # ★ JSONの書式エラーを具体的に表示
                    print(f"\n[!] JSON Syntax Error in '{conf_path}':")
                    print(f"    Line {e.lineno}, Col {e.colno}: {e.msg}")
                    print("    (Check for missing commas or unescaped quotes!)\n")
                    sys.exit(1)
                except Exception as e:
                    print(f"[!] Unexpected error loading config: {e}")
                    sys.exit(1)
            else:
                print(f"[!] Config file not found: {conf_path}")
                sys.exit(1)

    # 2. メインスキャン: 引数による上書き
    for arg in sys.argv[1:]:
        if "=" not in arg:
            continue
        parts = arg.split("=", 1)
        key = parts[0]
        val = parts[1]

        if key == "-width":
            CONFIG["width"] = int(val)
        elif key == "-page":
            w, h = val.lower().split("x")
            CONFIG["grid_w"], CONFIG["grid_h"] = int(w), int(h)
        elif key == "-prefix":
            CONFIG["prefix"] = val
        elif key == "-save":
            CONFIG["save_dir"] = val
        elif key == "-load":
            CONFIG["load_path"] = val
        elif key == "-height":
            CONFIG["height"] = int(val)
        elif key == "-smooth":
            CONFIG["smooth"] = (val.lower() == "on")
        elif key == "-threshold":
            CONFIG["threshold"] = int(val)
        elif key == "-upscale":
            CONFIG["upscale"] = int(val)
        elif key == "-crop":
            CONFIG["auto_crop"] = (val.lower() == "on")
        elif key == "-padding":
            CONFIG["auto_padding"] = (val.lower() == "on")
        elif key == "-color":
            CONFIG["color"] = (255, 255, 255, 255) if val.lower() == "w" else (0, 0, 0, 255)
        elif key == "-shift":
            sx, sy = val.split(",")
            CONFIG["shift_x"], CONFIG["shift_y"] = int(sx), int(sy)
        elif key == "-help" or key == "--help":
            print(HELP_TEXT); sys.exit(0)

    # 保存先ディレクトリ作成
    os.makedirs(CONFIG["save_dir"], exist_ok=True)

    # --- 最終的な設定を表示 ---
    print("\n" + "="*30)
    print(" FINAL RUNTIME SETTINGS ")
    print("="*30)
    for k, v in CONFIG.items():
        # special_shifts は長いので件数だけ表示
        if k == "special_shifts":
            print(f" {k:<15}: {len(v)} rules defined")
        else:
            print(f" {k:<15}: {v}")
    print("="*30 + "\n")

def render_glyph(ch, load_path, height, width):
    upscale = CONFIG["upscale"]
    target_height = height * upscale
    target_width = width * upscale
    
    font = ImageFont.truetype(load_path, target_height)
    
    bbox = font.getbbox(ch)
    if bbox:
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    else:
        w, h = 0, 0

    w = max(1, w)
    h = max(1, h)

    large_glyph = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(large_glyph)
    draw.text((-bbox[0] if bbox else 0, -bbox[1] if bbox else 0), ch, font=font, fill=255)

    res_large = Image.new("L", (target_width, target_width), 0)
    
    off_x = max(0, (target_width - w) // 2) if CONFIG["auto_padding"] else 0
    off_y = max(0, (target_width - h) // 2) if CONFIG["auto_padding"] else 0
    
    res_large.paste(large_glyph.crop((0, 0, target_width, target_width)), (off_x, off_y))

    if upscale > 1:
        res = res_large.resize((width, width), resample=Image.LANCZOS)
    else:
        res = res_large

    if CONFIG["threshold"] >= 0:
        res = res.point(lambda p: 255 if p > CONFIG["threshold"] else 0)
    
    return res
    
def draw_page(page, fontarray):
    width = CONFIG["width"]
    gw, gh = CONFIG["grid_w"], CONFIG["grid_h"]
    img = Image.new("RGBA", (width * gw, width * gh), (0, 0, 0, 0))
    ascent, descent = fontarray.getmetrics()

    for index in range(256):
        codepoint = page * 256 + index
        ch = chr(codepoint)
        col, row = index % gw, index // gw
        x, y = col * width, row * width

        glyph = render_glyph(ch, CONFIG["load_path"], CONFIG["height"], width)

        if CONFIG["auto_padding"]:
            dx = (width - glyph.width) // 2
            dy = (width - ascent) // 2
        else:
            dx = 0
            dy = 0

        char_shift_x = 0
        char_shift_y = 0
        if "special_shifts" in CONFIG:
            for rule in CONFIG["special_shifts"]:
                if ch in rule["chars"]:
                    char_shift_x += rule.get("x", 0)
                    char_shift_y += rule.get("y", 0)

        final_x = x + dx + CONFIG["shift_x"] + char_shift_x
        final_y = y + dy + CONFIG["shift_y"] + char_shift_y

        g_rgba = Image.new("RGBA", (glyph.width, glyph.height), CONFIG["color"])
        g_rgba.putalpha(glyph)
        img.paste(g_rgba, (final_x, final_y), g_rgba)

    filename = os.path.join(CONFIG["save_dir"], f"{CONFIG['prefix']}_{page:02x}.png")
    img.save(filename)
    print(f"[*] Saved {filename}")

def main():
    if len(sys.argv) == 1:
        print(HELP_TEXT); sys.exit(0)
    
    parse_args()
    
    if not CONFIG["load_path"] or not os.path.exists(CONFIG["load_path"]):
        print(f"Error: Font not found at {CONFIG['load_path']}")
        sys.exit(1)
    
    try:
        fontarray = ImageFont.truetype(CONFIG["load_path"], CONFIG["height"])
        for page in range(256):
            draw_page(page, fontarray)
        print("\n[!] All pages generated successfully.")
    except Exception as e:
        print(f"Failed to load font: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
