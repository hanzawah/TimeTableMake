import os
import re
from jinja2 import Environment, FileSystemLoader
import pandas as pd

def create_jinja2_env(templates_dir):
    """Jinja2の環境をセットアップする"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return Environment(loader=FileSystemLoader(os.path.join(base_dir, 'templates')))

def generate_timetable_table_html_from_class_csv(env, class_row, header_periods, header_day_columns_map, header_dates_decoded):
    """
    クラスの1行データから時間割テーブルのHTMLを生成する。
    授業を前方に詰めて表示するロジックを実装。
    """
    class_name = str(class_row.iloc[0]).strip()
    day_headers = header_dates_decoded[:5]
    days_of_week = ["月", "火", "水", "木", "金"]
    num_periods = len(header_periods)

    # 1. 曜日ごとに、CSVに記載のままの授業データを抽出する
    raw_daily_lessons = {}
    for day_char in days_of_week:
        lessons_for_day = []
        if day_char in header_day_columns_map:
            for col_index_in_csv in header_day_columns_map[day_char]:
                lesson = "" # デフォルトは空文字列
                if col_index_in_csv < len(class_row):
                    lesson_val = class_row.iloc[col_index_in_csv]
                    if pd.notna(lesson_val) and str(lesson_val).strip():
                        lesson = str(lesson_val).strip()
                lessons_for_day.append(lesson)
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
        
        compacted_daily_lessons[day_char] = compacted_list

    # 3. Jinja2テンプレート用に、時限ごとのデータ構造に変換（テーブルの転置）
    timetable_data = {}
    # header_periodsを['1', '2', ...]の順でループさせるため、intに変換してソート
    for i, period_str in enumerate(sorted(header_periods, key=int)):
        lessons_for_period = []
        for day_char in days_of_week:
            lessons_for_period.append(compacted_daily_lessons.get(day_char, ["-"]*num_periods)[i])
        timetable_data[period_str] = lessons_for_period

    # 4. テンプレートをレンダリングしてHTMLを返す
    table_template = env.get_template('timetable_table.html')
    return table_template.render(
        class_name=class_name,
        day_headers=day_headers,
        timetable_data=timetable_data
    )

def generate_all_htmls(config_data, parsed_header_info, class_list_data_df, master_class_info_list):
    """すべてのクラスのHTMLファイルと目次ページを生成する"""
    env = create_jinja2_env(config_data["templates_dir"])
    
    week_range_str = parsed_header_info["week_range_str"]
    unique_periods = parsed_header_info["unique_periods"]
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
        filename = f"{filename_base}.html"
        class_links_for_index.append({"name": display_name, "link": f"class/{filename}"})

    index_html_content = index_template.render(
        week_range=week_range_str,
        class_list=class_links_for_index,
        github_pages_base_url=config_data["github_pages_base_url"]
    )
    with open(os.path.join(latest_output_dir, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html_content)
    print(f"目次HTMLを {os.path.join(latest_output_dir, 'index.html')} に生成しました。")

    # --- 各クラスの時間割ページの生成 ---
    class_template = env.get_template('class_template.html')
    
    for i, master_class_entry in enumerate(master_class_info_list):
        class_name_display = master_class_entry['name']
        filename_base = master_class_entry['filename_base']
        filename = f"{filename_base}.html"

        if i < len(class_list_data_df):
            class_row_data = class_list_data_df.iloc[i]
        else:
            print(f"警告: Class_names.csv のクラス数 ({len(master_class_info_list)}) が クラス一覧.csv のデータ行数 ({len(class_list_data_df)}) を超えました。'{class_name_display}' の時間割生成をスキップします。")
            continue
        
        csv_class_name_in_row = str(class_row_data.iloc[0]).strip()
        if csv_class_name_in_row != master_class_entry.get('internal_name', class_name_display): # 内部名があればそちらと比較
             # 全角・半角の違いなどを吸収する正規化処理
             normalized_csv_name = re.sub(r'[-－]', '-', csv_class_name_in_row)
             normalized_master_name = re.sub(r'[-－]', '-', class_name_display)
             if normalized_csv_name != normalized_master_name:
                 print(f"警告: Class_names.csv の表示名と クラス一覧.csv のデータ行のクラス名が異なります。")
                 print(f"     表示名: '{class_name_display}', CSV内の名前: '{csv_class_name_in_row}'")

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
        with open(os.path.join(latest_class_dir, filename), 'w', encoding='utf-8') as f:
            f.write(class_html_content)
        print(f"{class_name_display} の時間割HTMLを {os.path.join(latest_class_dir, filename)} に生成しました。")

    print("すべての時間割HTMLの生成が完了しました！")