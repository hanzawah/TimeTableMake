# python_scripts/config.py
import os
import datetime

def load_config():
    # プロジェクトルートのパスを取得 (python_scripts/config.py から見て2つ上のディレクトリ)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 週の開始日と終了日を計算 (今日の日付でデフォルト値を設定)
    # これは初期設定用で、CSVから週を特定するロジックは data_parser.py に持たせる
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    default_week_range_str = f"{start_of_week.strftime('%Y-%m-%d')}_{end_of_week.strftime('%m-%d')}"

    return {
        "project_root": project_root,
        "data_dir": os.path.join(project_root, "data"), # data/ フォルダのパス
        "templates_dir": os.path.join(project_root, "python_scripts", "templates"), # テンプレートフォルダのパス
        "github_pages_output_base_dir": os.path.join(project_root, "docs"), # docs/ フォルダのパス
        "github_pages_base_url": "https://hanzawah.github.io/TimeTableMake/", # ★あなたのGitHub Pages URLに置き換え済み！
        "csv_encoding": "cp932", # CSVファイルのエンコーディング（もしUTF-8なら'utf-8'に変更）
        "class_list_csv_filename": "クラス一覧.csv", # 時間割データ本体のCSVファイル名
        "class_names_csv_filename": "Class_names.csv", # クラス名リストのCSVファイル名
        "teacher_names_csv_filename": "teacher_names.csv", # 教師名リストのCSVファイル名
        "default_week_range_str": default_week_range_str, # デフォルトの週の範囲文字列
        "num_periods_per_day": 6, # 1日あたりの時限数（CSVフォーマットから判断）
        "csv_data_start_col_offset": 7, # CSVで時間割データが始まる列のインデックス（クラス名1 + 空白6）
    }