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

            header_dates_encoded_row = rows[1][1:]
            header_dates_decoded = [utils.decode_sjis(s).strip() for s in header_dates_encoded_row if s.strip() or s == '""'] 
            
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
                week_range_str = utils.get_week_range_string(first_date_obj)
                print(f"CSVヘッダーから週の範囲を特定しました: {week_range_str}")
            else:
                print(f"警告: CSVヘッダーから有効な日付を特定できませんでした。今週の範囲 ({week_range_str}) で生成します。")

            header_periods_raw_row = rows[2][1:]
            header_periods_decoded = [utils.decode_sjis(s).strip() for s in header_periods_raw_row if s.strip() or s == '""'] 
            
            unique_periods = sorted(list(set([s.replace('１','1').replace('２','2').replace('３','3').replace('４','4').replace('５','5').replace('６','6') for s in header_periods_decoded if s])))
            
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

            print(f"CSVヘッダーから抽出した時限: {unique_periods}")
            print(f"列インデックスマッピング: {header_day_columns_map}")
            
            return {
                "week_range_str": week_range_str, 
                "unique_periods": unique_periods, 
                "header_day_columns_map": header_day_columns_map
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
    """
    Class_names.csv からクラス名とファイル名のマッピングを読み込みます。
    このファイルはヘッダーなし、2列 (表示名, ファイル名拡張子なし) を想定。
    例: "3年1組,C31"
    """
    try:
        df = pd.read_csv(csv_path, encoding=encoding, header=None, names=['表示名', 'ファイル名'], engine='python')
        
        class_info_list = []
        for index, row in df.iterrows():
            display_name = row['表示名'].strip()
            filename_base = row['ファイル名'].strip()
            if display_name and filename_base:
                class_info_list.append({'name': display_name, 'filename_base': filename_base})
        
        return sorted(class_info_list, key=lambda x: x['name'])
    except FileNotFoundError:
        raise FileNotFoundError(f"エラー: クラス名ファイル '{csv_path}' が見つかりません。")
    except Exception as e:
        raise ValueError(f"エラー: クラス名ファイル '{csv_path}' の読み込み中に問題が発生しました: {e}. CSVファイルのエンコーディングや形式を確認してください。")

def load_teacher_names_list(csv_path, encoding):
    try:
        df = pd.read_csv(csv_path, encoding=encoding, header=None, names=['教師名'], engine='python')
        return sorted(df['教師名'].dropna().unique().tolist())
    except FileNotFoundError:
        raise FileNotFoundError(f"エラー: 教師名ファイル '{csv_path}' が見つかりません。")
    except Exception as e:
        raise ValueError(f"エラー: 教師名ファイル '{csv_path}' の読み込み中に問題が発生しました: {e}. CSVファイルのエンコーディングや形式を確認してください。")