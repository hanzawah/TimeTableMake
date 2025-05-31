import os
import shutil
import datetime
from jinja2 import Environment, FileSystemLoader
import pandas as pd
import re
import csv # csvモジュールを追加

# --- 設定 ---
DATA_DIR = "data"
SRC_DIR = "src"
TEMPLATES_DIR = os.path.join(SRC_DIR, "templates")
GITHUB_PAGES_OUTPUT_BASE_DIR = "docs" 

GITHUB_PAGES_BASE_URL = "https://hanzawah.github.io/TimeTableMake/" 

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# --- 日付関連ユーティリティ関数 ---
def get_week_range_string(date=None):
    if date is None:
        date = datetime.date.today()
    start_of_week = date - datetime.timedelta(days=date.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    return f"{start_of_week.strftime('%Y-%m-%d')}_{end_of_week.strftime('%m-%d')}"

# --- Shift_JIS文字列のデコードヘルパー ---
def decode_sjis(s):
    if isinstance(s, str):
        try:
            return s.encode('latin1').decode('cp932')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
    return str(s)

# --- クラス名からファイル名を生成するヘルパー関数 ---
def generate_filename_from_classname(class_name):
    class_name = class_name.replace('－', '-')
    class_name = class_name.replace('１', '1').replace('２', '2').replace('３', '3') 
    
    class_name_parts = []
    for part in class_name.split(' '):
        if part == '年':
            class_name_parts.append('nen')
        elif part == '組':
            class_name_parts.append('gumi')
        elif part == '理探':
            class_name_parts.append('ritan')
        elif part == '国探':
            class_name_parts.append('kokutan')
        elif part == '総理':
            class_name_parts.append('souri')
        else:
            class_name_parts.append(part)
    
    filename_base = "".join(class_name_parts).replace(' ', '_').replace('　', '_')
    filename_base = re.sub(r'[\\/:*?"<>|]', '', filename_base)
    return f"class_{filename_base}.html"

# --- CSVから時間割HTMLテーブルを生成する関数 (クラス一覧.csv特化版) ---
def generate_timetable_table_html_from_class_csv(class_row, header_periods, header_day_columns_map):
    class_name_encoded = class_row.iloc[0]
    class_name = decode_sjis(class_name_encoded).strip()

    html_table = f"<h3>{class_name}の時間割詳細</h3>"
    html_table += "<table border='1' style='width:100%; border-collapse: collapse; text-align: center;'>"
    
    days_of_week = ["月", "火", "水", "木", "金"] 
    html_table += "<thead><tr><th>時限</th>"
    for day in days_of_week:
        html_table += f"<th>{day}</th>"
    html_table += "</tr></thead>"
    
    html_table += "<tbody>"
    
    for period in sorted(header_periods):
        html_table += f"<tr><td>{period}</td>"
        try:
            period_idx_in_day_list = header_periods.index(period) 
        except ValueError:
            period_idx_in_day_list = -1 

        for day in days_of_week:
            lesson = "-" 
            if day in header_day_columns_map and period_idx_in_day_list != -1:
                col_index_in_csv = header_day_columns_map[day][period_idx_in_day_list]
                
                if col_index_in_csv < len(class_row): 
                    lesson_encoded = class_row.iloc[col_index_in_csv]
                    lesson = decode_sjis(lesson_encoded).strip()
                    if not lesson:
                        lesson = "-"
                else:
                    lesson = "-" 
            html_table += f"<td>{lesson}</td>"
        html_table += "</tr>"
        
    html_table += "</tbody></table>"
    return html_table

# --- メインのHTML生成関数 ---
def generate_all_htmls():
    class_list_csv_path = os.path.join(DATA_DIR, "クラス一覧.csv")

    # ★ここからCSVヘッダーの読み込み方法を修正！★
    header_dates_decoded = []
    unique_periods = []
    header_day_columns_map = {}
    week_range_str = get_week_range_string(datetime.date.today()) # デフォルト値

    try:
        # csvモジュールを使って生データを読み込む
        with open(class_list_csv_path, 'r', encoding='cp932', newline='') as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            rows = list(reader) # 全行をリストとして読み込む
            
            if len(rows) < 3:
                raise ValueError("CSVファイルは少なくとも3行のヘッダーが必要です。")

            # 2行目から日付情報を抽出・デコード
            # .iloc[1] は DataFrame の場合なので、リストの2番目の要素 [1]
            header_dates_encoded_row = rows[1][1:] # 2行目(index 1)の2列目以降
            header_dates_decoded = [decode_sjis(s).strip() for s in header_dates_encoded_row if s.strip() or s == '" "'] # 空白フィールドも考慮

            # 週の範囲を特定
            first_valid_date_str = None
            for date_entry in header_dates_decoded:
                if date_entry: 
                    first_date_str_match = re.search(r'(\d{1,2}/\d{1,2})', date_entry)
                    if first_date_str_match:
                        first_date_str = first_date_str_match.group(1)
                        break
            
            if first_date_str:
                current_year = datetime.date.today().year
                first_date_obj = datetime.datetime.strptime(f"{current_year}/{first_date_str}", "%Y/%m/%d").date()
                week_range_str = get_week_range_string(first_date_obj)
                print(f"CSVヘッダーから週の範囲を特定しました: {week_range_str}")
            else:
                print(f"警告: CSVヘッダーから有効な日付を特定できませんでした。今週の範囲 ({week_range_str}) で生成します。")

            # 3行目から時限情報を抽出・デコード
            header_periods_raw_row = rows[2][1:] # 3行目(index 2)の2列目以降
            header_periods_decoded = [decode_sjis(s).strip() for s in header_periods_raw_row if s.strip() or s == '" "'] 
            
            unique_periods = sorted(list(set([s.replace('１','1').replace('２','2').replace('３','3').replace('４','4').replace('５','5').replace('６','6') for s in header_periods_decoded if s])))
            
            # 各曜日のデータの開始列インデックスをマッピング (元のCSV列インデックスに基づく)
            header_day_columns_map = {}
            days_of_week_long = ["月", "火", "水", "木", "金"]
            
            current_col_idx_in_csv = 7 # クラス名(1) + 空白列(6) = 7列目からデータ
            num_periods_per_day = len(unique_periods) # 1日あたりの時限数
            
            for day in days_of_week_long:
                day_indices = []
                for _ in range(num_periods_per_day):
                    day_indices.append(current_col_idx_in_csv)
                    current_col_idx_in_csv += 1
                header_day_columns_map[day] = day_indices

            print(f"CSVヘッダーから抽出した時限: {unique_periods}")
            print(f"列インデックスマッピング: {header_day_columns_map}")

    except FileNotFoundError:
        print(f"エラー: クラス一覧ファイル '{class_list_csv_path}' が見つかりません。スクリプトを終了します。")
        return
    except Exception as e:
        print(f"エラー: クラス一覧ファイル '{class_list_csv_path}' のヘッダー読み込み中に問題が発生しました: {e}")
        print("CSVファイルのエンコーディングや形式を再度確認してください。")
        print("CSVの先頭数行（メモ帳で開いた生データ）を共有してください。")
        return

    # --- 共通の出力ディレクトリ設定 ---
    latest_output_dir = os.path.join(GITHUB_PAGES_OUTPUT_BASE_DIR, "latest")
    archive_output_dir = os.path.join(GITHUB_PAGES_OUTPUT_BASE_DIR, week_range_str)

    # --- 1. 古い latest/ の内容をアーカイブディレクトリへ移動 ---
    if os.path.exists(latest_output_dir) and os.listdir(latest_output_dir):
        if not os.path.exists(archive_output_dir):
            os.makedirs(archive_output_dir)
        
        for item_name in os.listdir(latest_output_dir):
            item_path = os.path.join(latest_output_dir, item_name)
            if os.path.isfile(item_path) and item_name == ".gitkeep":
                continue 
            shutil.move(item_path, archive_output_dir)
        print(f"古い時間割を {archive_output_dir} にアーカイブしました。")
    else:
        print("アーカイブする古い時間割はありません。")

    # --- 2. GitHub Pages出力ディレクトリ (docs/latest/) を準備 ---
    if not os.path.exists(latest_output_dir):
        os.makedirs(latest_output_dir)

    # --- 3. クラス一覧.csv をデータフレームとして読み込む (データ部分のみ) ---
    # skiprows=3 でヘッダーをスキップし、データ部分を読み込む
    # engine='python' はそのまま維持
    class_list_data_df = pd.DataFrame() # 初期化
    try:
        class_list_data_df = pd.read_csv(class_list_csv_path, encoding='cp932', header=None, skiprows=3, sep=',', quotechar='"', skipinitialspace=True, engine='python')
    
    except FileNotFoundError:
        print(f"エラー: クラス一覧ファイル '{class_list_csv_path}' が見つかりません。スクリプトを終了します。")
        return
    except Exception as e:
        print(f"エラー: クラス一覧ファイル '{class_list_csv_path}' のデータ読み込み中に問題が発生しました: {e}")
        print("CSVファイルのエンコーディングや形式を確認してください。")
        return

    # --- 4. 目次HTML (index.html) を生成 ---
    index_template = env.get_template('index_template.html')
    class_links_for_index = []
    
    for idx, class_row_data in class_list_data_df.iterrows():
        class_name_encoded = class_row_data.iloc[0] 
        class_name_decoded = decode_sjis(class_name_encoded).strip()
        if not class_name_decoded:
            continue

        filename = generate_filename_from_classname(class_name_decoded)
        class_links_for_index.append({"name": class_name_decoded, "filename": filename})

    index_html_content = index_template.render(
        week_range=week_range_str,
        class_list=class_links_for_index,
        github_pages_base_url=GITHUB_PAGES_BASE_URL
    )
    with open(os.path.join(latest_output_dir, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html_content)
    print(f"目次HTMLを {os.path.join(latest_output_dir, 'index.html')} に生成しました。")

    # --- 5. 各クラスのHTMLを生成 ---
    class_template = env.get_template('class_template.html')
    
    for idx, class_row_data in class_list_data_df.iterrows():
        class_name_encoded = class_row_data.iloc[0]
        class_name_decoded = decode_sjis(class_name_encoded).strip()
        if not class_name_decoded:
            continue

        timetable_table_html = generate_timetable_table_html_from_class_csv(
            class_row_data, unique_periods, header_day_columns_map
        )

        filename = generate_filename_from_classname(class_name_decoded)

        class_html_content = class_template.render(
            week_range=week_range_str,
            class_name=class_name_decoded,
            timetable_table_html=timetable_table_html,
            github_pages_base_url=GITHUB_PAGES_BASE_URL
        )
        with open(os.path.join(latest_output_dir, filename), 'w', encoding='utf-8') as f:
            f.write(class_html_content)
        print(f"{class_name_decoded} の時間割HTMLを {os.path.join(latest_output_dir, filename)} に生成しました。")

    print("すべての時間割HTMLの生成が完了しました！")


if __name__ == "__main__":
    if not os.environ.get('VIRTUAL_ENV'):
        print("警告: 仮想環境が有効化されていません。")
        print("スクリプトを実行する前に `.venv\\Scripts\\Activate.ps1` を実行してください。")
    
    generate_all_htmls()