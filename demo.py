import datetime

date_str = '2024-01-01 23:32'
try:
    datetime.datetime.strptime(date_str, "%Y-%m-%d")
except ValueError:
    print("Invalid date format")