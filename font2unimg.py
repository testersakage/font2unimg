#!/usr/bin/env python3
import sys
import os
import json
from PIL import Image, ImageDraw, ImageFont

# --- デフォルト設定 ---
CONFIG = {
    "grid_w": 32,
    "grid_h": 8,
    "prefix": "unicode_page",
    "save_dir": "./unicode_pages",
    "load_path": "",
    "smooth": "off",
    "color": (255, 255, 255, 255),
    "upscale": 4,
    "threshold": 128,
    "pt": 12.0,
    "dpi": 72.0,
    "width": 12
}

def analyze_font_metrics(load_path, pt, dpi):
    """フォントの設計図を可視化する計器"""
    px_size = (pt * dpi) / 72.0
    try:
        font = ImageFont.truetype(load_path, int(px_size))
    except:
        return
    
    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    
    print("\n" + "="*45)
    print(f" SDL3-Style Font Metrics Analysis ")
    print("="*45)
    print(f" Font Path     : {load_path}")
    print(f" Calc Size     : {px_size:.2f} px (at {pt}pt, {dpi}dpi)")
    print(f" Ascent (Up)   : {ascent} px")
    print(f" Descent (Down): {descent} px")
    print(f" Total Height  : {line_height} px")
    print("-" * 45)
    print(f" {'Char':<4} | {'Width':<5} | {'BBox (L, T, R, B)':<20}")
    print("-" * 45)
    for ch in ["A", "g", "j", "あ", "|", "（", "鬱"]:
        bbox = font.getbbox(ch)
        if bbox:
            w = bbox[2] - bbox[0]
            print(f" {ch:<4} | {w:<5} | {bbox}")
    print("="*45 + "\n")

def parse_args():
    global CONFIG
    # 1. Config読込
    for arg in sys.argv[1:]:
        if arg.startswith("-config="):
            conf_path = arg.split("=", 1)[1]
            if os.path.exists(conf_path):
                try:
                    with open(conf_path, 'r', encoding='utf-8-sig') as f:
                        CONFIG.update(json.load(f))
                except Exception as e:
                    print(f"[!] Config Error: {e}"); sys.exit(1)

    # 2. 引数読込
    for arg in sys.argv[1:]:
        if "=" not in arg: continue
        key, val = arg.split("=", 1)
        if key == "-load":      CONFIG["load_path"] = val
        elif key == "-pt":      CONFIG["pt"] = float(val)
        elif key == "-dpi":     CONFIG["dpi"] = float(val)
        elif key == "-upscale": CONFIG["upscale"] = int(val)
        elif key == "-threshold": CONFIG["threshold"] = int(val)
        elif key == "-save":    CONFIG["save_dir"] = val
        elif key == "-prefix":  CONFIG["prefix"] = val
        elif key == "-smooth":  CONFIG["smooth"] = val.lower()
        elif key == "-color":   CONFIG["color"] = (255,255,255,255) if val=="w" else (0,0,0,255)
        elif key == "-page":
            w, h = val.lower().split("x")
            CONFIG["grid_w"], CONFIG["grid_h"] = int(w), int(h)
        elif key in ["-help", "--help"]:
            print("Options: -config, -load, -pt, -dpi, -upscale, -threshold, -smooth, -save, -page, -color"); sys.exit(0)

    os.makedirs(CONFIG["save_dir"], exist_ok=True)
    print("\n" + "="*45 + "\n FINAL RUNTIME SETTINGS \n" + "="*45)
    for k, v in CONFIG.items(): print(f" {k:<15}: {v}")
    print("="*45)

def render_glyph_v3(ch, load_path, pt, dpi, width):
    """
    SDL3準拠: ベースライン(11px目)を基準とした固定配置エンジン
    width: 半角なら6, 全角なら12を想定
    """
    upscale = CONFIG["upscale"]
    # 1. SDL3準拠の精密サイズ計算
    px_size = (pt * dpi) / 72.0
    target_px = px_size * upscale
    font = ImageFont.truetype(load_path, int(target_px))
    
    # 2. メトリクス取得（SDL3流：共通のアセント値を基準にする）
    ascent, descent = font.getmetrics()
    
    # 3. 器（14px高）の拡大版作成
    canvas_h = 14 * upscale
    canvas_w = width * upscale
    res_large = Image.new("L", (canvas_w, canvas_h), 0)
    
    # 基準線（ベースライン）を上から11px目に固定
    baseline_y = 11 * upscale
    
    # SDL3の流儀：個別の文字のbboxに左右されず、フォント全体の基準位置で描画
    # 横方向：左端(0)から描画。半角6px / 全角12pxの枠内でフォント自身の幅に従う
    # 縦方向：ベースラインからascent分だけ上にずらした位置を固定の開始点とする
    draw_x = 0 
    draw_y = baseline_y - ascent
    
    # 描画
    draw = ImageDraw.Draw(res_large)
    draw.text((draw_x, draw_y), ch, font=font, fill=255)

    # 4. 縮小 & 2値化
    # smoothがonならLANCZOS、offならNEAREST（パキパキ重視）
    resample_method = Image.LANCZOS if CONFIG["smooth"] == "on" else Image.NEAREST
    
    if upscale > 1:
        res = res_large.resize((width, 14), resample=resample_method)
    else:
        res = res_large

    if CONFIG["threshold"] >= 0:
        res = res.point(lambda p: 255 if p > CONFIG["threshold"] else 0)
    
    return res

def draw_page(page):
    width_base = CONFIG["width"] # 基本12
    gw, gh = CONFIG["grid_w"], CONFIG["grid_h"]
    img = Image.new("RGBA", (width_base * gw, 14 * gh), (0, 0, 0, 0))

    for index in range(256):
        cp = page * 256 + index
        ch = chr(cp)
        
        # --- 半角判定ロジック ---
        # 1. ASCII範囲 (0x00-0x7F)
        # 2. 半角カタカナ範囲 (0xFF61-0xFF9F)
        if (0x00 <= cp <= 0x7F) or (0xFF61 <= cp <= 0xFF9F):
            char_w = 6
        else:
            char_w = 12
        
        col, row = index % gw, index // gw
        # 描画先x座標は、grid_w(32)x12px の中で「左詰め」になるように配置
        # (半角でも12pxのグリッド枠の中で左側に居座る形)
        target_x = col * width_base 
        target_y = row * 14

        glyph = render_glyph_v3(ch, CONFIG["load_path"], CONFIG["pt"], CONFIG["dpi"], char_w)

        g_rgba = Image.new("RGBA", (glyph.width, glyph.height), CONFIG["color"])
        g_rgba.putalpha(glyph)
        
        # 12pxの枠内の(target_x, target_y)に、6pxまたは12pxのglyphを貼り付け
        img.paste(g_rgba, (target_x, target_y), g_rgba)

    filename = os.path.join(CONFIG["save_dir"], f"{CONFIG['prefix']}_{page:02x}.png")
    img.save(filename)
    print(f"[*] Saved: {filename}")

def main():
    parse_args()
    if not os.path.exists(CONFIG["load_path"]):
        print(f"[!] Font not found: {CONFIG['load_path']}"); sys.exit(1)
    
    # 実行前に解析を表示（職人の計器）
    analyze_font_metrics(CONFIG["load_path"], CONFIG["pt"], CONFIG["dpi"])
    
    for page in range(256):
        draw_page(page)
    print("\n[!] All pages generated successfully.")

if __name__ == "__main__":
    main()
