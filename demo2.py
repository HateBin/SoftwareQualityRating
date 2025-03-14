import math
def calculation_plot_y_max_height(max_number: int or float, max_y_interval_count: int = 7):

    if not isinstance(max_number, (int, float)):
        raise TypeError("输入必须为数值类型")
    if max_number < 0:
        raise ValueError("输入值不能为负数")

    base_intervals = tuple(range(1, 6))

    if max_number <= 1:
        return tuple(range(0, 3, 1))

    max_number = math.ceil(max_number)

    for interval in base_intervals:
        if max_number // interval < max_y_interval_count:
            return tuple(range(0, max_number + interval + 1, interval))

    max_interval = max(base_intervals)
    while True:
        if max_number // max_interval < max_y_interval_count:
             break
        max_interval *= 2

    # 返回计算出的Y轴最大高度和间隔
    return tuple(range(0, max_number + max_interval + 1, max_interval))

if __name__ == '__main__':
    print(calculation_plot_y_max_height(160.5))