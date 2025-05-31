import pandas as pd
import csv
import re
import datetime
from python_scripts import utils

def parse_class_list_header(csv_path, encoding, csv_data_start_col_offset, num_periods_per_day_config):
    week_range_str = utils.get_week_range_string(datetime.date.today())
    header_dates_decoded = []
    unique_periods = []
    header_day_columns_map = {}

    try:
        with open(csv_path, 'r', encoding=encoding, newline='') as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            rows = list(reader)
            
            if len(rows) < 3:
                raise ValueError(f"CSVファイル '{csv_path}' は少なくとも3行のヘッダーが必要です。")

            # --- CSV 2行目から日付情報を正確に抽出 ---
            # CSV 2行目(index 1)の全データ
            header_dates_full_row_encoded = rows[1] 
            
            # 各曜日の日付が格納されている列のインデックスを特定
            # CSVのデータ構造に合わせて、1列目(インデックス0)は空白のためスキップし、
            # その後 num_periods_per_day_config (6) 列ごとに日付が入る
            # 例: CSV列インデックス: 1, 8, 15, 22, 29 (6時限+空白1で7列ごと)
            
            # 抽出したい日付のCSV列インデックス (Pythonのリストインデックス+1)
            # CSVの2行目データ例: " "," 5/12 (月)","","","","",""," 5/13 (火)",...
            # Pythonリストのインデックスとしては [1], [8], [15], [22], [29]
            date_col_indices_in_row = [1 + (i * (num_periods_per_day_config + 1)) for i in range(5)] # 月～金 5日分
            
            for col_idx in date_col_indices_in_row:
                if col_idx < len(header_dates_full_row_encoded):
                    s_encoded = header_dates_full_row_encoded[col_idx]
                    s_decoded = utils.decode_sjis(s_encoded).strip()
                    # 日付パターンにマッチするものだけを header_dates_decoded に追加 (必須)
                    if re.search(r'\d{1,2}/\d{1,2}\s*\(.+\)', s_decoded): 
                        header_dates_decoded.append(s_decoded)
                    else:
                        # 日付パターンに合致しない場合、空のまま追加 (ヘッダーの列数を維持するため)
                        header_dates_decoded.append("-") # または空文字列 ""

            # 最初の有効な日付から週の範囲を特定 (ロジック変更なし)
            first_valid_date_str = None
            for date_entry in header_dates_decoded:
                if date_entry and date_entry != "-": 
                    first_date_str_match = re.search(r'(\d{1,2}/\d{1,2})', date_entry)
                    if first_date_str_match:
                        first_date_str = first_date_str_match.group(1)
                        break
            
            if first_date_str:
                current_year = datetime.date.today().year
                first_date_obj = datetime.datetime.strptime(f"{current_year}/{first_date_str}", "%Y/%m/%d").date()
                week_range_str = utils.get_week_range_string(first_date_obj)
                print(f"CSVヘッダーから週の範囲を特定しました: {week_range_str}")
            else:
                print(f"警告: CSVヘッダーから有効な日付を特定できませんでした。今週の範囲 ({week_range_str}) で生成します。")

            # --- 時限はコンフィグから固定値として取得 ---
            unique_periods = [str(i) for i in range(1, num_periods_per_day_config + 1)] # 例: ['1', '2', '3', '4', '5', '6']
            
            # --- 列インデックスマッピングは固定の曜日で生成 ---
            header_day_columns_map = {}
            days_of_week_long = ["月", "火", "水", "木", "金"] 
            
            current_col_idx_in_csv = csv_data_start_col_offset
            num_periods_per_day = num_periods_per_day_config
            
            for day in days_of_week_long:
                day_indices = []
                for _ in range(num_periods_per_day):
                    day_indices.append(current_col_idx_in_csv)
                    current_col_idx_in_csv += 1
                header_day_columns_map[day] = day_indices

            print(f"時限数制約に基づいて生成した時限: {unique_periods}")
            print(f"列インデックスマッピング: {header_day_columns_map}")
            
            return {
                "week_range_str": week_range_str, 
                "unique_periods": unique_periods, 
                "header_day_columns_map": header_day_columns_map,
                "header_dates_decoded": header_dates_decoded 
            }

    except FileNotFoundError:
        raise FileNotFoundError(f"エラー: クラス一覧ファイル '{csv_path}' が見つかりません。")
    except Exception as e:
        raise ValueError(f"エラー: クラス一覧ファイル '{csv_path}' のヘッダー読み込み中に問題が発生しました: {e}. CSVファイルのエンコーディングや形式を確認してください。")

def load_class_list_data_df(csv_path, encoding, skiprows):
    try:
        df = pd.read_csv(csv_path, encoding=encoding, header=None, skiprows=skiprows, sep=',', quotechar='"', skipinitialspace=True, engine='python')
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"エラー: クラス一覧ファイル '{csv_path}' のデータ部分が見つかりません。")
    except Exception as e:
        raise ValueError(f"エラー: クラス一覧ファイル '{csv_path}' のデータ部分読み込み中に問題が発生しました: {e}. CSVファイルのエンコーディングや形式を確認してください。")

def load_class_names_list(csv_path, encoding):
    try:
        df = pd.read_csv(csv_path, encoding=encoding, header=None, names=['表示名', 'ファイル名'], engine='python')
        
        class_info_list = []
        for index, row in df.iterrows():
            display_name = row['表示名'].strip()
            filename_base = row['ファイル名'].strip()
            if display_name and filename_base:
                class_info_list.append({'name': display_name, 'filename_base': filename_base})
        
        return class_info_list
    except FileNotFoundError:
        raise FileNotFoundError(f"エラー: クラス名ファイル '{csv_path}' が見つかりません。")
    except Exception as e:
        raise ValueError(f"エラー: クラス名ファイル '{csv_path}' の読み込み中に問題が発生しました: {e}. CSVファイルのエンコーディングや形式を確認してください。")

def load_teacher_names_list(csv_path, encoding):
    try:
        df = pd.read_csv(csv_path, encoding=encoding, header=None, names=['教師名'], engine='python')
        return df['教師名'].dropna().unique().tolist()
    except FileNotFoundError:
        raise FileNotFoundError(f"エラー: 教師名ファイル '{csv_path}' が見つかりません。")
    except Exception as e:
        raise ValueError(f"エラー: 教師名ファイル '{csv_path}' の読み込み中に問題が発生しました: {e}. CSVファイルのエンコーディングや形式を確認してください。")