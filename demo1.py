import datetime
from dateutil.relativedelta import relativedelta

def _get_date(date: str, month: int = None, day: int = None):
    if month is not None and not isinstance(month, int):
        raise ValueError("月参数必须是整数")
    if day is not None and not isinstance(day, int):
        raise ValueError("日参数必须是整数")

    try:
        date_time = datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError as e:
        if e.args[0] == "day is out of range for month":
            dates = date.split('-')
            raise ValueError(f"{dates[0]}年{dates[1]}月中不存在日期：{dates[2]}")
        else:
            raise ValueError("日期格式错误，请输入正确的日期格式，例如：2023-07-01")

    if month:
        date_time += relativedelta(months=month)
    if day:
        date_time += relativedelta(days=day)

    return date_time.strftime('%Y-%m-%d')


if __name__ == '__main__':
    try:
        print(_get_date('2099-02-29'))
    except ValueError as e:
        print(e)