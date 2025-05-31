import os
import shutil
import datetime
from jinja2 import Environment, FileSystemLoader

# --- 設定 ---
# プロジェクトルートからの相対パス
DATA_DIR = "data"
SRC_DIR = "src"
TEMPLATES_DIR = os.path.join(SRC_DIR, "templates")
INTERNAL_OUTPUT_BASE_DIR = "output_for_internal_server" # 学内サーバー用HTMLの出力元
GITHUB_PAGES_BASE_URL = "https://hanzawah.github.io/TimeTableMake/" # ★あなたのGitHub Pages URLに！
# ★あなたの学内サーバーのURLに！最後の /timetable/ は学内サーバーでの時間割ページのルートパス
INTERNAL_SERVER_BASE_URL = "http://YOUR_INTERNAL_SERVER_URL/timetable/"

# Jinja2 環境設定
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def get_week_range_string(date=None):
    if date is None:
        date = datetime.date.today()

    # 月曜日を開始日とする (weekday()は月曜が0、日曜が6)
    start_of_week = date - datetime.timedelta(days=date.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)

    # フォルダ名形式 (例: 2025-06-02_06-08)
    return f"{start_of_week.strftime('%Y-%m-%d')}_{end_of_week.strftime('%m-%d')}"

def generate_all_htmls():
    current_date = datetime.date.today() # 今日の日付
    week_range_str = get_week_range_string(current_date)

    # 学内サーバー用出力ディレクトリ (例: output_for_internal_server/latest/)
    latest_output_dir = os.path.join(INTERNAL_OUTPUT_BASE_DIR, "latest")
    # 週次アーカイブディレクトリ (例: output_for_internal_server/2025-06-02_06-08/)
    archive_output_dir = os.path.join(INTERNAL_OUTPUT_BASE_DIR, week_range_str)

    # --- 1. 古い latest/ の内容をアーカイブディレクトリへ移動 ---
    if os.path.exists(latest_output_dir) and os.listdir(latest_output_dir):
        if not os.path.exists(archive_output_dir):
            os.makedirs(archive_output_dir)

        # latest の中身を丸ごと archive_output_dir へ移動
        # 移動元は latest/ 内のファイル群
        for item in os.listdir(latest_output_dir):
            shutil.move(os.path.join(latest_output_dir, item), archive_output_dir)
        print(f"古い時間割を {archive_output_dir} にアーカイブしました。")
    else:
        print("アーカイブする古い時間割はありません。")

    # --- 2. output_for_internal_server/latest/ ディレクトリを準備 ---
    if not os.path.exists(latest_output_dir):
        os.makedirs(latest_output_dir)

    # --- 3. 時間割データを読み込む (ダミーデータとして) ---
    # 実際には data/ のCSVなどを読み込むロジックをここに実装
    # 例: pandas で CSV を読み込む
    # import pandas as pd
    # class_list_df = pd.read_csv(os.path.join(DATA_DIR, "クラス一覧.csv"))
    # timetable_df = pd.read_csv(os.path.join(DATA_DIR, "時間割.csv"))

    # ここではダミーデータで進めます
    class_names = ["1年A組", "1年B組", "2年A組", "3年A組"]
    dummy_timetable_data = {
        "1年A組": "<table><tr><th>月</th><td>国語</td><td>数学</td></tr></table>",
        "1年B組": "<table><tr><th>月</th><td>理科</td><td>社会</td></tr></table>",
        # ... 他のクラスの時間割データ（HTML形式）
    }

    # --- 4. 目次HTML (index.html) を生成 ---
    index_template = env.get_template('index_template.html')
    class_links_for_index = []
    for name in class_names:
        filename = f"class_{name.replace(' ', '_').replace('組', '')}.html" # ファイル名に変換 (例: class_1年A.html)
        class_links_for_index.append({"name": name, "filename": filename})

    index_html_content = index_template.render(
        week_range=week_range_str,
        class_list=class_links_for_index
    )
    with open(os.path.join(latest_output_dir, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html_content)
    print(f"目次HTMLを {os.path.join(latest_output_dir, 'index.html')} に生成しました。")

    # --- 5. 各クラスのHTMLを生成 ---
    class_template = env.get_template('class_template.html')
    for class_name, timetable_html in dummy_timetable_data.items():
        filename = f"class_{class_name.replace(' ', '_').replace('組', '')}.html"
        class_html_content = class_template.render(
            week_range=week_range_str,
            class_name=class_name,
            timetable_table_html=timetable_html # HTML文字列をそのまま渡す
        )
        with open(os.path.join(latest_output_dir, filename), 'w', encoding='utf-8') as f:
            f.write(class_html_content)
        print(f"{class_name} の時間割HTMLを {os.path.join(latest_output_dir, filename)} に生成しました。")

    print("すべての時間割HTMLの生成が完了しました！")


if __name__ == "__main__":
    generate_all_htmls()