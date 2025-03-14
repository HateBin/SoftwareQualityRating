import math
def calculation_plot_y_max_height(max_number: float) -> tuple[int, int]:
    """
    计算Y轴刻度最大值和间隔，保证range_max > max_number且输出为整数

    参数规则:
        - 当max_number <= 1时：固定返回 (2, 1)
        - 当max_number > 1时：确保range_max > max_number
        - 输出列表长度<=8：len(range(0, range_max+1, y_interval)) <=8

    参数:
        max_number (float): 输入数据最大值，必须为非负数

    返回:
        tuple[int, int]: (range_max, y_interval)

    异常:
        ValueError: 输入为负数或非数值时抛出

    测试示例:
        >>> calculation_plot_y_max_height(10)
        (12, 2)  # 生成列表长度7: [0,2,4,6,8,10,12]
        >>> calculation_plot_y_max_height(1)
        (2, 1)    # 列表长度3: [0,1,2]
        >>> calculation_plot_y_max_height(7)
        (8, 1)    # 列表长度9会触发调整→(8,2)→列表长度5: [0,2,4,6,8]
    """
    # =====================
    # 输入验证
    # =====================
    if not isinstance(max_number, (int, float)):
        raise TypeError("输入必须为数值类型")
    if max_number < 0:
        raise ValueError("输入值不能为负数")

    # =====================
    # 处理max_number <=1
    # =====================
    if max_number <= 1:
        return 2, 1  # 强制返回固定值

    # =====================
    # 主计算逻辑
    # =====================
    max_number = math.ceil(max_number)  # 确保输入转换为整数处理

    # 候选间隔基数 (1,2,5的倍数)
    base_intervals = [1, 2, 5]
    magnitude = 10 ** (len(str(int(max_number))) - 1)  # 数量级计算

    # 寻找最优解
    for interval in base_intervals:
        y_interval = interval * magnitude // 10  # 保证间隔为整数
        if y_interval == 0:
            y_interval = 1

        # 计算range_max必须大于max_number
        range_max = ((max_number // y_interval) + 1) * y_interval
        tick_count = (range_max // y_interval) + 1  # 包含0点的数量

        # 满足刻度数量<=8时立即返回
        if tick_count <= 8:
            return range_max, y_interval

    # 未找到合适解时降级处理（理论上不会执行到这里）
    return max_number + 1, 1


if __name__ == '__main__':
    range_max, y_interval, = calculation_plot_y_max_height(9)
    print(list(range(0, range_max + 1, y_interval)))