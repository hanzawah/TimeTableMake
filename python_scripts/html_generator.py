import os
from jinja2 import Environment, FileSystemLoader
import pandas as pd
from python_scripts import utils

def create_jinja2_env(templates_dir):
    return Environment(loader=FileSystemLoader(templates_dir))

def generate_timetable_table_html_from_class_csv(class_row, header_periods, header_day_columns_map, header_dates_decoded):
    class_name = utils.decode_sjis(class_row.iloc[0]).strip()

    html_table = f"<h3>{class_name}の時間割詳細</h3>"
    html_table += "<table border='1' style='width:100%; border-collapse: collapse; text-align: center;'>"
    
    # ここを修正：曜日のリストではなく、読み取った日付ヘッダーを使う
    days_to_display_in_header = header_dates_decoded[:5] 

    html_table += "<thead><tr><th>時限</th>"
    for date_str in days_to_display_in_header:
        html_table += f"<th>{date_str}</th>"
    html_table += "</tr></thead>"
    
    html_table += "<tbody>"
    
    fixed_days_of_week_for_data_lookup = ["月", "火", "水", "木", "金"]

    for period in sorted(header_periods):
        html_table += f"<tr><td>{period}</td>"
        
        for day in fixed_days_of_week_for_data_lookup:
            lesson = "-" 
            if day in header_day_columns_map: 
                period_idx_in_day_list = header_periods.index(period) if period in header_periods else -1
                
                if period_idx_in_day_list != -1:
                    col_index_in_csv = header_day_columns_map[day][period_idx_in_day_list]
                    
                    if col_index_in_csv < len(class_row): 
                        lesson_encoded = class_row.iloc[col_index_in_csv]
                        
                        if pd.isna(lesson_encoded) or str(lesson_encoded).strip() == "":
                            lesson = "-" 
                        else:
                            lesson = utils.decode_sjis(lesson_encoded).strip()
                    else:
                        lesson = "-" 
                else:
                    lesson = "-"
            html_table += f"<td>{lesson}</td>"
        html_table += "</tr>"
        
    html_table += "</tbody></table>"
    return html_table

def generate_all_htmls(config_data, parsed_header_info, class_list_data_df, master_class_info_list):
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

    index_template = env.get_template('index_template.html')
    class_links_for_index = []
    
    for class_info in master_class_info_list:
        display_name = class_info['name']
        filename_base = class_info['filename_base']
        filename = f"{filename_base}.html"
        class_links_for_index.append({"name": display_name, "filename": filename})

    index_html_content = index_template.render(
        week_range=week_range_str,
        class_list=class_links_for_index,
        github_pages_base_url=config_data["github_pages_base_url"]
    )
    with open(os.path.join(latest_output_dir, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html_content)
    print(f"目次HTMLを {os.path.join(latest_output_dir, 'index.html')} に生成しました。")

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
        
        csv_class_name_in_row_decoded = utils.decode_sjis(class_row_data.iloc[0]).strip()
        if csv_class_name_in_row_decoded != class_name_display:
            print(f"警告: Class_names.csv の表示名と クラス一覧.csv のデータ行のクラス名が異なります。")
            print(f"    Class_names.csvからのクラス名: '{class_name_display}'")
            print(f"    クラス一覧.csvからのデータ行: '{csv_class_name_in_row_decoded}'")
            print(f"    このHTMLは'{class_name_display}'のファイル名で、'{csv_class_name_in_row_decoded}'の時間割データを含みます。")

        timetable_table_html = generate_timetable_table_html_from_class_csv(
            class_row_data, unique_periods, header_day_columns_map, header_dates_decoded # ★ここも変更：header_dates_decoded を渡す
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