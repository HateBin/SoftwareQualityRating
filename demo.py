import math
def calculation_plot_y_max_height(max_number: int):
    """
    根据提供的最大数字计算图表的Y轴最大高度和Y轴间隔。

    该函数的目的是为了合理设置图表的Y轴刻度间隔和最大高度，使得图表既不过于拥挤也不过于稀疏。
    参数:
    - max_number (int): 图表中最大的数字。

    返回:
    - range_max (float): 计算出的Y轴最大高度。
    - y_interval (int): 计算出的Y轴刻度间隔。
    """
    # 处理max_number为None或0的情况，设置默认值和初始Y轴间隔
    if not max_number:
        max_number = 1
        y_interval = 1
    # 根据max_number的值选择合适的Y轴间隔
    elif max_number < 5:
        y_interval = 1
    elif max_number < 9:
        y_interval = 2
    elif max_number < 15:
        y_interval = 3
    else:
        y_interval = 5

    # 循环计算合适的Y轴最大高度和间隔
    while True:
        # 计算初步的Y轴最大高度
        range_max = math.ceil(max_number / y_interval) * y_interval
        # 如果初步计算的高度等于max_number，增加一个间隔以避免最大值重合
        if range_max == max_number:
            range_max += y_interval
        # 检查Y轴刻度数是否超过7，如果超过则加大间隔
        if range_max // y_interval > 7:
            y_interval *= 2
        else:
            break
    # 返回计算出的Y轴最大高度和间隔
    return range_max, y_interval, list(range(0, range_max + 1, y_interval))

if __name__ == '__main__':
    range_max, y_interval, = calculation_plot_y_max_height(10)
    print(list(range(0, range_max + 1, y_interval)))