import datetime

def get_week_range_string(date=None):
    if date is None:
        date = datetime.date.today()
    start_of_week = date - datetime.timedelta(days=date.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    return f"{start_of_week.strftime('%Y-%m-%d')}_{end_of_week.strftime('%m-%d')}"

def decode_sjis(s):
    if isinstance(s, str):
        try:
            return s.encode('latin1').decode('cp932')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s 
    return str(s)