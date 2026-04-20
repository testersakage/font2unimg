## font2unimg V3 (Unicode Atlas Generator)  
TrueType フォントから、Luanti 近代化エンジン（V3）専用の高精度 Unicode アトラスを生成します。
従来の 12px 規格では解決できなかった「文字の欠け」や「ベースラインのズレ」を、フォントメトリクスの自動解析によって根本から解決するために開発されました。
------------------------------
## 🔧 このツールの革新的な機能  
## 1. JSON 設定ファイルによる一括管理  

* プロファイル運用: フォント名、サイズ、オフセット、出力先などの設定を JSON 形式で保存・管理可能。
* 再現性の確保: 一度決めた「職人の設定」をファイルとして残せるため、フォントの再生成や微調整が極めて容易になります。

## 2. 14px ハイ・アスペクト設計  

* アンチ・クリッピング: 従来の 12x12px では収まりきらなかった括弧の底、キリル文字、アクセント記号を救済するため、14px 高 での焼き付けに対応。
* 1px の聖域: 行間 0px で文字を積み上げても、上下の文字が干渉せず、かつ 1px も欠けない「職人品質」の表示を実現します。

## 3. 11px ベースラインの黄金律  

* フォントの内部データを解析し、すべての文字を 11px 目をベースライン として整列させます。
* 日本語、英語、ロシア語などが混在しても、すべての文字の「腰の高さ」がパキッと揃い、視認性が飛躍的に向上します。

------------------------------
## 🚀 使い方  
## 依存関係  

* Python 3.x
* Pillow (PIL)

## 設定ファイルの例 (config.json)  

{  
    "font_path": "./msgothic.ttc",  
    "font_size": 12,  
    "line_height": 14,  
    "offset_y": 1,  
    "output_dir": "./output_v3"  
}  

## 実行例

# JSON設定ファイルを使用して実行
python font2unimg.py --config config.json 
# コマンドライン引数での直接指定も可能
python font2unimg.py --font ./msgothic.ttc --size 12 --line_height 14  

------------------------------
## 📘 English Overview
This tool generates high-precision Unicode font atlases optimized for the Luanti Unicode Modernization Engine (V3).

* JSON Configuration Support: Manage font paths, sizes, and rendering offsets via JSON files for consistent and reproducible builds.
* 14px Height Canvas: Prevents character clipping (e.g., lower parts of parentheses or Cyrillic characters) that occurs in standard 12px grids.
* Fixed 11px Baseline: Synchronizes the visual "waistline" of characters across all languages by referencing font metrics.

------------------------------
## 📝 補足

* 生成されたアトラスは、Luanti 本体の utf8combine API と組み合わせて使用します。
* AI (Copilot / Gemini) との対話を通じて、数学的に正確なピクセル配置を実現するロジックを構築しました。

