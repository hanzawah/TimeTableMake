import os
import sys
import datetime 

from python_scripts import config
from python_scripts import data_parser
from python_scripts import html_generator
from python_scripts import file_manager

def main():
    cfg = config.load_config()

    try:
        parsed_header_info = data_parser.parse_class_list_header(
            os.path.join(cfg["data_dir"], cfg["class_list_csv_filename"]), 
            cfg["csv_encoding"],
            cfg["csv_data_start_col_offset"], 
            cfg["num_periods_per_day"]
        )
        
        class_list_data_df = data_parser.load_class_list_data_df(
            os.path.join(cfg["data_dir"], cfg["class_list_csv_filename"]), 
            cfg["csv_encoding"], 
            skiprows=3
        )

        master_class_info_list = data_parser.load_class_names_list(
            os.path.join(cfg["data_dir"], cfg["class_names_csv_filename"]), cfg["csv_encoding"]
        )

    except (FileNotFoundError, ValueError) as e:
        print(f"エラー: データの読み込み中に問題が発生しました: {e}")
        sys.exit(1)

    file_manager.move_and_archive_files(cfg, parsed_header_info["week_range_str"])

    html_generator.generate_all_htmls(cfg, parsed_header_info, class_list_data_df, master_class_info_list)

    print("すべての処理が完了しました！")

if __name__ == "__main__":
    if not os.environ.get('VIRTUAL_ENV'):
        print("警告: 仮想環境が有効化されていません。")
        print("スクリプトを実行する前に `.venv\\Scripts\\Activate.ps1` を実行してください。")
        sys.exit(1)
    
    main()