from datetime import datetime


def format_timestamp(timestamp):
    t = datetime.fromtimestamp(int(timestamp))
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")
