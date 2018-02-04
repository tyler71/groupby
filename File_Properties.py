import datetime

def modification_date(filename: str) -> datetime.datetime:
    modification_time = os.path.getmtime(filename)
    parsed_date = datetime.datetime.fromtimestamp(modification_time)
    return parsed_date

def disk_size(filename: str) -> int:
    byte_usage = os.path.getsize(filename)
    return byte_usage

if __name__ == '__main__':
    pass