import os
import re
from jinja2 import Environment, FileSystemLoader
import pandas as pd

def create_jinja2_env(templates_dir):
    """Jinja2の環境をセットアップする"""
    # このスクリプト(html_generator.py)の場所を基準にtemplatesディレクトリのパスを解決
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return Environment(loader=FileSystemLoader(os.path.join(base_dir, templates_dir)))

def generate_timetable_table_html_from_class_csv(env, class_row, header_periods, header_day_columns_map, header_dates_decoded):
    """
    クラスの1行データから時間割テーブルのHTMLを生成する。
    授業を前方に詰めて表示するロジックを実装。
    """
    class_name = str(class_row.iloc[0]).strip() # クラス名を取得
    day_headers = header_dates_decoded[:5]      # 表示する曜日のヘッダー（月～金）
    days_of_week = ["月", "火", "水", "木", "金"] # 処理対象の曜日
    num_periods = len(header_periods)           # 1日の時限数

    # 1. 曜日ごとに、CSVに記載のままの授業データを抽出する
    raw_daily_lessons = {}
    for day_char in days_of_week:
        lessons_for_day = []
        if day_char in header_day_columns_map:
            for col_index_in_csv in header_day_columns_map[day_char]:
                lesson = "" # デフォルトは空文字列（授業なしを示す）
                if col_index_in_csv < len(class_row): # CSVの列範囲内か確認
                    lesson_val = class_row.iloc[col_index_in_csv]
                    # NaNでなく、かつ空白除去後に何かしら文字が残る場合のみ授業名として採用
                    if pd.notna(lesson_val) and str(lesson_val).strip():
                        lesson = str(lesson_val).strip()
                lessons_for_day.append(lesson)
        else: # マップに曜日が存在しない場合（通常はありえないが念のため）
            lessons_for_day = [""] * num_periods
        raw_daily_lessons[day_char] = lessons_for_day
    
    # 2. 曜日ごとに授業を前方に「詰める」処理を行う
    compacted_daily_lessons = {}
    for day_char in days_of_week:
        # 空文字列でない授業だけを抽出
        actual_lessons = [lesson for lesson in raw_daily_lessons.get(day_char, []) if lesson]
        
        # 新しいリストを作成し、抽出した授業を前から配置
        compacted_list = actual_lessons[:] # スライスでリストをコピー
        
        # 1日の時限数に満たない部分をハイフンで埋める
        while len(compacted_list) < num_periods:
            compacted_list.append("-")
        
        compacted_daily_lessons[day_char] = compacted_list[:num_periods] # 念のため時限数でスライス

    # 3. Jinja2テンプレート用に、時限ごとのデータ構造に変換（テーブルの転置）
    timetable_data = {}
    # header_periods (['1', '2', ...]) を元に、正しい順序で時限データを構築
    for i, period_str in enumerate(sorted(header_periods, key=int)): # 時限を数値としてソートしてループ
        lessons_for_period = []
        for day_char in days_of_week:
            # compacted_daily_lessonsから該当曜日のi番目の授業を取得
            # もし該当曜日のデータがないか、時限が不足している場合は"-"を追加
            day_lessons = compacted_daily_lessons.get(day_char)
            if day_lessons and i < len(day_lessons):
                lessons_for_period.append(day_lessons[i])
            else:
                lessons_for_period.append("-") # データ不足時のフォールバック
        timetable_data[period_str] = lessons_for_period

    # 4. テンプレートをレンダリングしてHTMLを返す
    table_template = env.get_template('timetable_table.html')
    return table_template.render(
        class_name=class_name,
        day_headers=day_headers,
        timetable_data=timetable_data # 時限をキーとした辞書
    )

def generate_all_htmls(config_data, parsed_header_info, class_list_data_df, master_class_info_list):
    """すべてのクラスのHTMLファイルと目次ページを生成する"""
    # templates_dir は config_data から取得する想定
    # create_jinja2_env に渡すパスは、このファイル(html_generator.py)からの相対パスではなく、
    # プロジェクトルートからの相対パスか、絶対パスであるべき。
    # ここでは、config_data["templates_dir"] が 'python_scripts/templates' のような
    # プロジェクトルートからの相対パスであることを期待する。
    # もし、html_generator.py と同じ階層に templates があるなら、'templates'だけで良い。
    # 状況に応じて env の初期化方法を調整してください。
    # 例: env = create_jinja2_env(os.path.join(os.path.dirname(__file__), 'templates'))
    env = create_jinja2_env(config_data.get("templates_dir", "python_scripts/templates"))
    
    week_range_str = parsed_header_info["week_range_str"]
    unique_periods = parsed_header_info["unique_periods"] # ['1', '2', '3', '4', '5', '6']など
    header_day_columns_map = parsed_header_info["header_day_columns_map"]
    header_dates_decoded = parsed_header_info["header_dates_decoded"] 

    github_pages_output_base_dir = config_data["github_pages_output_base_dir"]
    latest_output_dir = os.path.join(github_pages_output_base_dir, "latest")
    
    latest_class_dir = os.path.join(latest_output_dir, "class")
    if not os.path.exists(latest_class_dir):
        os.makedirs(latest_class_dir, exist_ok=True)

    # --- 目次ページの生成 ---
    index_template = env.get_template('index_template.html')
    class_links_for_index = []
    
    for class_info in master_class_info_list:
        display_name = class_info['name']
        filename_base = class_info['filename_base']
        filename_html = f"{filename_base}.html"
        
        # ★★★ index_template.html の href="./class/{{ class_info.filename }}" に合わせる ★★★
        class_links_for_index.append({
            "name": display_name, 
            "filename": filename_html # 'C11.html' など、ファイル名のみ
        })

    index_html_content = index_template.render(
        week_range=week_range_str,
        class_list=class_links_for_index,
        github_pages_base_url=config_data["github_pages_base_url"]
    )
    index_html_path = os.path.join(latest_output_dir, "index.html")
    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(index_html_content)
    print(f"目次HTMLを {index_html_path} に生成しました。")

    # --- 各クラスの時間割ページの生成 ---
    class_template = env.get_template('class_template.html')
    
    for i, master_class_entry in enumerate(master_class_info_list):
        class_name_display = master_class_entry['name']
        filename_base = master_class_entry['filename_base']
        filename_html = f"{filename_base}.html"
        class_html_path = os.path.join(latest_class_dir, filename_html)

        if i < len(class_list_data_df):
            class_row_data = class_list_data_df.iloc[i]
        else:
            print(f"警告: Class_names.csv のクラス数 ({len(master_class_info_list)}) が クラス一覧.csv のデータ行数 ({len(class_list_data_df)}) を超えました。'{class_name_display}' の時間割生成をスキップします。")
            continue
        
        # CSV内のクラス名とマスターリストのクラス名比較の警告 (必要に応じてロジックを調整)
        csv_class_name_in_row = str(class_row_data.iloc[0]).strip()
        # master_class_entry に 'internal_name' があればそれと比較、なければ表示名と比較
        # この比較ロジックは、class_names.csv の内容とクラス一覧.csv のクラス名の書式に依存
        expected_csv_name = master_class_entry.get('internal_name', class_name_display)
        normalized_csv_name = re.sub(r'[-－]', '-', csv_class_name_in_row) # ハイフン正規化
        normalized_master_name = re.sub(r'[-－]', '-', expected_csv_name)

        if normalized_csv_name != normalized_master_name:
            print(f"警告: クラス名不一致の可能性: 表示名='{class_name_display}', CSV名='{csv_class_name_in_row}'")

        timetable_table_html = generate_timetable_table_html_from_class_csv(
            env,
            class_row_data, 
            unique_periods, 
            header_day_columns_map, 
            header_dates_decoded
        )

        class_html_content = class_template.render(
            week_range=week_range_str,
            class_name=class_name_display,
            timetable_table_html=timetable_table_html,
            github_pages_base_url=config_data["github_pages_base_url"]
        )
        with open(class_html_path, 'w', encoding='utf-8') as f:
            f.write(class_html_content)
        print(f"{class_name_display} の時間割HTMLを {class_html_path} に生成しました。")

    print("すべての時間割HTMLの生成が完了しました！")

