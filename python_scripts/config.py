import os
import datetime

def load_config():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    default_week_range_str = f"{start_of_week.strftime('%Y-%m-%d')}_{end_of_week.strftime('%m-%d')}"

    return {
        "project_root": project_root,
        "data_dir": os.path.join(project_root, "data"),
        "templates_dir": os.path.join(project_root, "python_scripts", "templates"),
        "github_pages_output_base_dir": os.path.join(project_root, "docs"),
        "github_pages_base_url": "https://hanzawah.github.io/TimeTableMake/",
        "csv_encoding": "cp932",
        "class_list_csv_filename": "クラス一覧.csv",
        "class_names_csv_filename": "Class_names.csv",
        "teacher_names_csv_filename": "teacher_names.csv",
        "default_week_range_str": default_week_range_str,
        "num_periods_per_day": 6,
        "csv_data_start_col_offset": 1,
    }