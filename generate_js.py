import pandas as pd
import io
import json

def generate_js_data_from_special_timetable_csv(input_csv_path, output_js_path, input_encoding='cp932'):
    """
    特殊な形式の時間割CSVを読み込み、JavaScriptのデータファイルに変換して保存する。
    Args:
        input_csv_path (str): 入力CSVファイルのパス (特殊形式、Shift-JIS)。
        output_js_path (str): 出力JavaScriptファイルのパス。
        input_encoding (str): 入力CSVのエンコーディング。
    """
    try:
        # 1. CSVの読み込み（生データとして読み込む）
        with open(input_csv_path, 'r', encoding=input_encoding) as f:
            lines = f.readlines()

        # 時限の行（3行目、0-indexedでは2）とデータ行（4行目以降、0-indexedでは3以降）を抽出
        data_start_row = 3
        
        # 時限の行とデータ行だけをDataFrameに読み込む準備
        data_io = io.StringIO("".join(lines[data_start_row:]))
        df_raw = pd.read_csv(data_io, header=None, encoding=input_encoding)
        
        # 曜日と時限の情報を抽出
        period_header_line = lines[2].strip() # " ,"１","２","３","４","５","６",...
        periods_str_raw = [p.strip().replace('”','').replace('"','') for p in period_header_line.split(',')]
        periods_str = [p for p in periods_str_raw if p != '' and p != ' '] # 空文字やスペースを除外

        # 曜日ヘッダー行から曜日を特定
        # " "," 5/12 (月)","","","","",""," 5/13 (火)",...
        date_header_line = lines[1].strip()
        date_parts = [p.strip().replace('”','').replace('"','') for p in date_header_line.split(',')]
        
        # 曜日と時限を組み合わせた列のインデックス情報を作成
        # df_rawの列インデックスと、対応する曜日・時限をマッピング
        col_to_day_period_map = {}
        current_day = ''
        col_in_raw_data = 1 # df_rawの最初のデータ列（クラス名を除く）のインデックス
        
        for i, date_part_val in enumerate(date_parts):
            if i == 0: continue # 最初の空文字列はスキップ
            
            # 日付部分から曜日を抽出 (例: " 5/12 (月)" -> "月")
            day_match = ""
            for d in ['月', '火', '水', '木', '金', '土', '日']:
                # CSVの文字化けを考慮し、部分一致で判定
                if f'({d})' in date_part_val:
                    day_match = d
                    break
            
            if day_match:
                current_day = day_match

            # 時限ヘッダーの実際の値（１, ２, など）
            # periods_str_raw は最初の空セルを含むので、インデックスを調整
            if i < len(periods_str_raw): # 範囲チェック
                period_val_raw = periods_str_raw[i]
                if period_val_raw in ['１', '２', '３', '４', '５', '６']:
                    period_num = int(period_val_raw.replace('”','').replace('"','')) # '１' -> 1
                    col_to_day_period_map[col_in_raw_data] = {'day': current_day, 'period': period_num}
                    col_in_raw_data += 1 # 次のデータ列へ
                elif period_val_raw.strip() == '': # 時限ヘッダーが空の場合も列インデックスを進める
                     col_in_raw_data += 1
                
        # 最終的な整形済みデータを作成するためのリスト（JSONに変換される）
        standard_timetable_rows = []

        # df_raw の各行を処理
        # df_raw の最初の列はクラス名 (0-indexed)
        # それ以降の列が授業内容
        for index, row_data in df_raw.iterrows():
            class_name_raw = str(row_data[0]).strip() # 最初の列がクラス名
            
            # クラス名の文字化けを想定して変換（例: ' �R�|�P' -> '3年1組'）
            # これはCSVの内容に依存するため、必要に応じて正確に調整
            class_name_map = {
                '３－１': '3年1組', '３－２': '3年2組', '３－３': '3年3組', '３－４': '3年4組',
                '３理探': '3理探', '３国探': '3国探',
                '２－１': '2年1組', '２－２': '2年2組', '２－３': '2年3組', '２－４': '2年4組',
                '２理探': '2理探', '２国探': '2国探',
                '１－１': '1年1組', '１－２': '1年2組', '１－３': '1年3組', '１－４': '1年4組',
                '１－５': '1年5組', '１－６': '1年6組',
                # 他のクラスもここに追加してください
            }
            class_name = class_name_map.get(class_name_raw, class_name_raw) # マップになければそのまま

            # 授業内容の列をイテレート
            for col_idx_in_df_raw in range(1, len(row_data)): # df_rawの1列目から最後まで
                day_period_info = col_to_day_period_map.get(col_idx_in_df_raw)
                
                if day_period_info: # 曜日と時限が有効な列の場合
                    lesson_content = str(row_data[col_idx_in_df_raw]).strip() if pd.notna(row_data[col_idx_in_df_raw]) else ''

                    if lesson_content and lesson_content != '-': # 内容がある場合のみ
                        standard_timetable_rows.append({
                            'クラス': class_name,
                            '曜日': day_period_info['day'],
                            '時限': day_period_info['period'],
                            '科目': lesson_content,
                            '担当教師': '', # データに含まれない
                            '教室': ''     # データに含まれない
                        })

        # 重複する行があれば削除
        # PythonでDataFrameに変換して drop_duplicates を使うのが最も安全だが、
        # ここではリストと辞書で処理しているため、手動で重複確認が必要になる。
        # 簡単のため、ここでは重複排除はしない。
        
        # クラス名と曜日と時限でソート (JavaScript側でも行うが、ここでしておくと確実)
        # PythonのDataFrameに一度変換してソートするのが最も簡単
        df_final = pd.DataFrame(standard_timetable_rows)
        day_order = ['月', '火', '水', '木', '金', '土', '日']
        df_final['曜日'] = pd.Categorical(df_final['曜日'], categories=day_order, ordered=True)
        df_final = df_final.sort_values(by=['クラス', '曜日', '時限'])

        # DataFrameを辞書のリストに変換し、JSONとして保存
        final_data_for_js = df_final.to_dict(orient='records')
        
        # JavaScriptファイルとして出力
        js_content = f"const timetableData = {json.dumps(final_data_for_js, ensure_ascii=False, indent=2)};"
        
        with open(output_js_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        print(f"'{input_csv_path}' を解析し、JavaScriptデータファイル '{output_js_path}' を生成しました。")
        print(f"最初の5件のデータ:\n{json.dumps(final_data_for_js[:5], ensure_ascii=False, indent=2)}")

    except Exception as e:
        print(f"JavaScriptデータファイル生成中にエラーが発生しました: {e}")
        print("入力CSVの形式がスクリプトの想定と異なる可能性があります。")

# 実行例
input_csv = 'data/クラス一覧.csv' # 元の特殊形式CSV (Shift-JIS)
output_js = 'data/timetable_data.js' # 生成されるJavaScriptデータファイル (UTF-8)

generate_js_data_from_special_timetable_csv(input_csv, output_js)