import datetime

def get_week_range_string(date=None):
    if date is None:
        date = datetime.date.today()
    start_of_week = date - datetime.timedelta(days=date.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    return f"{start_of_week.strftime('%Y-%m-%d')}_{end_of_week.strftime('%m-%d')}"

def decode_sjis(s):
    """
    この関数はShift_JISデコードを行いません。
    ファイルの読み込み時にエンコーディングを指定する方法に変更したため、
    この関数は単純に受け取った値を文字列として返すだけにします。
    """
    return str(s)