import os
import shutil

def move_and_archive_files(config_data, week_range_str):
    github_pages_output_base_dir = config_data["github_pages_output_base_dir"]
    latest_output_dir = os.path.join(github_pages_output_base_dir, "latest")
    archive_output_dir = os.path.join(github_pages_output_base_dir, week_range_str)
    
    latest_class_dir = os.path.join(latest_output_dir, "class")
    archive_class_dir = os.path.join(archive_output_dir, "class")

    # latest/ ディレクトリが存在し、かつ中にファイルがある場合のみアーカイブ
    if os.path.exists(latest_output_dir) and os.listdir(latest_output_dir):
        # アーカイブディレクトリが存在しない場合は作成
        if not os.path.exists(archive_output_dir):
            os.makedirs(archive_output_dir)
        
        # docs/latest/class/ の内容を docs/YYYY-MM-DD_MM-DD/class/ へ移動
        if os.path.exists(latest_class_dir):
            if not os.path.exists(archive_class_dir):
                os.makedirs(archive_class_dir)
            
            for item_name in os.listdir(latest_class_dir):
                item_path = os.path.join(latest_class_dir, item_name)
                if os.path.isfile(item_path) and item_name.endswith('.html'):
                    destination_path = os.path.join(archive_class_dir, item_name)
                    # ★移動先にファイルが存在する場合、削除してから移動
                    if os.path.exists(destination_path):
                        os.remove(destination_path)
                    shutil.move(item_path, archive_class_dir)
            print(f"古いクラス別時間割を {archive_class_dir} にアーカイブしました。")
        
        # docs/latest/index.html を docs/YYYY-MM-DD_MM-DD/index.html へ移動
        latest_index_html = os.path.join(latest_output_dir, "index.html")
        if os.path.exists(latest_index_html):
            destination_path = os.path.join(archive_output_dir, "index.html")
            # ★移動先にファイルが存在する場合、削除してから移動
            if os.path.exists(destination_path):
                os.remove(destination_path)
            shutil.move(latest_index_html, archive_output_dir)
            print(f"古い目次HTMLを {archive_output_dir} にアーカイブしました。")
        
        # docs/latest/ ディレクトリの中身をクリーンアップ
        for item_name in os.listdir(latest_output_dir):
            item_path = os.path.join(latest_output_dir, item_name)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path) and not os.listdir(item_path):
                os.rmdir(item_path)

    else:
        print("アーカイブする古い時間割はありません。")