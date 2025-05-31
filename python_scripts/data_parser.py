import pandas as pd
import csv
import re
import datetime
from python_scripts import utils

def parse_class_list_header(csv_path, encoding, csv_data_start_col_offset, num_periods_per_day_config):
    """
    CSVファイルのヘッダーを解析する（最終FIX版）。
    日付と授業データの異なる列パターン（ストライド）を個別に正しく処理する。
    授業データの列マッピングのストライドをデータ行の実際の構造に合わせる。
    """
    try:
        with open(csv_path, 'r', encoding='cp932', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            if len(rows) < 3:
                raise ValueError(f"CSVファイル '{csv_path}' は少なくとも3行のヘッダーが必要です。")

            days_of_week = ["月", "火", "水", "木", "金"]
            unique_periods = [str(i) for i in range(1, num_periods_per_day_config + 1)]
            date_row = rows[1]
            
            # --- 1. 授業データの列インデックスを計算 ---
            # データ行では、各曜日の授業データブロックは区切り列なしに連続している
            # (例: 月曜6限の次が火曜1限)
            # そのため、ストライドは1日の時限数そのものになる
            header_day_columns_map = {}
            current_lesson_col_idx = csv_data_start_col_offset # config.py から (通常は1)
            lesson_stride = num_periods_per_day_config        # ★★★ 修正点 ★★★ (データ行の構造に合わせる)
            for day_char in days_of_week:
                day_column_indices = list(range(current_lesson_col_idx, current_lesson_col_idx + num_periods_per_day_config))
                header_day_columns_map[day_char] = day_column_indices
                current_lesson_col_idx += lesson_stride

            # --- 2. 日付ヘッダーの文字列を計算 ---
            # CSVの2行目(日付行)では、日付はインデックス 1, 7, 13, 19, 25 に配置 (ストライド6)
            header_dates_decoded = []
            current_date_col_idx = 1  # 月曜日の日付は常にインデックス1から
            date_stride = 6           # 日付間の実際の列の進み幅
            for day_char in days_of_week:
                date_string_for_header = ""
                if current_date_col_idx < len(date_row):
                    decoded_date_cell_value = date_row[current_date_col_idx].strip()
                    if re.search(r'\d{1,2}/\d{1,2}', decoded_date_cell_value):
                        date_string_for_header = decoded_date_cell_value
                
                if not date_string_for_header:
                    date_string_for_header = f"({day_char})"
                
                header_dates_decoded.append(date_string_for_header)
                current_date_col_idx += date_stride

            # --- 週範囲文字列の特定 ---
            week_range_str = utils.get_week_range_string(datetime.date.today())
            first_valid_date_entry = next((d for d in header_dates_decoded if re.search(r'\d{1,2}/\d{1,2}', d)), None)

            if first_valid_date_entry:
                date_part_match = re.search(r'(\d{1,2}/\d{1,2})', first_valid_date_entry)
                if date_part_match:
                    date_part_str = date_part_match.group(1)
                    current_year = datetime.date.today().year
                    try:
                        first_date_object = datetime.datetime.strptime(f"{current_year}/{date_part_str}", "%Y/%m/%d").date()
                        week_range_str = utils.get_week_range_string(first_date_object)
                    except ValueError:
                         pass 
            
            return {
                "week_range_str": week_range_str, 
                "unique_periods": unique_periods, 
                "header_day_columns_map": header_day_columns_map,
                "header_dates_decoded": header_dates_decoded 
            }

    except FileNotFoundError:
        raise FileNotFoundError(f"エラー: クラス一覧ファイル '{csv_path}' が見つかりません。")
    except Exception as e:
        import traceback
        print("--- parse_class_list_header でエラーが発生しました ---")
        print(traceback.format_exc())
        raise ValueError(f"エラー: クラス一覧ファイル '{csv_path}' のヘッダー読み込み中に問題が発生しました: {e}")

def load_class_list_data_df(csv_path, encoding, skiprows):
    try:
        df = pd.read_csv(csv_path, encoding='cp932', header=None, skiprows=skiprows, sep=',', quotechar='"', skipinitialspace=True, engine='python')
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"エラー: クラス一覧ファイル '{csv_path}' のデータ部分が見つかりません。")
    except Exception as e:
        raise ValueError(f"エラー: クラス一覧ファイル '{csv_path}' のデータ部分読み込み中に問題が発生しました: {e}")

def load_class_names_list(csv_path, encoding):
    try:
        df = pd.read_csv(csv_path, encoding='cp932', header=None, names=['表示名', 'ファイル名'], engine='python')
        class_info_list = []
        for index, row in df.iterrows():
            display_name = str(row['表示名']).strip()
            filename_base = str(row['ファイル名']).strip()
            if display_name and filename_base:
                class_info_list.append({'name': display_name, 'filename_base': filename_base})
        return class_info_list
    except FileNotFoundError:
        raise FileNotFoundError(f"エラー: クラス名ファイル '{csv_path}' が見つかりません。")
    except Exception as e:
        raise ValueError(f"エラー: クラス名ファイル '{csv_path}' の読み込み中に問題が発生しました: {e}")

def load_teacher_names_list(csv_path, encoding):
    try:
        df = pd.read_csv(csv_path, encoding='cp932', header=None, names=['教師名'], engine='python')
        teacher_names = [str(name).strip() for name in df['教師名'].dropna().unique() if str(name).strip()]
        return teacher_names
    except FileNotFoundError:
        raise FileNotFoundError(f"エラー: 教師名ファイル '{csv_path}' が見つかりません。")
    except Exception as e:
        raise ValueError(f"エラー: 教師名ファイル '{csv_path}' の読み込み中に問題が発生しました: {e}")

