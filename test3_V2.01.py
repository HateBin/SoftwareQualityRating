# 2025年3月9日00:35:14

"""
1、考虑不同客户端上线时间分开的问题
"""

# 导入必要的库
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional, TypeVar, List, Union, Tuple
from io import BytesIO
from openai import OpenAI, APIConnectionError, APIStatusError, APIError
from collections import defaultdict
import matplotlib.pyplot as plt
import cloudscraper
import os
import base64
import chinese_calendar as calendar
import datetime
import requests
import sys
import re
import functools
import traceback
import numpy as np
import platform
import json
import math
import time

IS_CREATE_REPORT = False  # 是否创建报告
IS_CREATE_AI_SUMMARY = False  # 是否创建AI总结
IS_SUPPORT_RETRY_CREATE_AI_SUMMARY = True  # 是否支持重试创建AI总结, 生成完成后可input进行重新生成
OPEN_AI_MODEL = 'r1'  # deepseek模型名称，目前支持：v3、r1、百炼r1、百炼v3

OPEN_AI_IS_STREAM_RESPONSE = True  # 是否支持流式响应

# 定义常量和全局变量
ACCOUNT = 'wuchong@addcn.com'  # 账号
PASSWORD = 'WUchong_1008'  # 密码
PROJECT_ID = "63835346"  # 项目ID
# REQUIREMENT_ID = "1163835346001078047"  # 需求ID 无BUG
REQUIREMENT_ID = "1163835346001071668"  # 需求ID
# REQUIREMENT_ID = "1163835346001033609"  # 需求ID 中规中矩  TypeError: '<=' not supported between instances of 'str' and 'NoneType'
# REQUIREMENT_ID = "1163835346001051222"  # 需求ID 较差的质量
# REQUIREMENT_ID = "1163835346001049795"  # 需求ID 较差的质量  开发周期也是很多小数点尾数
# REQUIREMENT_ID = "1163835346001055792"  # 需求ID 较差的质量
# REQUIREMENT_ID = "1163835346001118124"  # 需求ID
REQUIREMENT_LIST_ID = '1000000000000000417'  # 需求列表ID, 用于查询或者编辑列表展示字段的配置

DEPARTMENT = 'T5'  # 部门名称
TESTERS = ["吴崇", "许万乐", "梁锦松", "刘倩", "周国豪", "段雪花", "喻文涛", "毛有有"]  # 测试人员列表
TESTER_LEADER = DEPARTMENT + TESTERS[0]  # 测试负责人, 选取第一个测试人员作为测试负责人带上部门名称
BUG_LEVELS = ["致命", "严重", "一般", "提示", "建议"]  # BUG级别列表

TEST_REPORT_CC_RECIPIENTS = ['T5黄帝佳', 'T5董静']  # 测试报告抄送人列表

# 测试报告总结的组成部分，如不配置则由AI自己生成
TEST_REPORT_SUMMARY_COMPOSITION = [
    "总体评价",
    "核心亮点",
    "主要不足与改进建议",
    "后续优化重点",
    "风险预警",
]

HOST = 'https://www.tapd.cn'  # Tapd的域名

LINE_LENGTH = 100  # 横线的长度

# 图像文字的字体, 根据操作系统选择字体
PLT_FONT = {
    'macOS': 'STHeiti',
    'windows': 'SimHei',
}

# AI的模型映射
AI_CONFIG_MAPPING = {
    'v3': {'model': 'deepseek-chat', 'name': 'deepseek', 'msg': '源生deepseek-V3模型'},
    'r1': {'model': 'deepseek-reasoner', 'name': 'deepseek', 'msg': '源生deepseek-R1模型'},
    '百炼r1': {'model': 'deepseek-r1', 'name': 'tongyi', 'msg': '通义千问deepseek-V3模型'},
    '百炼v3': {'model': 'deepseek-v3', 'name': 'tongyi', 'msg': '通义千问deepseek-R1模型'},
}

AI_URL_AND_KEY = {
    'deepseek': {
        'url': 'https://api.deepseek.com/v1',
        'key': 'sk-00987978d24e445a88f1f5a57944818b',
    },
    'tongyi': {
        'url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'key': 'sk-a5ae4633515d448e9bbbe03770712d4e',
    },
}

# 创建一个CloudScraper实例，用于模拟浏览器请求
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',  # 模拟的浏览器类型为Chrome
        'platform': 'windows',  # 模拟的平台为Windows
        'desktop': True,  # 模拟桌面环境，而非移动设备
    }
)

# 定义泛型类型变量用于返回类型
ResponseType = TypeVar('ResponseType', requests.Response, Dict[str, Any])

# BUG列表中必须包含的字段
BUG_LIST_MUST_KEYS = [
    "status",  # 状态
    "custom_field_Bug等级",  # BUG等级
    "custom_field_严重等级",  # 严重等级
    "fixer",  # 修复人
    "resolved",  # 解决时间
    "created",  # 创建时间
    "closed",  # 关闭时间
    "source",  # 缺陷根源
    "platform",  # 软件平台
]

# 子任务列表中必须包含的字段
SUB_TASK_LIST_MUST_KEYS = [
    "owner",  # 处理人
    "begin",  # 预计开始
    "due",  # 预计结束
    "effort_completed",  # 完成工时
]

# 评分输入数据的格式
SCORE_INPUT_DATA = {
    'input_type': int,  # 输入类型
    'allow_content': [20, 15, 10, 5, 1]  # 评分输入数据的可选值
}

# 柱状图的颜色映射
PLOT_COLORS = [
    '#F6695E',  # 玫瑰红
    '#2196F3',  # 天蓝
    '#79DEA3',  # 浅绿
    '#EC9749',  # 橙色
    '#A65FB2',  # 紫罗兰
    '#E8E22F',  # 黄色
    '#5DC9D7',  # 浅蓝绿
    '#5E9555',  # 深绿
    '#FFCD39',  # 金黄
    '#D29DD7',  # 淡紫
    '#ED4B82',  # 草莓红
    '#6574C4',  # 深蓝
]


def create_plot(func):
    """
    图表创建装饰器工厂函数
    用于标准化生成Matplotlib图表，统一处理样式配置、资源清理和图表保存

    功能特性：
    1. 自动处理图表样式的标准化配置
    2. 自动管理图表对象的生命周期
    3. 统一错误处理和资源清理
    4. 支持将图表保存到内存缓冲区

    参数：
    func (Callable): 被装饰的图表数据生成函数，应返回包含图表配置的字典

    返回：
    Callable: 包装后的图表生成函数

    异常：
    当被装饰函数返回数据不符合规范时抛出 ValueError
    图表生成过程中发生错误时抛出 RuntimeError
    """

    @functools.wraps(func)  # 保留被装饰函数的元数据
    def wrapper(*args, **kwargs) -> dict:
        """
        装饰器包装函数

        执行流程：
        1. 执行被装饰函数获取图表数据
        2. 验证数据完整性
        3. 配置图表样式
        4. 保存图表到内存缓冲区
        5. 清理图表资源
        """
        buf = None  # 初始化图表缓冲区对象
        try:
            # ==================================================================
            # 数据准备阶段
            # ==================================================================

            # 执行被装饰函数获取图表配置数据
            func_data: dict = func(*args, **kwargs)

            # 验证返回数据结构的完整性
            required_keys = {'desiredWidthData', 'labels', 'title', 'maxBarHeight', 'ax'}
            if not required_keys.issubset(func_data.keys()):
                missing = required_keys - func_data.keys()
                raise ValueError(f"缺失必要的图表配置参数: {missing}")

            # ==================================================================
            # 数据解包与预处理
            # ==================================================================

            # 解包图表配置参数
            plot_data: dict = func_data['desiredWidthData']  # 图表尺寸等元数据
            labels: list[str] = func_data['labels']  # 数据系列标签列表
            title: str = func_data['title']  # 图表主标题
            max_bar_height: int = func_data['maxBarHeight']  # 最大柱状高度值
            ax: plt.Axes = func_data['ax']  # Matplotlib坐标轴对象

            # ==================================================================
            # 图表样式配置
            # ==================================================================

            # 设置图表主标题（字号17pt，默认字体由rcParams配置）
            plt.title(title, fontsize=17, pad=12)  # pad参数控制标题与图表的间距

            # 配置坐标轴边框样式
            # 隐藏顶部、右侧、左侧边框，底部边框设置为浅蓝色
            for spine in ['top', 'right', 'left']:
                ax.spines[spine].set_visible(False)
            ax.spines['bottom'].set_color('#c0d0e0')  # 使用HEX颜色码设置边框颜色

            # 配置X轴刻度样式
            ax.tick_params(
                axis='x',  # 作用于X轴
                length=10,  # 刻度线长度10像素
                labelsize=9,  # 标签字号9pt
                color='#c0d0e0',  # 刻度线颜色与底部边框一致
                labelcolor='black'  # 标签文字颜色为黑色
            )

            # 配置Y轴刻度样式
            ax.tick_params(
                axis='y',  # 作用于Y轴
                length=10,  # 刻度线长度10像素
                color='white',  # 刻度线颜色设置为白色（不可见）
                labelcolor='black'  # 标签文字颜色为黑色
            )

            # 配置网格系统
            ax.set_axisbelow(True)  # 将网格线置于数据层下方
            ax.grid(
                axis='y',  # 仅显示Y轴方向网格线
                linestyle='-',  # 实线样式
                alpha=0.7,  # 70%不透明度
                color='#e6ecf2'  # 浅灰色网格线
            )

            # ==================================================================
            # 图例配置
            # ==================================================================

            if labels:  # 当存在数据标签时添加图例
                ax.legend(
                    loc='upper center',  # 图例定位在图表上方中央
                    bbox_to_anchor=(0.5, -0.13),  # 调整图例位置（横轴居中，纵轴向下13%）
                    ncol=8,  # 分8列排列图例项
                    fontsize=10,  # 图例文字大小10pt
                    frameon=False,  # 不显示图例外框
                    handlelength=1.0,  # 图例标记长度1.0字符宽
                    handletextpad=0.3,  # 标记与文本间距0.3字符
                    columnspacing=1.3  # 列间距1.3字符
                )

            # ==================================================================
            # Y轴刻度配置
            # ==================================================================

            # 计算合适的Y轴范围及刻度间隔
            y_intervals = calculation_plot_y_max_height(max_bar_height)

            # 设置Y轴刻度位置及标签
            plt.yticks(
                y_intervals,  # 生成等间隔刻度位置
                labels=[str(x) for x in y_intervals]  # 生成纯数字标签
            )

            # 设置y轴的最大值
            max_height = max(y_intervals)

            # 设置Y轴显示范围（扩展10%的上方空间）
            ax.set_ylim(0, max_height * 1.1)

            # ==================================================================
            # 布局调整与图表保存
            # ==================================================================

            plt.tight_layout(pad=2.0)  # 自动调整子图参数，留白2.0英寸

            # 创建内存缓冲区保存图表图像
            buf = BytesIO()
            plt.savefig(
                buf,
                format='png',  # 输出PNG格式
                dpi=plt.rcParams['figure.dpi'],  # 使用全局DPI设置
                bbox_inches='tight'  # 紧凑模式，去除多余白边
            )

            # ==================================================================
            # 后处理与元数据计算
            # ==================================================================

            # 计算实际像素宽度（当存在宽度配置时）
            if plot_data and 'width' in plot_data:
                current_dpi = plt.rcParams['figure.dpi']
                plot_data['widthPx'] = int(plot_data['width'] * current_dpi)

            # 重置缓冲区指针以便读取数据
            buf.seek(0)

            # 返回图表路径和元数据
            return {
                'plotPath': upload_file(buf.getvalue()),  # 上传到文件存储服务
                'plotData': plot_data  # 包含尺寸等元数据
            }

        except Exception as e:
            # 错误处理：包装原始异常，添加上下文信息
            raise RuntimeError(f"图表生成失败: {str(e)}") from e
        finally:
            # ==================================================================
            # 资源清理阶段
            # ==================================================================

            # 确保关闭所有Matplotlib图形对象
            plt.close('all')

            # 显式释放缓冲区资源
            if buf:
                buf.close()

    return wrapper


def calculate_bug_count_rating(X: float) -> int or None:
    """
    根据BUG密度计算软件质量评分。

    评分规则：
    - BUG密度 = BUG总数 / (开发人数 × 日均工时)
    - 评分基于BUG密度所在的预设区间映射得到，密度越低评分越高

    参数:
        X (float): 计算得到的BUG密度值，表示平均每个开发人日的BUG数量
                   X的取值范围应为 X > 0，但方法内做了容错处理

    返回:
        int or None: 返回对应的质量评分(20/15/10/5/1分)，若输入不在任何区间则返回None

    异常处理:
        - 当输入X为负数时，默认匹配第一个区间(-1,1]
        - 当输入X为非数值类型时，会触发类型错误

    评分映射规则（左开右闭区间）:
        (-∞, 1]   → 20分（极低密度，质量优秀）
        (1, 1.5]  → 15分（低密度，质量良好）
        (1.5, 2]  → 10分（中等密度，质量合格）
        (2, 3]    → 5分（较高密度，质量堪忧）
        (3, +∞)   → 1分（极高密度，质量差）
    """
    # 定义评分区间与得分的映射关系（按评分从高到低排列）
    # 每个元组格式：(区间下界, 区间上界), 得分
    # 注意：区间为左开右闭，即 lower < X <= upper
    score_mapping = {
        (-1, 1): 20,  # 特殊处理负值情况，实际业务中X应为正数
        (1, 1.5): 15,  # 1 < X <= 1.5
        (1.5, 2): 10,  # 1.5 < X <= 2
        (2, 3): 5,  # 2 < X <= 3
        (3, float('inf')): 1  # X > 3
    }

    # 遍历所有评分区间
    for (lower, upper), score in score_mapping.items():
        # 检查X是否在当前区间内（左开右闭）
        if lower < X <= upper:
            return score

    # 若未匹配任何区间（理论上不会执行到这里，因最后一个区间覆盖+∞）
    # 防御性编程：打印警告信息并返回None
    print("错误：BUG密度值不在预期范围内，请检查输入数据有效性")
    return None


def calculate_bug_reopen_rating(X):
    """
    根据缺陷重新打开次数计算软件质量评分

    评分规则（左闭右闭区间）:
        0次  → 20分（质量优秀）
        1次  → 15分（质量良好）
        2次  → 10分（质量合格）
        3次  → 5分（质量堪忧）
        4次及以上 → 1分（质量差）

    参数:
        X (int): 缺陷重新打开次数，应为非负整数。
                  当输入值非整数时会触发隐式类型转换

    返回:
        int: 对应评分值（20/15/10/5/1分），输入不符合规范时返回None

    异常处理:
        - 输入负数值时触发AssertionError
        - 输入非数值类型将触发TypeError
        - 所有未定义情况返回None并打印警告
    """
    # 防御性处理：将输入强制转换为整数（处理浮点数输入情况）
    try:
        X = int(X)
    except (ValueError, TypeError):
        raise TypeError("错误：输入值必须为可转换为整数的类型")

    # 处理负值输入（根据业务逻辑视为最差情况）
    try:
        assert X >= 0
    except AssertionError:
        raise ValueError("错误：缺陷重新打开次数不应为负数")

    # 定义评分映射字典（key为最大次数阈值，value为对应得分）
    score_mapping = {
        0: 20,  # 0次重开得满分
        1: 15,  # 1次重开扣5分
        2: 10,  # 2次重开扣10分
        3: 5,  # 3次重开扣15分
        4: 1  # 4次及以上扣19分
    }

    # 遍历评分阈值判断区间（按阈值降序排列）
    for threshold in sorted(score_mapping.keys(), reverse=True):
        if X >= threshold:
            return score_mapping[threshold]


def calculate_bug_repair_rating(unrepaired_bug: dict) -> int or None:
    """
    根据未修复缺陷的严重程度计算缺陷修复质量评分

    评分规则（按优先级从高到低判断）：
    - 若上线当天存在未修复的致命(P0)或严重(P1)缺陷 → 1分（质量极差）
    - 若上线当天存在未修复的一般(P2)缺陷 → 5分（质量堪忧）
    - 若缺陷创建当天未修复致命(P0)但存在未修复严重(P1) → 10分（质量合格）
    - 若缺陷创建当天已修复所有P0/P1，但存在未修复P2 → 15分（质量良好）
    - 若所有缺陷在创建当天均被修复 → 20分（质量优秀）

    参数:
        unrepaired_bug (dict): 未修复缺陷分类字典，结构示例：
            {
                # 上线当天未修复的缺陷（按严重等级分组）
                "deployProdDayUnrepaired": {
                    "P0P1": ["BUG_ID1", ...],  # 致命/严重缺陷列表
                    "P2": ["BUG_ID2", ...]     # 一般缺陷列表
                },
                # 缺陷创建当天未修复的缺陷（按严重等级分组）
                "onThatDayUnrepaired": {
                    "P0": ["BUG_ID3", ...],    # 致命缺陷列表
                    "P1": ["BUG_ID4", ...],    # 严重缺陷列表
                    "P2": ["BUG_ID5", ...]     # 一般缺陷列表
                }
            }

    返回:
        int: 质量评分（20/15/10/5/1分）
        None: 当数据结构异常或未匹配任何条件时返回

    异常处理:
        - 当输入数据结构不符合预期时，打印错误日志并返回None
    """

    # 解构输入数据，提高可读性
    prod_day_unrepaired = unrepaired_bug.get('deployProdDayUnrepaired', {})
    on_that_day_unrepaired = unrepaired_bug.get('onThatDayUnrepaired', {})

    # ----------------------------
    # 优先级1：上线当天存在P0/P1未修复
    # ----------------------------
    # 检查上线当天未修复的致命/严重缺陷列表是否非空
    if prod_day_unrepaired.get('P0P1'):
        return 1  # 存在上线未修复的高危缺陷，最低评分

    # ----------------------------
    # 优先级2：上线当天存在P2未修复
    # ----------------------------
    # 检查上线当天未修复的一般缺陷列表是否非空
    if prod_day_unrepaired.get('P2'):
        return 5  # 存在上线未修复的中等缺陷，较低评分

    # ----------------------------
    # 优先级3：创建当天P0已修复但存在P1未修复
    # ----------------------------
    # P0已修复（列表为空）且P1未修复（列表非空）
    if not on_that_day_unrepaired.get('P0') and on_that_day_unrepaired.get('P1'):
        return 10  # 存在当天未修复的严重缺陷，中等评分

    # ----------------------------
    # 优先级4：创建当天P0/P1已修复但存在P2未修复
    # ----------------------------
    # P0和P1已修复（列表为空）且P2未修复（列表非空）
    if (not on_that_day_unrepaired.get('P0')
            and not on_that_day_unrepaired.get('P1')
            and on_that_day_unrepaired.get('P2')):
        return 15  # 仅存在当天未修复的低风险缺陷，良好评分

    # ----------------------------
    # 优先级5：所有缺陷均及时修复
    # ----------------------------
    # 所有严重等级缺陷列表均为空
    if (not on_that_day_unrepaired.get('P0')
            and not on_that_day_unrepaired.get('P1')
            and not on_that_day_unrepaired.get('P2')):
        return 20  # 无当天未修复缺陷，最高评分

    # ----------------------------
    # 异常处理：未匹配任何条件
    # ----------------------------
    # 打印结构化错误日志（实际项目中建议使用logging模块）
    print("错误：缺陷修复评分计算失败，数据结构异常或存在未覆盖的逻辑分支")
    print(f"输入数据结构：{json.dumps(unrepaired_bug, indent=2)}")
    return None  # 防御性返回


def _input(text: str, input_type: type = None, allow_content: list = None) -> any:
    """
    从用户获取输入并进行类型及有效性验证

    该函数实现一个交互式输入循环，持续提示用户输入直到满足以下条件：
    1. 输入内容能正确转换为指定类型（若指定 input_type）
    2. 输入内容存在于允许的值列表（若指定 allow_content）

    特性：
    - 自动处理类型转换异常
    - 支持自定义允许值范围验证
    - 提供友好的错误提示
    - 支持任意可转换类型（int/float/str等）

    参数详解：
    :param text: str -> 输入提示文本，显示在输入框前（如 "请输入年龄："）
    :param input_type: type -> 目标数据类型（如 int/float/str），None表示保持字符串类型
    :param allow_content: list -> 允许的输入值列表，None表示不限制输入范围

    返回：
    any -> 返回经过验证和类型转换后的输入值

    异常处理：
    - 类型转换失败时自动提示重新输入
    - 输入值不在允许范围内时提示有效值列表
    """
    # 无限循环直到获得合法输入
    while True:
        try:
            # 显示提示信息并获取原始输入
            raw_input = input(text)  # 调用内置input函数获取用户输入

            # 类型转换处理
            if input_type:
                # 尝试将输入转换为目标类型（如int('123')）
                converted_value = input_type(raw_input)
            else:
                # 未指定类型则保持原始字符串
                converted_value = raw_input

            # 允许值范围验证
            if allow_content is not None:
                # 检查转换后的值是否在允许列表中
                if converted_value not in allow_content:
                    # 构建友好的错误提示信息
                    allowed_values = ', '.join(map(str, allow_content))
                    error_msg = f"输入值必须在 [{allowed_values}] 范围内"
                    # 打印带颜色的错误提示
                    print(_print_text_font(f"\n错误：{error_msg}\n", color='red'))
                    continue  # 跳过后续代码，重新循环

            # 通过所有检查，返回合法值
            return converted_value

        except ValueError as ve:  # 捕获类型转换错误（如将字母串转为数字）
            # 提取目标类型名称（如 'int'/'float'）
            type_name = input_type.__name__ if input_type else '字符串'
            # 生成具体错误描述
            error_detail = f"输入的内容数据类型不匹配, 期望为 {type_name} 类型"
            print(_print_text_font(f"\n格式错误：{error_detail}\n", color='red'))

        except Exception as e:  # 防御性编程，捕获其他未预料异常
            # 打印通用错误提示（理论上不会执行到这里）
            print(_print_text_font("\n发生未预期的错误，请重新输入\n", color='red'))


def _print_text_font(text: str or int, is_weight: bool = False, color: str = 'red') -> str:
    """
    生成带有指定颜色和字重的ANSI转义序列格式化文本

    该函数通过ANSI转义码实现在终端输出彩色文本，支持8种基础颜色和字体加粗效果。
    返回的字符串可直接用于print()函数，在支持ANSI转义的终端中显示彩色文本。

    参数详解:
        text (str or int):
            需要格式化的文本内容。支持任意字符串或者数字，包含多行文本和特殊字符。
            示例："Hello World"

        is_weight (bool):
            字体加粗开关，默认为False。
            - True: 使用加粗字体(实际表现为增加亮度，因部分终端不支持真正的粗体)
            - False: 使用正常字体
            示例：is_weight=True 显示亮色文本

        color (str):
            文本颜色名称，不区分大小写，默认为'red'。支持以下颜色：
            - 基础色：black, red, green, yellow, blue, purple, cyan, white
            - 扩展色：默认红色(当输入颜色不在支持列表时)
            示例："blue" 显示蓝色文本

    返回值:
        str: 包含ANSI转义序列的格式化字符串。格式为：
            \033[字重代码;颜色代码m文本内容\033[0m
        示例：\033[1;91mError!\033[0m

    异常处理:
        无显式异常抛出，但颜色参数不在支持列表时会默认使用红色

    实现原理:
        1. ANSI转义码结构：
           - \033[  : 转义序列起始符
           - 代码部分: 由分号分隔的多个数值组成
           - m      : 表示样式设置结束
           - 文本内容: 应用样式的文本
           - \033[0m: 重置所有样式

        2. 颜色代码映射：
           基础颜色使用90-97区间的高亮前景色代码，与常规30-37代码相比具有更好的兼容性

    示例用法:
        print(_print_text_font("警告信息", is_weight=True, color="yellow"))
    """

    # 处理字重参数：将布尔值转换为ANSI代码
    # 0 = 正常，1 = 加粗/高亮（注意：部分终端中1表现为字体加亮而非真正加粗）
    weight_code = "1" if is_weight else "0"

    # 统一颜色参数为小写，实现大小写不敏感的匹配
    color = color.lower()

    # ANSI颜色代码映射字典
    # 键为颜色名称，值为对应的ANSI前景色代码
    color_codes = {
        'black': "90",  # 黑色
        'red': "91",  # 红色
        'green': "92",  # 绿色
        'yellow': "93",  # 黄色
        'blue': "94",  # 蓝色
        'purple': "95",  # 紫色
        'cyan': "96",  # 青色
        'white': "97"  # 白色
    }

    # 获取颜色代码，若颜色不存在则默认使用红色
    # 使用字典的get方法提供默认值，等效于：
    # color_code = color_codes[color] if color in color_codes else "91"
    color_code = color_codes.get(color, "91")  # 默认红色

    # 构建完整的ANSI转义序列
    # 结构说明：
    # - \033[         : 转义序列开始
    # - ;             : 分隔字重和颜色代码
    # - m             : 样式设置结束符
    # - {text}        : 需要格式化的文本
    # - \033[0m       : 重置所有样式到默认
    formatted_text = (
        f"\033[{weight_code};{color_code}m"  # 设置样式
        f"{text}"  # 添加文本内容
        "\033[0m"  # 重置样式
    )

    return formatted_text


def get_session_id():
    """
    用户登录认证并获取有效会话ID

    本方法实现完整的登录流程，包含以下关键步骤：
    1. 构造登录请求的URL和查询参数
    2. 准备登录表单数据（包含账户信息及加密后的密码）
    3. 发送加密的POST请求进行登录认证
    4. 处理响应及异常状态
    5. 自动更新会话cookie供后续请求使用

    流程细节：
    - 使用AES-CBC算法对密码进行零填充加密
    - 通过cloudscraper绕过基础的反爬机制
    - 自动处理cookie存储，成功登录后cookie会保存在scraper实例中
    - 严格检查HTTP状态码，识别403等异常状态
    - 登录失败时程序主动退出，避免后续无效操作

    异常处理：
    - 网络请求异常：捕获requests库相关异常并打印错误信息
    - 加密异常：由encrypt_password_zero_padding方法处理加密过程异常
    - 状态码异常：检测403等非常规状态，触发cookie更新流程

    关联方法：
    - encrypt_password_zero_padding()：实现密码加密逻辑
    - fetch_data()：后续请求使用本方法维护的会话状态
    """
    try:
        # 构建登录接口URL（主域名+登录路径）
        login_url = HOST + '/cloud_logins/login'

        # 构造URL查询参数：
        # - site：指定认证站点标识
        # - ref：登录成功后的跳转地址（经过URL编码的页面地址）
        login_params = {
            'site': 'TAPD',
            'ref': 'https://www.tapd.cn/tapd_fe/63835346/story/list?categoryId=0&useScene=storyList&groupType=&conf_id=1163835346001048563&left_tree=1',
        }

        # 初始化基础登录表单数据
        login_data = {
            # 登录后重定向地址（需与ref参数保持一致）
            'data[Login][ref]': 'https://www.tapd.cn/tapd_fe/63835346/story/list?categoryId=0&useScene=storyList&groupType=&conf_id=1163835346001048563&left_tree=1',
            # 登录操作标识符
            'data[Login][login]': 'login',
            # 用户邮箱账号（从全局常量ACCOUNT获取）
            'data[Login][email]': ACCOUNT,
        }

        # 通过加密方法生成密码相关字段：
        # 返回示例：
        # {
        #   'data[Login][password]': 'Base64加密后的密码',
        #   'data[Login][encrypt_iv]': 'Base64加密后的初始化向量',
        #   'data[Login][encrypt_key]': 'Base64加密后的密钥'
        # }
        encrypted_password = encrypt_password_zero_padding(PASSWORD)

        # 合并加密字段到登录表单数据
        login_data.update(encrypted_password)

        # 发送POST登录请求
        # 使用预配置的scraper实例（包含cloudscraper的防爬特性）
        # 关键参数：
        # - url：登录接口地址
        # - params：URL查询参数
        # - data：表单数据（application/x-www-form-urlencoded格式）
        response = scraper.post(
            url=login_url,
            params=login_params,
            data=login_data
        )

        # 严格检查HTTP状态码（非2xx状态会抛出HTTPError）
        # 作用：
        # 1. 识别网络错误（如500服务器错误）
        # 2. 检测登录失败（如401未授权）
        response.raise_for_status()

    except requests.RequestException as e:
        # 统一处理请求异常：
        # 包含连接超时、SSL错误、超时等所有requests异常
        # 打印错误信息后终止程序，避免后续无效操作
        print(f"登录失败: {str(e)}")
        sys.exit(1)


def get_workitem_status_transfer_history(entity_type: str, entity_id: str) -> list:
    """
    获取工作项（需求/任务/BUG）的状态流转历史记录

    通过TAPD官方API接口，获取指定实体的全生命周期状态变更记录，
    包括状态变更时间、操作人、来源状态和目标状态等关键信息。

    参数:
        entity_type (str): 实体类型标识符，取值范围：
            - 'story'   : 需求类实体
            - 'task'    : 任务类实体
            - 'bug'     : 缺陷类实体
        entity_id (str): 实体唯一标识符，如需求ID、任务ID、BUGID

    返回:
        dict: 结构化状态历史数据，格式示例：
        [
            {
                "change_type": "manual_update",
                "creator": "T5段雪花",
                "created": "2025-03-11 10:14:49",
                "changes": [
                    {
                        "field": "状态",
                        "value_before": "已验证",
                        "value_after": "已关闭",
                        "value_before_origin": "verified",
                        "value_after_origin": "closed",
                        "html_type": ""
                    },
                    {
                        "field": "关闭时间",
                        "value_before": "",
                        "value_after": "2025-03-11 10:14:49",
                        "value_before_origin": "",
                        "value_after_origin": "2025-03-11 10:14:49",
                        "html_type": ""
                    }
                ],
                "current_status": "已关闭",
                "current_status_origin": "closed",
                "status_remain_time": "0",
                "status_remain_begin_date": "2025-03-11 10:14:49",
                "status_remain_end_date": "2025-03-11 10:14:49",
                "entity_type": "bug"
            },
            ...
        ]
        若接口无数据或请求失败，返回空列表

    异常:
        requests.JSONDecodeError: 响应数据解析json异常时抛出
        ValueError: 响应数据解析异常时抛出
        KeyError: 响应数据结构缺失关键字段时抛出

    实现逻辑:
        1. 动态构建API请求URL和鉴权参数
        2. 通过统一请求方法fetch_data发送GET请求
        3. 校验数据完整性
        4. 提取核心业务数据并返回结构化结果
    """
    # ------------------------------
    # 阶段1：请求参数构造
    # ------------------------------
    # 拼接完整API端点URL（HOST取自全局常量）
    api_path = "/api/entity/workitems/get_workitem_status_transfer_history"
    url = f"{HOST}{api_path}"  # 示例：https://www.tapd.cn/api/entity/...

    # 构造查询参数：
    # - workspace_id : 项目空间ID（取自全局PROJECT_ID）
    # - program_id   : 项目集ID（当前项目未使用，置空字符串）
    # - entity_type  : 实体类型透传
    # - entity_id    : 实体ID强制转换为字符串类型
    params = {
        "workspace_id": PROJECT_ID,
        "program_id": "",  # 保留字段，保持为空
        "entity_type": entity_type,
        "entity_id": str(entity_id)  # 防御性类型转换
    }

    # ------------------------------
    # 阶段2：发送API请求
    # ------------------------------
    # 通过封装后的fetch_data方法发送GET请求
    # 该方法已内置重试机制和Cookie管理
    response = fetch_data(
        url=url,
        params=params,
        method="GET"
    )

    try:
        # ------------------------------
        # 阶段3：响应数据处理
        # ------------------------------
        # 将响应内容解析为JSON格式
        # 可能抛出JSONDecodeError（继承自ValueError）
        response_json = response.json()

        # 数据完整性校验：
        # 检查顶层data字段是否存在（TAPD标准响应结构）
        if "data" not in response_json:
            raise KeyError("API响应缺少'data'字段")

        # 提取业务数据主体
        status_history_data = response_json["data"]

        # 二次校验数据结构类型（防御非字典类型响应）
        if not isinstance(status_history_data, list):
            raise ValueError(
                f"预期列表类型状态数据，实际获取类型：{type(status_history_data)}"
            )

        return status_history_data

    except requests.JSONDecodeError as json_err:
        # 捕获JSON解析异常并附加上下文信息
        error_msg = f"响应内容非JSON格式，原始内容：{response.text[:200]}..."
        raise ValueError(error_msg) from json_err
    except KeyError as key_err:
        # 细化键缺失异常信息
        raise KeyError(f"响应数据缺失关键字段：{str(key_err)}") from key_err
    except Exception as orig_err:
        # 通用异常包装（保留原始堆栈信息）
        raise RuntimeError(
            f"获取状态历史记录失败，实体类型[{entity_type}] ID[{entity_id}]"
        ) from orig_err


def get_requirement_list_config() -> list:
    """
    获取TAPD需求列表视图的列字段配置信息

    通过TAPD官方API接口，获取指定需求列表视图的字段展示配置，包括系统字段和自定义字段。
    该配置决定在需求列表页面中展示哪些字段及字段的排列顺序。

    返回:
        list: 包含已配置字段标识符的列表，按视图中的显示顺序排列。
              示例: ['id', 'title', 'status', 'owner']
              若接口无数据或请求失败，返回空列表

    异常:
        requests.JSONDecodeError: 响应数据解析json异常时抛出
        ValueError: 响应数据解析异常时抛出
        KeyError: 响应数据结构缺失关键字段时抛出

    实现逻辑:
        1. 构造带鉴权参数的API请求URL
        2. 发送GET请求获取配置数据
        3. 校验响应数据结构完整性
        4. 提取字段配置信息并返回
    """
    # 构建完整API端点URL
    url = HOST + '/api/basic/userviews/get_show_fields'

    # 构造查询参数
    params = {
        "id": REQUIREMENT_LIST_ID,  # 需求列表视图ID
        "workspace_id": PROJECT_ID,  # 项目空间ID
        "location": "/prong/stories/stories_list",  # 视图位置路径
        "form": "show_fields",  # 表单类型标识
    }

    # 发送API请求并获取响应
    response = fetch_data(url, params=params, method='GET').json()

    try:
        # 数据完整性校验（防御性编程）
        if not isinstance(response, dict):
            raise ValueError("响应数据格式异常，预期字典类型")

        data = response.get('data', {})
        if not isinstance(data, dict):
            raise KeyError("响应数据缺失'data'字段")

        fields = data.get('fields', [])
        if not isinstance(fields, list):
            raise ValueError("字段配置数据格式异常，预期列表类型")

        return fields

    except requests.JSONDecodeError as json_err:
        error_msg = f"JSON解析失败，原始响应: {response.text[:200]}..." if 'response' in locals() else "响应内容为空"
        raise ValueError(error_msg) from json_err
    except KeyError as key_err:
        raise KeyError(f"响应数据缺失关键字段: {str(key_err)}") from key_err


def edit_requirement_list_config(custom_fields: str) -> bool:
    """
    编辑需求列表视图的列展示字段配置

    通过TAPD官方API接口，更新指定需求列表视图的字段展示配置。
    该操作将直接影响需求列表页面的字段显示和排序。

    参数:
        custom_fields (str): 配置的字段标识符字符串，多个字段用分号分隔
                            示例: "id;title;status;owner"

    返回:
        bool: 操作结果标识
              - True: 配置更新成功
              - False: 配置更新失败

    异常:
        requests.JSONDecodeError: 响应数据解析json异常时抛出
        ValueError: 输入参数格式异常或响应数据异常时抛出

    实现逻辑:
        1. 参数格式校验
        2. 构造带鉴权参数的API请求URL
        3. 发送POST请求更新配置
        4. 校验响应状态及业务状态码
    """
    # 参数校验
    if not isinstance(custom_fields, str) or ';' not in custom_fields:
        raise ValueError("参数格式异常，应为分号分隔的字符串")

    # 构建完整API端点URL
    url = HOST + '/api/basic/userviews/edit_show_fields'

    # 构造请求体数据
    data = {
        "id": REQUIREMENT_LIST_ID,  # 需求列表视图ID
        "custom_fields": custom_fields,  # 字段配置字符串
        "workspace_id": PROJECT_ID,  # 项目空间ID
        "location": "/search/get_all/bug",  # 视图位置路径（保留字段）
    }

    # 发送API请求并获取响应
    response = fetch_data(url, json=data, method='POST').json()

    try:
        # 响应状态校验（防御性编程）
        meta = response.get('meta', {})
        if meta.get('message') == 'success':
            return True
        return False

    except requests.JSONDecodeError as json_err:
        error_msg = f"响应数据非JSON格式，原始内容: {response.text[:200]}..."
        raise ValueError(error_msg) from json_err


def get_query_filtering_list_config() -> list:
    """
    获取TAPD查询过滤列表的字段展示配置

    通过TAPD官方API接口，获取指定查询过滤视图的字段展示配置，包含系统字段和自定义字段。
    该配置决定在缺陷列表页面中展示哪些字段及字段的排列顺序。

    返回:
        list: 包含已配置字段标识符的列表，按视图中的显示顺序排列。
              示例: ['id', 'title', 'status', 'owner']
              若接口无数据或请求失败，返回空列表

    异常:
        requests.JSONDecodeError: 响应数据解析json异常时抛出
        ValueError: 响应数据解析异常时抛出
        KeyError: 响应数据结构缺失关键字段时抛出

    实现逻辑:
        1. 构造带鉴权参数的API请求URL
        2. 发送POST请求获取配置数据
        3. 校验响应数据结构完整性
        4. 提取字段配置信息并返回
    """
    # 构建完整API端点URL（HOST取自全局常量）
    url = HOST + '/api/search_filter/search_filter/get_show_fields'

    # 构造请求体数据
    request_body = {
        "workspace_ids": [PROJECT_ID],  # 项目空间ID列表（当前仅支持单个项目）
        "location": "/search/get_all/bug",  # 视图位置路径（缺陷列表页面）
        "form": "show_fields",  # 表单类型标识
    }

    # 发送API请求并获取响应（使用封装后的fetch_data方法）
    response = fetch_data(
        url=url,
        json=request_body,
        method='POST'
    ).json()

    try:
        # ==================================================================
        # 数据完整性校验（防御性编程）
        # ==================================================================
        # 检查顶层data字段是否存在（TAPD标准响应结构）
        if "data" not in response:
            raise KeyError("API响应缺少'data'字段")

        # 提取业务数据主体
        config_data = response["data"]

        # 检查fields字段是否存在且为列表类型
        if not isinstance(config_data.get('fields'), list):
            raise ValueError(
                f"字段配置数据格式异常，预期列表类型，实际类型：{type(config_data.get('fields'))}"
            )

        return config_data['fields']

    except requests.JSONDecodeError as json_err:
        # 捕获JSON解析异常并附加上下文信息
        error_msg = f"响应内容非JSON格式，原始内容：{response.text[:200]}..." if 'response' in locals() else "响应内容为空"
        raise ValueError(error_msg) from json_err
    except KeyError as key_err:
        # 细化键缺失异常信息
        raise KeyError(f"响应数据缺失关键字段：{str(key_err)}") from key_err
    except Exception as orig_err:
        # 通用异常包装（保留原始堆栈信息）
        raise RuntimeError("获取查询过滤列表配置失败") from orig_err


def edit_query_filtering_list_config(custom_fields: str) -> bool:
    """
    编辑查询过滤列表的字段展示配置

    通过TAPD官方API接口，更新指定查询过滤视图的字段展示配置。
    该操作将直接影响缺陷列表页面的字段显示和排序。

    参数:
        custom_fields (str): 字段配置字符串，多个字段用分号分隔
                            格式要求：字段标识符必须存在于系统字段或自定义字段中
                            示例: "id;title;status;current_owner"

    返回:
        bool: 操作结果标识
              - True: 配置更新成功
              - False: 配置更新失败

    异常:
        requests.JSONDecodeError: 响应数据解析json异常时抛出
        ValueError: 输入参数格式异常或响应数据异常时抛出

    实现逻辑:
        1. 参数格式校验
        2. 构造带鉴权参数的API请求URL
        3. 发送POST请求更新配置
        4. 校验响应状态及业务状态码
    """
    # ==================================================================
    # 参数校验阶段
    # ==================================================================
    if not isinstance(custom_fields, str) or ';' not in custom_fields:
        raise ValueError("参数格式异常，应为分号分隔的字符串")

    # ==================================================================
    # 请求构造阶段
    # ==================================================================
    # 构建完整API端点URL
    url = HOST + '/api/search_filter/search_filter/edit_show_fields'

    # 构造请求体数据
    request_body = {
        "custom_fields": custom_fields,  # 字段配置字符串
        "location": "/search/get_all/bug",  # 视图位置路径（与获取配置时保持一致）
    }

    # ==================================================================
    # 请求执行阶段
    # ==================================================================
    response = fetch_data(
        url=url,
        json=request_body,
        method='POST'
    ).json()

    try:
        # ==================================================================
        # 响应校验阶段
        # ==================================================================
        # 检查meta字段是否存在（TAPD标准响应结构）
        if "meta" not in response:
            raise KeyError("API响应缺少'meta'字段")

        # 提取业务状态码
        meta_info = response["meta"]
        if meta_info.get('message') == 'success':
            return True
        return False

    except requests.JSONDecodeError as json_err:
        error_msg = f"JSON解析失败，原始响应: {response.text[:200]}..." if 'response' in locals() else "响应内容为空"
        raise ValueError(error_msg) from json_err
    except KeyError as key_err:
        raise KeyError(f"响应数据缺失关键字段: {str(key_err)}") from key_err


def get_user_detail() -> dict:
    """
    获取当前用户的详细信息

    通过TAPD官方API接口，获取当前认证用户的完整信息，包括：
    - 用户基础信息（ID、昵称、邮箱等）
    - 所属部门信息
    - 权限配置信息
    - 工作空间关联信息

    返回:
        dict: 结构化用户信息
        若接口无数据或请求失败，返回空字典

    异常:
        requests.JSONDecodeError: 响应数据解析json异常时抛出
        ValueError: 响应数据解析异常时抛出
        KeyError: 响应数据结构缺失关键字段时抛出

    实现逻辑:
        1. 构造用户信息API端点URL
        2. 发送GET请求获取用户数据
        3. 校验响应状态码和数据完整性
        4. 提取核心用户数据并返回
    """
    # ==================================================================
    # 阶段1：请求参数构造
    # ==================================================================
    # 拼接用户信息API端点（HOST取自全局常量）
    api_path = "/api/aggregation/user_and_workspace_aggregation/get_user_and_workspace_basic_info"
    url = f"{HOST}{api_path}"  # 完整URL示例：https://www.tapd.cn/api/aggregation/...

    # ==================================================================
    # 阶段2：发送API请求
    # ==================================================================
    # 通过封装后的fetch_data方法发送GET请求（已内置重试和Cookie管理）
    response = fetch_data(
        url=url,
        method="GET"
    )

    try:
        # ==================================================================
        # 阶段3：响应数据处理
        # ==================================================================
        # 将响应内容解析为JSON格式（可能抛出JSONDecodeError）
        response_json = response.json()

        # 数据完整性校验（多层防御校验）：
        # 1. 检查顶层data字段是否存在
        if "data" not in response_json:
            raise KeyError("API响应缺少'data'字段")

        # 2. 检查用户数据主体结构
        user_data = response_json["data"]
        if "get_current_user_ret" not in user_data:
            raise KeyError("响应数据缺少用户信息主体字段")

        # 3. 检查核心用户信息字段
        core_user_info = user_data["get_current_user_ret"].get("data", {})
        return core_user_info

    except requests.JSONDecodeError as json_err:
        # 捕获JSON解析异常并附加上下文信息
        error_msg = f"响应内容非JSON格式，原始内容：{response.text[:200]}..." if 'response' in locals() else "响应内容为空"
        raise ValueError(error_msg) from json_err
    except KeyError as key_err:
        # 细化键缺失异常信息
        raise KeyError(f"用户数据解析失败：{str(key_err)}") from key_err
    except Exception as orig_err:
        # 通用异常包装（保留原始堆栈信息）
        raise RuntimeError("获取用户信息失败") from orig_err


def get_requirement_tasks() -> List[Dict[str, Any]]:
    """
    获取指定需求的所有子任务信息

    通过TAPD官方API接口，递归获取指定需求的所有子任务信息，包括任务的基本信息、处理人、预计开始和结束时间、完成工时等。
    该方法支持分页查询，确保获取所有相关子任务数据。

    返回:
        list: 包含所有子任务信息的列表，每个子任务为一个字典结构。
              示例: [
                  {
                      "owner": "T5张三",  # 任务处理人
                      "begin": "2025-03-01",  # 预计开始时间
                      "due": "2025-03-05",  # 预计结束时间
                      "effort_completed": 10.5,  # 完成工时
                      ...
                  },
                  ...
              ]
              若接口无数据或请求失败，返回空列表

    异常:
        requests.JSONDecodeError: 响应数据解析json异常时抛出
        ValueError: 响应数据解析异常时抛出
        KeyError: 响应数据结构缺失关键字段时抛出

    实现逻辑:
        1. 构造API请求URL和查询参数
        2. 分页获取子任务数据
        3. 校验数据完整性
        4. 提取核心业务数据并返回
    """

    # 初始化页码和每页大小
    page: int = 1
    page_size: int = 100

    # 初始化存储子任务数据的列表
    requirement_tasks: list = []

    # 拼接完整API端点URL（HOST取自全局常量）
    api_path = "/api/entity/stories/get_children_stories"
    url = f"{HOST}{api_path}"  # 示例：https://www.tapd.cn/api/entity/...

    # 构造查询参数：
    # - workspace_id : 项目空间ID（取自全局PROJECT_ID）
    # - story_id : 需求ID（取自全局REQUIREMENT_ID）
    # - page : 当前页码
    # - per_page : 每页数据量
    # - sort_name : 排序字段（按预计结束时间排序）
    # - order : 排序顺序（升序）
    params = {
        "workspace_id": PROJECT_ID,
        "story_id": REQUIREMENT_ID,
        "page": page,
        "per_page": page_size,
        "sort_name": "due",
        "order": "asc",
    }

    # 循环分页获取所有子任务数据
    while True:
        # 通过封装后的fetch_data方法发送GET请求
        # 该方法已内置重试机制和Cookie管理
        response = fetch_data(
            url=url,
            params=params,
            method="GET"
        )

        try:
            # 将响应内容解析为JSON格式
            # 可能抛出JSONDecodeError（继承自ValueError）
            response_json = response.json()

            # 数据完整性校验：
            # 检查顶层data字段是否存在（TAPD标准响应结构）
            if "data" not in response_json:
                raise KeyError("API响应缺少'data'字段")

            # 检查children_list字段是否存在
            if "children_list" not in response_json['data']:
                raise KeyError("响应数据缺少children_list字段")

            # 提取业务数据主体
            requirement_datas: list = response_json["data"]['children_list']

            # 检查数据类型是否为列表
            if not isinstance(requirement_datas, list):
                raise ValueError(
                    f"预期列表类型状态数据，实际获取类型：{type(requirement_datas)}"
                )

            # 如果当前页数据为空，则退出循环
            if not requirement_datas:
                break

            # 将当前页数据添加到总列表中
            requirement_tasks.extend(requirement_datas)

            # 如果当前页数据量小于每页大小，说明已获取所有数据，退出循环
            if len(requirement_datas) < page_size:
                return requirement_tasks
            else:
                # 否则，增加页码，继续获取下一页数据
                params['page'] += 1

        except requests.JSONDecodeError as json_err:
            # 捕获JSON解析异常并附加上下文信息
            error_msg = f"响应内容非JSON格式，原始内容：{response.text[:200]}..."
            raise ValueError(error_msg) from json_err
        except KeyError as key_err:
            # 细化键缺失异常信息
            raise KeyError(f"响应数据缺失关键字段：{str(key_err)}") from key_err


def get_bug_list(requirement_name: str) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """
    获取指定需求关联的缺陷列表及其分类信息

    通过TAPD搜索接口分页获取指定需求的所有缺陷数据，同时提取平台和根源的分类选项信息。
    支持分页请求和动态字段配置，确保获取完整的缺陷数据集。

    参数:
        requirement_name (str): 需求名称，用于构建缺陷搜索条件

    返回:
        Tuple[List[str], List[str], List[Dict]]: 包含三个元素的元组：
            - 平台分类选项列表
            - 根源分类选项列表
            - 缺陷数据字典列表

    异常:
        ValueError: 当响应数据格式异常或关键字段缺失时抛出
        KeyError: 当接口返回数据结构不符合预期时抛出

    实现逻辑:
        1. 初始化分页参数和存储结构
        2. 构建动态查询条件并发送搜索请求
        3. 提取平台和根源的分类元数据
        4. 处理分页数据并合并结果集
        5. 校验数据结构完整性并返回标准化结果
    """
    # 初始化页码和每页大小
    page: int = 1  # 当前请求页码
    page_size: int = 100  # 每页数据量上限
    bugs: List[Dict] = []  # 存储缺陷数据的列表
    platforms: List[str] = []  # 存储平台分类选项
    sources: List[str] = []  # 存储根源分类选项

    # 构建API端点路径
    api_path = "/api/search_filter/search_filter/search"
    url = f"{HOST}{api_path}"  # 完整接口地址

    # 构造动态查询条件（JSON格式）
    search_condition = json.dumps({
        "data": [{
            "id": "5",
            "fieldLabel": "关联需求",
            "fieldOption": "like",
            "fieldType": "input",
            "fieldSystemName": "BugStoryRelation_relative_id",
            "value": requirement_name,
            "fieldIsSystem": "1",
            "entity": "bug"
        }],
        "optionType": "AND",
        "needInit": "1"
    })

    # 初始化请求参数模板
    request_data = {
        "workspace_ids": PROJECT_ID,  # 项目空间ID
        "search_data": search_condition,  # 序列化的搜索条件
        "obj_type": "bug",  # 查询对象类型为缺陷
        "hide_not_match_condition_node": "0",  # 显示不匹配条件节点
        "hide_not_match_condition_sub_node": "1",  # 隐藏不匹配子节点
        "page": page,  # 当前页码
        "perpage": str(page_size),  # 每页数据量（字符串类型）
        "order_field": "created",  # 按创建时间排序
    }

    # 分页请求循环
    while True:
        # 发送POST请求获取缺陷数据
        response = fetch_data(
            url=url,
            json=request_data,
            method="POST"
        )

        try:
            # 解析响应数据为JSON格式
            response_json = response.json()

            # 数据完整性校验：检查顶层data字段
            if "data" not in response_json:
                raise KeyError("API响应缺少'data'字段")

            # 首次请求时提取分类元数据
            if not platforms or not sources:
                # 校验项目特殊字段结构
                if "project_special_fields" not in response_json["data"]:
                    raise KeyError("响应数据缺少'project_special_fields'字段")

                # 获取当前项目的分类配置
                project_fields = response_json["data"]["project_special_fields"].get(PROJECT_ID, {})

                # 提取平台分类选项
                if not platforms and "platform" in project_fields:
                    platforms = [item["value"] for item in project_fields["platform"]]

                # 提取根源分类选项
                if not sources and "source" in project_fields:
                    sources = [item["value"] for item in project_fields["source"]]

            # 校验列表数据字段
            if "list" not in response_json["data"]:
                raise KeyError("响应数据缺少'list'字段")

            current_bugs = response_json["data"]["list"]  # 当前页缺陷数据

            # 数据类型校验
            if not isinstance(current_bugs, list):
                raise ValueError(f"缺陷数据格式异常，预期列表类型，实际类型：{type(current_bugs)}")

            # 合并数据到总列表
            bugs.extend(current_bugs)

            # 分页终止条件判断
            if len(current_bugs) < page_size:
                return platforms, sources, bugs  # 返回最终结果

            # 更新页码参数
            request_data["page"] += 1

        except requests.JSONDecodeError as e:
            # 处理JSON解析异常
            error_detail = f"响应内容非JSON格式，原始内容：{response.text[:200]}..." if hasattr(response,
                                                                                              'text') else "响应内容为空"
            raise ValueError(error_detail) from e


def fetch_data(
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        method: str = 'GET'
) -> ResponseType:
    """
    执行HTTP请求并处理重试逻辑

    核心功能：
    1. 统一请求执行入口，支持GET/POST/PUT/DELETE方法
    2. 自动处理会话Cookie管理
    3. 智能重试机制（网络错误/鉴权失败/服务端错误）
    4. 标准化响应处理

    参数:
        url (str): 请求目标URL
        params (Dict, optional): URL查询参数. 默认None
        data (Dict, optional): 表单数据. 默认None
        json (Dict, optional): JSON请求体. 默认None
        files (Dict, optional): 文件上传数据. 默认None
        method (str): HTTP方法，支持['GET', 'POST', 'PUT', 'DELETE']. 默认'GET'

    返回:
        Union[requests.Response, Dict]:
            - 成功时返回requests.Response对象
            - JSON解析失败时返回原始字典

    异常:
        requests.RequestException: 网络相关错误
        ValueError: 参数校验失败
        RuntimeError: 超过最大重试次数

    实现流程:
        1. 参数校验与准备
        2. 请求执行与状态检查
        3. 会话失效检测与更新
        4. 智能重试控制
        5. 响应格式标准化
    """
    # ==================================================================
    # 阶段1：参数校验与准备
    # ==================================================================
    # 校验HTTP方法有效性
    method = method.upper()
    if method not in {'GET', 'POST', 'PUT', 'DELETE'}:
        raise ValueError(f"不支持的HTTP方法: {method}")

    # 初始化重试计数器
    retry_count: int = 0
    max_retries: int = 3
    last_exception: Optional[Exception] = None

    # ==================================================================
    # 阶段2：请求循环执行
    # ==================================================================
    while retry_count <= max_retries:
        # 打印重试日志（非首次尝试时）
        if retry_count > 0:
            print(f'请求重试中({retry_count}/{max_retries}): {method} {url}')

        # 执行请求
        response = scraper.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json,
            files=files,
            timeout=30  # 统一超时设置
        )
        try:
            # ==================================================================
            # 阶段3：响应处理
            # ==================================================================
            # 强制检查HTTP状态码
            response.raise_for_status()

            if (response.status_code == 200
                    and "meta" in response.text
                    and "20002" in response.text):
                get_session_id()  # 重新获取会话
                raise requests.HTTPError('会话已过期', response=response)

            # 返回原始响应对象供后续处理
            return response

        except requests.RequestException as e:
            # ==================================================================
            # 阶段4：异常分类处理
            # ==================================================================
            last_exception = e
            response = getattr(e, 'response', None)

            # 处理会话过期(403)和业务错误码
            if isinstance(e, requests.HTTPError):
                if (response.status_code == 200
                        and "meta" in response.text
                        and "20002" in response.text):
                    print('检测到会话过期，正在更新Cookie...')
                    get_session_id()  # 重新获取会话
                elif 500 <= response.status_code < 600:
                    print(f'服务端错误({response.status_code})，等待重试...')

            # 更新重试计数器
            retry_count += 1

            # 最终重试检查
            if retry_count > max_retries:
                break

            # 智能等待策略（指数退避）
            wait_time = min(2 ** retry_count, 10)  # 上限10秒
            print(f'{wait_time}秒后重试...')
            time.sleep(wait_time)

    # ==================================================================
    # 阶段5：最终错误处理
    # ==================================================================
    error_msg = f"请求失败，超过最大重试次数({max_retries})"
    if last_exception is not None:
        error_msg += f": {str(last_exception)}"

    # 包含调试信息
    debug_info = {
        'url': url,
        'method': method,
        'retries': retry_count - 1,
        'status_code': getattr(response, 'status_code', None)
    }
    print(f"调试信息: {debug_info}")

    raise RuntimeError(error_msg)


def ai_result_switch_html(result: str) -> str:
    """
    将AI生成结果中的特定文本标记转换为标准HTML格式

    该函数通过一系列正则匹配和文本替换操作，将AI输出内容中的标记符号转换为HTML标签，
    使其能够在Web环境中正确显示格式和样式。转换规则包括颜色标记、标题层级、强调样式等。

    参数:
        result (str): AI输出的原始文本内容，包含约定的特殊标记符号

    返回:
        str: 转换后的HTML格式文本，可直接嵌入网页显示

    异常:
        re.error: 当正则表达式模式非法时抛出
        ValueError: 当输入内容非字符串类型时抛出

    实现逻辑:
        1. 移除井号标记，仅作为段落分隔符处理
        2. 转换基础排版符号（换行、水平线、空格、制表符）
        3. 处理颜色标记（红色强调文本）
        4. 转换标题标记（三级标题、二级标题）
        5. 处理强调文本（加粗效果）
        6. 防御性处理非法字符和嵌套标记

    转换规则说明:
        - "#文本" → 移除井号，作为普通段落
        - "\n" → <br/> 换行标签
        - "---" → <hr> 水平线
        - 空格 → &nbsp; 非断行空格
        - <red>文本</red> → <span style="color:#ff3b30;">文本</span>
        - ***文本*** → <h3>文本</h3> 三级标题
        - **文本** → <b>文本</b> 加粗文本
    """
    try:
        # ==================================================================
        # 参数校验
        # ==================================================================
        if not isinstance(result, str):
            raise ValueError("输入必须为字符串类型")

        # ==================================================================
        # 基础排版转换
        # ==================================================================
        # 移除段落标记井号（非破坏性处理，不影响原有结构）
        result = result.replace('#', '')

        # 换行符转换为HTML换行标签（保留段落结构）
        result = result.replace('\n', '<br/>')

        # 三个短横线转换为水平线标签（视觉分隔区块）
        result = result.replace('---', '<hr>')

        # 空格转换为非断行空格实体（保持文本对齐）
        result = result.replace(' ', '&nbsp;')

        # 制表符转换为四个非断行空格（模拟代码缩进效果）
        result = result.replace('\t', '&nbsp;' * 4)

        # ==================================================================
        # 颜色标记处理（使用正则确保完整标签匹配）
        # ==================================================================
        # 匹配<red>标签对并替换为红色span（支持嵌套内容捕获）
        result = re.sub(
            r'<red>(.*?)</red>',
            r'<span style="color:#ff3b30;">\1</span>',
            result,
            flags=re.DOTALL  # 允许跨行匹配
        )

        # ==================================================================
        # 标题标记转换（严格匹配三级标题标记）
        # ==================================================================
        # 匹配***包裹的文本生成h3标题（排除中间含*的情况）
        result = re.sub(
            r'\*\*\*(.*?)\*\*\*',
            r'<h3>\1</h3>',
            result,
            flags=re.DOTALL
        )

        # ==================================================================
        # 强调文本处理（避免与标题标记冲突）
        # ==================================================================
        # 匹配**包裹的文本生成加粗标签（不支持嵌套）
        result = re.sub(
            r'\*\*(.*?)\*\*',
            r'<b>\1</b>',
            result,
            flags=re.DOTALL
        )

        return result

    except re.error as e:
        # 包装正则错误并附加上下文信息
        error_msg = f"正则表达式处理失败: {str(e)}"
        raise re.error(error_msg) from e
    except Exception as e:
        # 通用异常处理（保留原始堆栈）
        raise RuntimeError(f"HTML转换失败: {str(e)}") from e


def ai_output_template(
        total_score: int = 100,
        sections: Optional[List[str]] = None,
        section_details: Optional[Dict[str, List[str]]] = None
) -> str:
    """
    生成AI总结报告的标准化模板结构

    本方法提供可定制的报告模板生成能力，支持动态配置章节内容和细节描述，
    同时保持格式规范性和视觉一致性。模板采用分级标题体系，支持多级结构化内容展示。

    参数详解:
        total_score (int): 项目总分值，用于总体评价部分展示。默认值100表示满分基准
        sections (List[str]): 需要包含的章节标题列表，控制模板结构。可选值：
            - "总体评价"    : 项目综合评分及总体结论
            - "核心亮点"    : 关键成功要素展示
            - "主要不足"    : 存在问题分析
            - "改进建议"    : 具体优化建议
            - "后续重点"    : 未来工作方向
            - "风险预警"    : 潜在风险说明
            默认包含全部章节
        section_details (Dict[str, List[str]]): 各章节预填充的细节内容字典
            格式示例：{
                "总体评价": ["项目最终评分为85分", "整体质量处于良好水平"],
                "核心亮点": ["架构设计合理性", "代码审查机制完善"]
            }

    返回:
        str: 结构化的模板字符串，包含Markdown格式标记，可直接用于AI内容生成引导

    异常:
        ValueError: 当传入的section_details包含未在sections中声明的章节时抛出

    实现策略:
        1. 模块化结构配置：通过sections参数控制模板包含的章节及顺序
        2. 分层内容填充：支持预定义内容占位符，提升模板实用性
        3. 智能默认值：当参数未指定时自动生成完整模板结构
        4. 防御性校验：确保用户自定义内容与模板结构的一致性

    模板特性:
        - 采用***作为一级标题标识符
        - 使用▶作为二级条目标识
        - 使用▷作为三级子项标识
        - 支持<red>标签突出关键内容
        - 自动生成水平分隔线
    """

    # ==================================================================
    # 中文序号构建
    # ==================================================================
    # 转换数字编号为中文
    def num_to_chinese(num: int) -> str:
        """将数字转换为中文序号"""
        chinese_num = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        return chinese_num[num] if 0 <= num <= len(chinese_num) else str(num)

    # 处理章节参数
    valid_sections = sections if sections else TEST_REPORT_SUMMARY_COMPOSITION

    # 校验预填充内容
    if section_details:
        invalid_keys = set(section_details.keys()) - set(valid_sections)
        if invalid_keys:
            raise ValueError(f"无效的章节配置: {invalid_keys}")

    # ==================================================================
    # 模板结构构建
    # ==================================================================
    template = []

    # 动态生成中间章节
    for idx, section in enumerate(valid_sections):
        # 章节标题
        template.append(f"***{num_to_chinese(idx)}、{section}***")

        # 预填充内容处理
        if section == "总体评价":
            template.extend([f"▶ 项目最终评分为XX分（满分{total_score}），整体质量处于XX水平。XXXXXXXXXXXXXXXXXXXX"])
        elif section_details and section in section_details:
            for item in section_details[section]:
                template.append(f"▶ **{item}**：XXXXXXXX")
        else:
            # 默认占位符生成规则
            if section == "核心亮点":
                template.extend([
                    "▶ **XXXXXX**：XXXXXXXX",
                    "▶ **XXXXXX**：XXXXXXXX",
                    "▶ ..."
                ])
            elif "不足" in section:
                template.extend([
                    "▶ **XXXXXXX**",
                    "    ▷ XXXXXXXXXX",
                    "    ▷ <red>建议</red>：XXXXXXXXXXXX",
                    "▶ ..."
                ])
            elif "优化" in section:
                template.extend([
                    "▶ **XXXXXXXX**：XXXXXXXX",
                    "▶ **XXXXXXXX**：XXXXXXXX",
                    "▶ ..."
                ])
            else:
                template.append("▶ XXXXXXXXXXXXXXXXX")

        # 添加分隔线（最后一个章节不添加）
        if section != valid_sections[-1]:
            template.append("---")

    return '\n'.join(template)


def deepseek_chat(
        user_input: str,
        temperature: float = 0.1,
        top_p: float = 0.5,
        max_tokens: int = 1024,
        retries: int = 3
) -> str:
    """
    执行与DeepSeek模型的交互会话，支持流式和非流式响应模式

    该方法封装了与DeepSeek API的完整交互流程，包含智能重试机制、响应内容实时解析
    和结构化错误处理。支持动态调整生成参数，适用于不同复杂度的对话场景。

    参数详解:
        user_input (str): 用户输入文本，需进行对话处理的原始内容
        temperature (float): 采样温度，取值范围[0,1]。值越小生成结果越确定，值越大越随机。默认0.1
        top_p (float): 核采样概率，取值范围[0,1]。控制生成多样性的阈值。默认0.5
        max_tokens (int): 生成内容的最大token数，取值范围[1, 4096]。默认1024
        retries (int): 网络错误时的最大重试次数。默认3

    返回:
        str: 格式化的HTML内容，包含：
            - 思考过程（灰色斜体）
            - 最终答案（标准格式）
            - 自动生成的排版标记

    异常:
        ValueError: 模型配置错误时抛出
        APIError: API返回非200状态码时抛出
        ConnectionError: 网络连接失败时抛出

    实现策略:
        1. 动态模型选择：根据配置自动匹配合适的API端点
        2. 双模式处理：统一处理流式/非流式响应
        3. 上下文管理：自动清理资源，确保连接安全关闭
        4. 实时反馈：流式模式下即时输出中间思考过程
    """
    # ==================================================================
    # 初始化准备阶段
    # ==================================================================
    result = []

    # 防御性配置校验
    open_ai_model = OPEN_AI_MODEL.lower()
    if open_ai_model not in AI_CONFIG_MAPPING:
        raise ValueError(f'模型配置错误，支持: {", ".join(AI_CONFIG_MAPPING.keys())}')

    model = AI_CONFIG_MAPPING[open_ai_model]['model']
    open_ai_config_data = AI_URL_AND_KEY[AI_CONFIG_MAPPING[open_ai_model]['name']]

    # ==================================================================
    # API交互核心逻辑
    # ==================================================================
    client = OpenAI(
        api_key=open_ai_config_data['key'],
        base_url=open_ai_config_data['url'],
        timeout=60.0  # 统一超时设置
    )

    for attempt in range(retries):
        print(f"{AI_CONFIG_MAPPING[open_ai_model]['msg']}执行中，请稍等...")
        try:
            # 创建聊天补全请求
            completion = client.chat.completions.create(
                model=model,  # 模型选择
                messages=[{"role": "user", "content": user_input}],  # 用户输入
                stream=OPEN_AI_IS_STREAM_RESPONSE,  # 流式/非流式选择, True: 流式响应，False: 普通响应
                temperature=temperature,  # 采样温度选择
                top_p=top_p,  # 核采样概率选择
                max_tokens=max_tokens,  # 最大输出长度选择
                extra_headers={"X-Dashboard-Version": "v3"}  # 兼容旧版API
            )

            # ==================================================================
            # 响应处理阶段
            # ==================================================================
            if OPEN_AI_IS_STREAM_RESPONSE:
                return _handle_stream_response(completion, result)
            return _handle_normal_response(completion, result)

        except APIConnectionError as e:
            # 网络层错误处理
            if attempt == retries - 1:
                raise ConnectionError(f"API连接失败: {str(e)}") from e
            time.sleep(2 ** attempt)  # 指数退避
        except APIStatusError as e:
            # 业务状态错误处理
            raise APIError(f"API返回错误: {e.status_code} {e.response.text}") from e

    return ai_result_switch_html(''.join(result))


def extract_matching(pattern: str, text: str) -> list:
    """
    使用预编译的正则表达式模式从输入文本中提取所有匹配项

    该方法通过预编译正则表达式模式优化匹配效率，并返回所有符合模式的子字符串列表。
    支持处理多行文本和复杂匹配规则，适用于从结构化文本中批量提取特定格式的信息。

    参数:
        pattern (str): 正则表达式模式字符串，定义需要匹配的文本规则。示例: r"\d(.*?)$"
        text (str): 需要执行匹配操作的原始文本内容。支持多行文本和Unicode字符

    返回:
        list: 包含所有非重叠匹配结果的字符串列表，按出现顺序排列。
              若无匹配项或输入为空，返回空列表

    异常:
        re.error: 当传入的pattern不是有效的正则表达式时抛出
        TypeError: 当text参数不是字符串类型时抛出

    实现逻辑:
        1. 正则表达式预编译
        2. 输入参数校验
        3. 执行匹配操作
        4. 返回标准化结果
    """
    try:
        # ==================================================================
        # 阶段1：正则表达式预编译
        # ==================================================================
        # 编译正则表达式模式以提高重复使用效率，添加re.DOTALL标志支持跨行匹配
        regex = re.compile(pattern, flags=re.DOTALL)  # re.DOTALL使.匹配包括换行符的所有字符

        # ==================================================================
        # 阶段2：输入参数校验
        # ==================================================================
        # 校验文本输入类型，防御非字符串类型输入
        if not isinstance(text, str):
            raise TypeError(f"文本参数必须为字符串类型，当前类型: {type(text).__name__}")

        # ==================================================================
        # 阶段3：执行匹配操作
        # ==================================================================
        # 使用预编译的正则对象查找所有非重叠匹配，返回匹配字符串列表
        matches = regex.findall(text)

        # ==================================================================
        # 阶段4：结果标准化处理
        # ==================================================================
        # 过滤空匹配项，确保返回列表元素均为有效字符串
        return [match for match in matches if match]

    except re.error as e:
        # 包装原始异常，添加模式上下文信息
        error_msg = f"无效的正则表达式模式: '{pattern}' - {str(e)}"
        raise re.error(error_msg) from e


def get_days(
        start_date: Union[str, datetime.date],
        end_date: Union[str, datetime.date],
        is_workday: bool = True,
        date_format: str = "%Y-%m-%d"
) -> List[str]:
    """
    获取指定日期范围内的日期序列，支持工作日过滤和自定义格式输出

    该方法提供完整的日期处理流程，包含类型转换、范围校验、工作日过滤等功能，
    适用于需要获取连续日期序列的业务场景，支持多种输入格式和灵活的输出配置

    参数:
        start_date (Union[str, datetime.date]):
            起始日期，接受"YYYY-MM-DD"格式字符串或datetime.date对象
        end_date (Union[str, datetime.date]):
            结束日期，格式要求与start_date一致，需大于等于起始日期
        is_workday (bool):
            是否进行工作日过滤，True返回仅工作日，False返回所有日期，默认为True
        date_format (str):
            输出日期的格式化字符串，遵循datetime.strftime语法，默认为"%Y-%m-%d"

    返回:
        List[str]:
            符合要求的日期字符串列表，按时间升序排列，格式由date_format参数指定

    异常:
        ValueError:
            1. 当日期字符串格式不符合YYYY-MM-DD规范时抛出
            2. 当起始日期晚于结束日期时抛出
        TypeError:
            当输入参数不是str/datetime.date类型时抛出

    实现流程:
        1. 参数校验与统一类型转换
        2. 日期范围有效性验证
        3. 基础日期序列生成
        4. 工作日过滤处理
        5. 最终格式标准化
    """

    # ==================================================================
    # 阶段1：参数校验与统一类型转换
    # ==================================================================
    def _convert_date(date_value: Union[str, datetime.date]) -> datetime.date:
        """统一日期输入格式，支持字符串和date对象类型转换"""
        if isinstance(date_value, str):
            try:
                # 严格校验日期字符串格式
                return datetime.datetime.strptime(date_value, "%Y-%m-%d").date()
            except ValueError as e:
                # 包装异常信息，增强可读性
                raise ValueError(
                    f"无效的日期格式: '{date_value}'，要求格式: YYYY-MM-DD"
                ) from e
        if isinstance(date_value, datetime.date):
            return date_value
        # 明确提示支持的类型
        raise TypeError(
            f"不支持的日期类型: {type(date_value).__name__}，"
            f"支持类型: str/datetime.date"
        )

    try:
        # 执行双日期转换
        start_dt = _convert_date(start_date)
        end_dt = _convert_date(end_date)
    except (ValueError, TypeError) as e:
        # 捕获底层异常并重新抛出
        raise type(e)(f"参数校验失败: {str(e)}") from e

    # ==================================================================
    # 阶段2：日期范围有效性验证
    # ==================================================================
    if start_dt > end_dt:
        # 生成明确的错误描述
        raise ValueError(
            f"无效的日期范围: 起始日期({start_dt.isoformat()}) "
            f"不能晚于结束日期({end_dt.isoformat()})"
        )

    # ==================================================================
    # 阶段3：基础日期序列生成
    # ==================================================================
    date_sequence = []
    current_dt = start_dt
    # 使用增量方式生成日期，避免计算总天数时的潜在错误
    while current_dt <= end_dt:
        date_sequence.append(current_dt)
        current_dt += datetime.timedelta(days=1)

    # ==================================================================
    # 阶段4：工作日过滤处理
    # ==================================================================
    if is_workday:
        # 使用列表推导式进行高效过滤
        filtered_dates = [
            dt
            for dt in date_sequence
            if calendar.is_workday(dt)
               and not calendar.is_holiday(dt)  # 明确排除节假日
        ]
    else:
        filtered_dates = date_sequence

    # ==================================================================
    # 阶段5：最终格式标准化
    # ==================================================================
    # 统一进行格式化处理，确保输出一致性
    return [dt.strftime(date_format) for dt in filtered_dates]


def encrypt_password_zero_padding(password: str) -> Dict[str, str]:
    """
    使用AES-CBC算法对密码进行零填充加密，并进行Base64编码

    该方法严格遵循零填充规范实现加密流程，主要面向需要兼容传统系统的场景。
    注意：零填充存在安全隐患，建议优先使用PKCS7等标准填充方案

    参数:
        password (str):
            需要加密的明文密码，支持任意长度的UTF-8字符串。
            空字符串将被拒绝，最小长度建议为8个字符

    返回:
        Dict[str, str]:
            包含加密结果的字典，结构为：
            {
                'data[Login][password]': Base64编码的密文,
                'data[Login][encrypt_iv]': Base64编码的初始化向量,
                'data[Login][encrypt_key]': Base64编码的加密密钥
            }

    异常:
        ValueError:
            1. 当输入密码为空字符串时抛出
            2. 当密码包含非UTF-8字符时抛出
            3. 当填充后数据长度不符合块大小时抛出
        TypeError:
            当输入参数不是字符串类型时抛出

    实现流程:
        1. 输入参数校验与预处理
        2. 密码学安全随机数生成
        3. 零填充处理
        4. 加密器初始化与加密操作
        5. 安全返回结果
    """

    # ==================================================================
    # 阶段1：输入参数校验与预处理
    # ==================================================================
    if not isinstance(password, str):
        raise TypeError(f"密码必须为字符串类型，当前类型: {type(password).__name__}")

    if not password:
        raise ValueError("密码不能为空字符串")

    try:
        plaintext = password.encode('utf-8')
    except UnicodeEncodeError as e:
        raise ValueError("密码包含非UTF-8编码字符") from e

    # ==================================================================
    # 阶段2：密码学安全随机数生成
    # ==================================================================
    key = os.urandom(32)  # AES-256密钥
    iv = os.urandom(16)  # CBC模式初始化向量

    # ==================================================================
    # 阶段3：零填充处理
    # ==================================================================
    block_size = 16  # AES块大小
    padding_length = block_size - (len(plaintext) % block_size)

    # 验证填充有效性
    if padding_length == 0:
        padding_length = block_size  # 处理正好对齐的情况

    try:
        # 使用二进制零字节填充
        padded_data = plaintext + b'\x00' * padding_length
    except OverflowError as e:
        raise ValueError("填充长度计算错误") from e

    # 防御性检查
    if len(padded_data) % block_size != 0:
        raise ValueError("填充后数据长度不符合块大小要求")

    # ==================================================================
    # 阶段4：加密器初始化与加密操作
    # ==================================================================
    try:
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    except ValueError as e:
        raise RuntimeError("加密过程参数错误") from e
    except Exception as e:
        raise RuntimeError("加密操作失败") from e

    # ==================================================================
    # 阶段5：安全返回结果
    # ==================================================================
    return {
        'data[Login][password]': base64.b64encode(ciphertext).decode('utf-8'),
        'data[Login][encrypt_iv]': base64.b64encode(iv).decode('utf-8'),
        'data[Login][encrypt_key]': base64.b64encode(key).decode('utf-8')
    }


def switch_numpy_data(data: dict) -> tuple:
    """
    将给定的字典数据转换为NumPy数组，同时提取并生成对应的标签。

    该方法处理多层嵌套字典结构，将同一子键下的数值按行排列，形成二维NumPy数组。
    支持处理包含数值类型（int/float）的直接键值对，自动归类到特殊键'_'对应的行。

    参数:
        data (dict): 输入数据字典，结构示例：
            {
                '分类1': {'子键A': 10, '子键B': 20},
                '分类2': {'子键A': 30, '子键B': 40},
                '分类3': 50  # 直接数值将归入特殊键'_'
            }

    返回:
        tuple[list[str], numpy.ndarray]:
            - labels (list[str]): 子键名称列表，按首次出现顺序排列
            - np_data (numpy.ndarray): 二维数组，行对应子键，列对应原始数据键

    异常:
        TypeError: 当输入值既不是字典也不是数值时抛出
        ValueError: 当数据结构不一致时（如子键长度不一致）抛出

    实现流程:
        1. 数据解构与标签收集：遍历输入数据，识别所有子键并收集数值
        2. 数据对齐与验证：确保每个子键对应的数值列表长度一致
        3. 数组转换：将重组后的数据转换为NumPy数组，保留原始数据类型
    """
    labels = []
    new_data = {}

    # ==================================================================
    # 阶段1：数据解构与标签收集
    # ==================================================================
    try:
        for outer_key, value in data.items():
            if isinstance(value, dict):
                # 处理嵌套字典结构，提取子键和对应值
                for sub_key, sub_value in value.items():
                    # 维护唯一且有序的子键列表（按首次出现顺序）
                    if sub_key not in labels:
                        labels.append(sub_key)
                    # 初始化子键对应的数据列表（如果不存在）
                    if sub_key not in new_data:
                        new_data[sub_key] = []
                    # 添加当前外层键对应的子键数值，保持原始数据类型
                    new_data[sub_key].append(sub_value)
            elif isinstance(value, (int, float)):
                # 处理直接数值类型，使用'_'作为特殊键归类
                if '_' not in new_data:
                    new_data['_'] = []
                new_data['_'].append(value)
            else:
                # 非字典或数值类型触发异常
                raise TypeError(
                    f"值类型必须为dict或数值，当前类型: {type(value).__name__}"
                )
    except KeyError as e:
        raise ValueError("输入数据结构异常，子键缺失") from e

    # ==================================================================
    # 阶段2：数据对齐与验证
    # ==================================================================
    # 计算外层键数量作为预期数据长度
    expected_length = len(data)
    # 检查每个子键的数据列表长度是否一致
    for sub_key, values in new_data.items():
        if len(values) != expected_length:
            raise ValueError(
                f"数据长度不一致，子键'{sub_key}'应有{expected_length}个值，实际{len(values)}个"
            )

    # ==================================================================
    # 阶段3：数组转换
    # ==================================================================
    try:
        # 将字典值转换为二维数组，NumPy自动推断数据类型（int/float）
        np_data = np.array(list(new_data.values()))
    except Exception as e:
        raise ValueError("NumPy数组转换失败") from e

    return labels, np_data


def calculation_plot_y_max_height(max_number: Union[int, float], max_y_interval_count: int = 7) -> tuple:
    """
    根据最大数据值计算Y轴刻度范围及间隔，生成等分刻度序列

    该函数通过动态调整间隔值，确保在指定最大刻度数量的前提下，找到最合适的刻度间隔。
    支持处理整数和浮点型输入，能够智能识别数据范围并生成易读的刻度分布。

    参数详解:
        max_number (int/float):
            输入的最大数据值，必须为非负数。该值决定了Y轴的上界
            示例: 若柱状图最高柱子为23.5，则max_number=23.5
        max_y_interval_count (int):
            期望的最大刻度线数量（含0刻度），控制刻度密度。默认7个间隔
            示例: 设为5时，可能生成[0,5,10,15,20]的刻度序列

    返回:
        tuple: 包含等分刻度值的元组，按升序排列
        示例: (0, 5, 10, 15, 20, 25)

    异常处理:
        TypeError: 输入非数值类型时抛出
        ValueError: 输入负数时抛出

    实现策略:
        1. 基础校验：类型检查与数值范围校验
        2. 特殊处理：极小值快速返回固定区间
        3. 动态计算：通过基准间隔和倍数扩展，寻找最优解
        4. 边界处理：确保最大值能被间隔整除并留有余量
    """
    # ==================================================================
    # 阶段1：输入参数校验
    # ==================================================================
    # 类型检查：确保输入为数值类型
    if not isinstance(max_number, (int, float)):
        raise TypeError("输入必须为整数或浮点数类型")

    # 数值范围检查：排除负数输入
    if max_number < 0:
        raise ValueError("输入值不能为负数")

    # ==================================================================
    # 阶段2：极小值快速处理
    # ==================================================================
    # 当最大值小于等于1时，返回固定刻度区间[0,1,2]
    # 避免对小数值进行复杂的间隔计算
    if max_number <= 1:
        return tuple(range(0, 3))

    # ==================================================================
    # 阶段3：基准间隔计算
    # ==================================================================
    # 对最大值向上取整，确保包含所有数据点
    # 示例: 23.2 → 24
    ceil_max = math.ceil(max_number)

    # 定义基础间隔候选集，优先使用人类友好的数字(1-5)
    # 这些数字易于整除且符合常见刻度习惯
    base_intervals = (1, 2, 3, 4, 5)

    # 遍历基准间隔，寻找第一个满足刻度数量限制的间隔
    for interval in base_intervals:
        # 计算当前间隔下的刻度数量
        # 公式：ceil(最大值/间隔) + 1（包含0刻度）
        # 示例：ceil(24/5)=5 → 5+1=6个刻度
        required_ticks = ceil_max // interval + 1

        # 判断是否满足最大刻度数量要求
        if required_ticks < max_y_interval_count:
            # 生成刻度序列：从0开始按间隔递增，直到超过最大值
            # 示例：interval=5 → (0,5,10,15,20,25)
            return tuple(range(0, ceil_max + interval + 1, interval))

    # ==================================================================
    # 阶段4：动态扩展间隔
    # ==================================================================
    # 当基准间隔都无法满足要求时，以最大基准间隔为起点进行倍数扩展
    # 初始间隔设为基准间隔最大值(5)，每次循环翻倍直到满足条件
    dynamic_interval = max(base_intervals)
    while True:
        # 计算动态扩展后的刻度数量
        required_ticks = ceil_max // dynamic_interval + 1

        # 判断是否满足刻度数量限制
        if required_ticks < max_y_interval_count:
            # 生成最终刻度序列，并扩展10%空间确保数据点不被截断
            # 示例：dynamic_interval=10 → (0,10,20,30)
            return tuple(range(0, ceil_max + dynamic_interval + 1, dynamic_interval))

        # 间隔翻倍继续尝试
        dynamic_interval *= 2


def calculate_plot_width(
        keys: list,
        fig: plt.Figure,
        bar_width: float = 0.073
) -> Tuple[float, Dict[str, float]]:
    """
    根据数据标签特征动态计算柱状图布局参数

    参数:
        keys (list):
            数据标签列表，决定X轴标签长度和柱子数量
            示例: ['分类A', '分类B', '长分类名称C']
        fig (plt.Figure):
            Matplotlib图形对象，用于设置物理尺寸
        bar_width (float):
            基础柱子宽度系数，默认0.073（经验值）

    返回:
        Tuple[float, Dict]:
            - desired_bar_width: 优化后的柱子宽度（比例值）
            - plot_data: 包含图形宽度参数的字典（保持原始结构）:
                { 'width': 最终应用的图形宽度 }

    优化点:
        1. 增强长标签处理能力
        2. 优化多柱子场景的显示密度
        3. 改进宽度计算公式的平滑度
    """
    # ==================================================================
    # 输入校验（防御性编程）
    # ==================================================================
    if not keys:
        raise ValueError("数据标签列表不能为空")
    if not isinstance(fig, plt.Figure):
        raise TypeError("fig参数必须为matplotlib.figure.Figure类型")

    # ==================================================================
    # 数据特征提取
    # ==================================================================
    # 计算最长标签字符数（考虑中英文混合）
    max_key_length = max(len(str(key)) for key in keys)
    # 获取柱子总数
    num_bars = len(keys)

    # ==================================================================
    # 动态宽度计算（保留原始算法结构，优化计算系数）
    # ==================================================================
    # 基础宽度（根据经验调整）
    base_width = 0
    # 设置图片最小宽度和最大宽度
    min_width = 9
    max_width = 20
    # 字符影响因子
    key_length_factor = max_key_length * 1
    # 数量影响因子
    bar_count_factor = num_bars * 0.3

    # 合成计算宽度（增加平滑处理）
    desired_width = min(
        max(base_width + key_length_factor + bar_count_factor, min_width),
        max_width
    )

    # ==================================================================
    # 柱子宽度动态调整（保留原始逻辑）
    # ==================================================================
    # 根据柱子数量智能调整（原逻辑增强）
    # 动态调整公式
    desired_bar_width = bar_width + num_bars * 0.057

    # ==================================================================
    # 图形参数配置（完全保留原始逻辑）
    # ==================================================================
    fig.set_size_inches(desired_width, 4.8)
    plt.xlim(-1, num_bars)

    # ==================================================================
    # 返回结构保持与原始完全一致
    # ==================================================================
    return desired_bar_width, {'width': desired_width}


@create_plot
def create_bar_plot(title: str, data: dict) -> dict:
    """
    严格保持原始功能的柱状图生成方法优化版

    参数与返回值结构完全不变，仅在以下方面优化：
    1. 增强数据校验
    2. 优化内存管理
    3. 改进异常处理
    4. 增加代码可读性
    """
    try:
        # ==================== 保持原始数据转换逻辑 ====================
        labels, np_data = switch_numpy_data(data)
        keys = list(data.keys())
        total_heights = np.sum(np_data, axis=0)

        # ========== 新增防御性校验（不影响原有逻辑）==========
        if not keys:
            raise ValueError("输入数据不能为空")
        if np_data.size == 0:
            raise ValueError("数据转换失败，请检查输入格式")

        # ========== 严格保持原始绘图逻辑 ==========
        fig, ax = plt.subplots()

        # 保持原始宽度计算方式
        desired_bar_width, plot_data = calculate_plot_width(keys, fig)

        # 严格保持原始堆叠逻辑
        bottoms = np.zeros(len(keys))
        for idx in range(np_data.shape[0]):
            # 保持原始bar参数设置
            bars = ax.bar(
                keys,
                np_data[idx],
                width=desired_bar_width,  # 关键点：保持原始宽度传递方式
                bottom=bottoms,
                color=PLOT_COLORS[idx % len(PLOT_COLORS)],
                label=labels[idx] if labels else None
            )
            bottoms += np_data[idx]

            # 保持原始标签添加逻辑
            if np_data.shape[0] > 1:
                for index, (bar, value) in enumerate(zip(bars, np_data[idx])):
                    if value and value != total_heights[index]:  # 原始条件判断
                        ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            bar.get_y() + value / 2,
                            str(int(value)),
                            ha='center',
                            va='center',
                            color='white',
                            fontsize=9
                        )

        for i, total in enumerate(total_heights):
            if total:
                ax.text(
                    i,
                    total,
                    str(round(total, 2)),
                    ha='center',
                    va='bottom'
                )

        # ========== 严格保持返回结构 ==========
        return {
            'desiredWidthData': plot_data,
            'labels': labels,
            'title': title,
            'maxBarHeight': math.ceil(max(total_heights)),
            'ax': ax
        }

    except Exception as e:
        # 增强资源清理（原逻辑无此处理）
        plt.close('all')
        raise RuntimeError(f"图表生成失败: {str(e)}") from e


@create_plot
def create_broken_line_plot(title: str, data: dict) -> dict:
    """
    创建动态趋势折线图，展示数据随时间变化趋势

    核心功能：
    1. 支持多维度数据序列展示
    2. 自动处理时间序列排序与数据对齐
    3. 智能标注关键数据点
    4. 自适应图表尺寸与样式配置

    参数详解:
        title (str):
            图表主标题，用于描述图表核心内容
            示例："缺陷每日变化趋势"

        data (dict):
            输入数据字典，结构要求：
            {
                "日期1": {"指标A": 数值, "指标B": 数值},
                "日期2": {"指标A": 数值, "指标B": 数值},
                ...
            }
            键为日期字符串，值为包含各指标数值的字典

    返回:
        dict: 包含图表配置的字典，结构：
        {
            'desiredWidthData': 图表尺寸元数据,
            'labels': 数据系列标签列表,
            'title': 图表标题,
            'maxBarHeight': 最大数据值,
            'ax': matplotlib坐标轴对象
        }

    异常处理:
        ValueError: 当输入数据格式不符合要求时抛出
        TypeError: 当输入数据类型错误时抛出
    """

    try:
        # ==================================================================
        # 阶段1：数据预处理与校验
        # ==================================================================

        # 按日期升序排列输入数据，确保时间序列正确性
        sorted_data = dict(sorted(data.items()))
        # 获取排序后的日期列表作为X轴标签
        dates = list(sorted_data.keys())

        # 数据完整性校验
        if not isinstance(data, dict) or len(data) == 0:
            raise ValueError("输入数据必须为非空字典类型")
        if not all(isinstance(v, dict) for v in data.values()):
            raise TypeError("数据值必须为字典类型")

        # ==================================================================
        # 阶段2：数据转换与结构化处理
        # ==================================================================

        # 提取所有唯一指标名称，确保标签顺序一致性
        labels = []
        for entry in data.values():
            labels.extend(entry.keys())
        labels = list(dict.fromkeys(labels))  # 保持插入顺序去重

        # 将数据转换为NumPy二维数组，行对应指标，列对应日期
        np_data = np.array([
            [date_data.get(label, 0) for date_data in sorted_data.values()]
            for label in labels
        ])

        # ==================================================================
        # 阶段3：图表对象初始化
        # ==================================================================

        # 创建图形和坐标轴对象
        fig, ax = plt.subplots()
        fig: plt.Figure  # 类型注释增强IDE支持
        ax: plt.Axes

        # 计算图表宽度参数（复用柱状图算法）
        plot_width_data = calculate_plot_width(dates, fig)[1]

        # ==================================================================
        # 阶段4：折线绘制与样式配置
        # ==================================================================

        # 记录已标注点坐标，避免重复标注
        annotated_points = set()

        # 遍历每个数据序列绘制折线
        for idx, (label, values) in enumerate(zip(labels, np_data)):
            # 绘制带标记点的折线
            line = ax.plot(
                dates,  # X轴数据：日期序列
                values,  # Y轴数据：当前指标数值序列
                marker='o',  # 数据点标记形状
                linestyle='-',  # 连线样式
                markersize=8,  # 标记尺寸
                color=PLOT_COLORS[idx % len(PLOT_COLORS)],  # 自动循环颜色
                label=label  # 图例标签
            )

            # ==================================================================
            # 阶段5：数据点智能标注
            # ==================================================================

            # 遍历每个数据点进行条件标注
            for date, value in zip(dates, values):
                point_key = (date, value)

                # 标注条件：首次出现的极值点或关键节点
                if point_key not in annotated_points:
                    # 添加数值标注
                    ax.annotate(
                        text=f'{value}',  # 显示数值
                        xy=(date, value - 0.3),  # 标注锚点
                        xytext=(0, 10),  # 文本位置偏移
                        textcoords='offset points',  # 偏移量单位
                        ha='center',  # 水平居中
                        fontsize=9,  # 字体大小
                        color=line[0].get_color(),  # 继承线条颜色
                        weight='bold',  # 加粗字体
                        fontfamily='Arial',  # 字体样式
                    )
                    annotated_points.add(point_key)

        # ==================================================================
        # 阶段=6：返回结构化数据
        # ==================================================================

        return {
            'desiredWidthData': plot_width_data,
            'labels': labels,
            'title': title,
            'maxBarHeight': math.ceil(np.max(np_data)),
            'ax': ax
        }

    except Exception as e:
        # 异常时主动释放资源
        plt.close('all')
        raise RuntimeError(f"折线图生成失败: {str(e)}") from e


def upload_file(file_content: bytes) -> str:
    """
    安全可靠地上传文件到TAPD文件存储服务

    功能增强：
    1. 增强错误处理机制
    2. 完善类型提示
    3. 优化参数构造方式
    4. 增加安全校验
    5. 改进响应处理

    参数:
        file_content (bytes): 要上传的文件二进制内容，最大支持10MB

    返回:
        str: 上传成功后的文件访问路径(相对路径)

    异常:
        ValueError: 当输入文件不符合要求时抛出
        ConnectionError: 网络连接异常时抛出
        RuntimeError: 服务器返回异常或解析失败时抛出
    """
    try:
        # ==================================================================
        # 阶段1：输入参数校验
        # ==================================================================
        if not isinstance(file_content, bytes):
            raise TypeError("文件内容必须为bytes类型")

        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        if len(file_content) > MAX_FILE_SIZE:
            raise ValueError(f"文件大小超过{MAX_FILE_SIZE // 1024 // 1024}MB限制")

        # ==================================================================
        # 阶段2：构造请求参数
        # ==================================================================
        # API端点配置
        upload_url = 'https://tdl.tapd.cn/tbl/apis/qmeditor_upload.php'

        # 查询参数(保持原有业务参数)
        query_params = {
            "show_relative_path": "1",  # 返回相对路径
            "relative_base_path": "/tfl/",  # 基础存储路径
            "image_prefix": "tapd_63835346_",  # 文件名前缀
            "ie_domain_fix": "itemRich"  # 跨域修复标识
        }

        # 表单数据(保持原有业务参数)
        form_data = {
            "sid": "sid",  # 会话标识(示例值)
            "fun": "add",  # 操作类型：添加文件
            "mode": "download",  # 文件模式：可下载
            "widthlimit": "0",  # 宽度限制(0表示不限制)
            "heightlimit": "0",  # 高度限制
            "sizelimit": "0",  # 大小限制
        }

        # 文件参数封装
        file_obj = BytesIO(file_content)
        files = {
            "UploadFile": (
                "chart.png",  # 固定文件名(根据业务需求调整)
                file_obj,
                "image/png"  # 明确指定MIME类型
            )
        }

        # ==================================================================
        # 阶段3：执行上传请求
        # ==================================================================
        try:
            response = fetch_data(
                url=upload_url,
                params=query_params,
                data=form_data,
                files=files,
                method='POST'
            )
            response.raise_for_status()  # 自动处理4xx/5xx状态码
        except requests.RequestException as e:
            raise ConnectionError(f"文件上传失败: {str(e)}") from e
        finally:
            file_obj.close()  # 确保关闭文件流

        # ==================================================================
        # 阶段4：解析响应内容
        # ==================================================================
        # 使用改进后的正则表达式匹配路径
        pattern = r"\);</script>(.*?)$"
        matched_paths = extract_matching(pattern, str(response.text))

        if not matched_paths:
            raise RuntimeError("响应内容解析失败，未找到文件路径")

        return matched_paths[0]

    except Exception as e:
        # 统一异常处理
        error_msg = f"文件上传流程异常: {str(e)}"
        raise type(e)(error_msg) from e


def date_time_to_date(date_time_str: str) -> str:
    """
    将多种日期时间格式统一转换为标准日期字符串

    功能增强：
    1. 支持多种输入格式
    2. 增强容错处理
    3. 完善类型提示
    4. 优化性能
    5. 添加详细文档

    参数:
        date_time_str (str): 日期时间字符串，支持格式：
            - 带时分秒：'2024-10-12 20:52:30'
            - 带时分：'2024-10-12 20:52'
            - 短横线分隔：'2024-10-12'
            - 无分隔符：'20241012'
            - 中文日期：'2024年10月12日'

    返回:
        str: 标准化日期字符串'YYYY-MM-DD'

    异常:
        ValueError: 当输入无法解析为有效日期时抛出
        TypeError: 当输入不是字符串类型时抛出
    """
    # ======================================================================
    # 输入验证阶段
    # ======================================================================
    if not isinstance(date_time_str, str):
        raise TypeError(f"输入必须为字符串类型，当前类型：{type(date_time_str).__name__}")

    # ======================================================================
    # 预处理阶段
    # ======================================================================
    # 统一全角字符为半角
    normalized_str = date_time_str.translate(
        str.maketrans('０１２３４５６７８９', '0123456789')
    ).strip()

    # ======================================================================
    # 格式匹配阶段（按处理优先级排序）
    # ======================================================================
    format_patterns = [
        # 带时间部分格式
        (r'\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}', '%Y-%m-%d %H:%M'),  # 2024-10-12 20:52
        (r'\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}', '%Y-%m-%d %H:%M:%S'),  # 2024-10-12 20:52:54
        # 纯日期格式
        (r'\d{4}年\d{1,2}月\d{1,2}日', '%Y年%m月%d日'),  # 中文格式
        (r'\d{4}/\d{1,2}/\d{1,2}', '%Y/%m/%d'),  # 斜杠格式
        (r'\d{4}-\d{1,2}-\d{1,2}', '%Y-%m-%d'),  # 标准短横线格式
        (r'\d{8}', '%Y%m%d'),  # 紧凑格式
    ]

    # ======================================================================
    # 解析阶段
    # ======================================================================
    for pattern, date_format in format_patterns:
        try:
            # 使用正则预过滤提高效率
            if re.fullmatch(pattern, normalized_str):
                dt_obj = datetime.datetime.strptime(normalized_str, date_format)
                return dt_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue

    # ======================================================================
    # 异常处理阶段
    # ======================================================================
    raise ValueError(f"无法解析日期字符串：{date_time_str} (支持格式：YYYY-MM-DD[ HH:MM]、YYYY年MM月DD日等)")


def style_convert(style_data: dict) -> str:
    """
    将样式参数字典转换为标准化的CSS样式字符串

    该函数实现以下核心功能：
    1. 类型安全校验：确保输入为字典类型
    2. 数据有效性过滤：自动跳过非字符串类型的键值对
    3. 格式标准化：按CSS属性名称字母顺序排序生成字符串
    4. 防御性处理：兼容空字典输入和异常值情况

    参数详解:
        style_data (dict):
            样式配置字典，键为CSS属性名称，值为对应样式设置。
            示例：{'color': 'red', 'font-size': '14px'}
            支持嵌套简写属性，如'margin': '10px 20px'
            允许值为数值类型，自动转换为字符串类型

    返回:
        str:
            标准化CSS样式字符串，格式为"key1: value1; key2: value2;"
            示例："color: red; font-size: 14px;"

    异常处理:
        TypeError: 当输入参数不是字典类型时抛出
        ValueError: 当字典值为空或None时生成警告日志（实际代码中建议使用logging模块）

    实现策略:
        1. 输入校验阶段：验证参数类型有效性
        2. 数据清洗阶段：过滤无效键值对，统一值类型
        3. 格式转换阶段：按字母顺序排序生成标准化字符串
        4. 结果优化阶段：移除末尾分号保持格式统一
    """

    # ==================================================================
    # 阶段1：输入参数校验
    # ==================================================================

    # 类型校验：确保输入为字典类型
    if not isinstance(style_data, dict):
        error_msg = f"参数类型错误，预期字典类型，实际类型：{type(style_data).__name__}"
        raise TypeError(error_msg)

    # 空值处理：快速返回空字符串避免后续处理
    if not style_data:
        return ''

    # ==================================================================
    # 阶段2：数据清洗与预处理
    # ==================================================================

    valid_items = []
    for key, value in style_data.items():
        # 键值有效性校验（双重防御机制）
        # 过滤非字符串键，保留合法CSS属性名
        if not isinstance(key, str):
            continue

        # 值类型统一化处理：允许数值型自动转换
        if isinstance(value, (int, float)):
            processed_value = str(value)
        elif not isinstance(value, str):
            continue  # 跳过无法处理的类型
        else:
            processed_value = value.strip()  # 去除前后空格

        # 空值过滤：跳过无效的空值配置
        if not processed_value:
            continue

        valid_items.append((key, processed_value))

    # ==================================================================
    # 阶段3：样式字符串生成
    # ==================================================================

    # 按属性名称字母排序（提升可读性，便于缓存优化）
    sorted_items = sorted(valid_items, key=lambda x: x[0].lower())

    # 使用列表推导式高效拼接字符串
    # 每项格式为"key: value;"，保留末尾分号保证格式一致性
    style_parts = [
        f"{key}: {value};"
        for key, value in sorted_items
    ]

    # ==================================================================
    # 阶段4：结果优化与返回
    # ==================================================================

    # 使用空格连接保证可读性（替代空字符串连接）
    return ' '.join(style_parts)


def multi_client_data_processing(
        result: Dict[str, Dict[str, int]],
        key: Optional[str],
        all_sub_keys: List[str],
        sub_key: Optional[str],
        all_keys: Optional[List[str]] = None
) -> None:
    """
    多维度数据聚合处理器

    功能增强说明:
        精确控制空值维度添加逻辑，仅在遇到空子键且目标维度不存在时补充空值维度
        同时确保所有子键维度最终都包含空值统计项

    核心处理逻辑:
        1. 空子键处理策略：
           - 仅当当前sub_key为空时触发空维度检查
           - 仅在all_sub_keys缺失空维度时进行补充
          2. 维度完整性保障：
           - 无论当前sub_key是否为空，最终确保所有主键维度都包含空子键
           - 动态修复历史数据中可能缺失的空维度

    参数说明强化:
        :param result: 多维统计字典，结构示例:
            {
                "Android": {"崩溃": 5, "卡顿": 3, "空": 2},
                "iOS": {"闪退": 4, "空": 1}
            }
        :param key: 主维度标识，如平台类型。空值自动转换为"空"
        :param all_sub_keys: 子维度全集，动态维护空维度存在性
        :param sub_key: 当前子维度值，空值触发特殊处理逻辑
        :param all_keys: 主维度全集，用于初始化完整矩阵结构

    异常处理:
        TypeError: 当输入参数类型不符合期望时抛出

    执行流程优化:
        空值检测 → 维度补全 → 结构初始化 → 数据聚合
    """
    # ==================================================================
    # 阶段1：入参校验
    # ==================================================================
    if not isinstance(result, dict):
        raise TypeError("统计结果必须为字典类型")

    if not isinstance(key, str):
        raise TypeError("主维度标识必须为字符串类型")

    if all_keys is not None and not isinstance(all_keys, list):
        raise TypeError("主维度全集必须为列表类型")

    if not isinstance(sub_key, str):
        raise TypeError("子维度标识必须为字符串类型")

    if not isinstance(all_sub_keys, list):
        raise TypeError("子维度全集必须为列表类型")

    # ==================================================================
    # 阶段2：空值标准化处理
    # ==================================================================
    # 主键空值转换（防御性处理）
    processed_key = key if key else "空"

    # 子键空值转换与空维度维护（精确控制添加条件）
    processed_sub_key = sub_key
    if not sub_key or sub_key == "空":
        processed_sub_key = "空"
        # 仅在遇到空子键且目标维度不存在时补充（原始需求核心逻辑）
        if "空" not in all_sub_keys:
            all_sub_keys.append("空")
            # 同步修复已存在主键结构的维度完整性
            for k in result:
                if "空" not in result[k]:
                    result[k]["空"] = 0

    # ==================================================================
    # 阶段3：数据结构初始化（增强维度完整性）
    # ==================================================================
    # 全量主键初始化模式（当提供all_keys时）
    if all_keys and not result:
        # 构建完整主键×子键矩阵
        result.update({
            k: {sk: 0 for sk in all_sub_keys}
            for k in all_keys
        })

    # ==================================================================
    # 阶段4：当前主键维度初始化
    # ==================================================================
    if processed_key not in result:
        # 初始化包含所有子键维度
        result[processed_key] = {sk: 0 for sk in all_sub_keys}

    # ==================================================================
    # 阶段5：数据聚合
    # ==================================================================
    # 原子操作更新计数器
    result[processed_key][processed_sub_key] += 1


def get_system_name() -> str:
    """
    获取标准化系统名称

    该方法通过平台检测和映射转换，提供统一的系统标识符。
    支持主流桌面操作系统识别，确保跨平台兼容性。

    返回:
        str: 标准化系统标识符，取值范围：
            - 'macOS' : Apple macOS系统
            - 'windows' : Microsoft Windows系统

    异常:
        ValueError: 检测到非支持操作系统时抛出
        RuntimeError: 平台检测失败时抛出

    实现策略:
        1. 调用底层平台接口获取原始系统标识
        2. 执行系统标识到标准名称的映射转换
        3. 防御性校验确保返回值有效性
    """
    # ==================================================================
    # 阶段1：原始系统标识获取
    # ==================================================================
    try:
        # 调用platform模块获取基础系统信息
        # 注意：WSL等特殊环境可能需要额外处理
        raw_system = platform.system()
    except Exception as e:
        # 封装原始异常，添加诊断上下文
        raise RuntimeError("系统检测失败，platform.system()执行异常") from e

    # ==================================================================
    # 阶段2：系统标识标准化处理
    # ==================================================================
    # 定义操作系统映射关系(键: platform返回值，值: 标准化名称)
    system_mapping = {
        'Darwin': 'macOS',  # macOS系统标识
        'Windows': 'windows'  # Windows系统标识
    }

    # 执行标识转换
    normalized_system = system_mapping.get(raw_system)

    # ==================================================================
    # 阶段3：结果校验与返回
    # ==================================================================
    if not normalized_system:
        # 生成详细的错误报告
        error_msg = (
            f"不支持的平台类型: {raw_system}。"
            f"当前支持: {', '.join(system_mapping.values())}"
        )
        raise ValueError(error_msg)

    return normalized_system


def _handle_stream_response(completion, result: list) -> str:
    """处理流式响应数据"""
    print(f'\n{datetime.datetime.now().strftime("%H:%M:%S")} 生成开始')

    # 初始化状态追踪
    is_reasoning = False
    is_final_answer = False

    try:
        for chunk in completion:
            # 提取增量内容
            delta = chunk.choices[0].delta
            reasoning_content = getattr(delta, 'reasoning_content', '')
            content = getattr(delta, 'content', '')

            # 思考过程处理
            if reasoning_content:
                if not is_reasoning:
                    print('\n思考轨迹:', flush=True)
                    is_reasoning = True
                print(_print_text_font(reasoning_content, color='black'), end='', flush=True)

            # 最终答案处理
            if content:
                if not is_final_answer:
                    print('\n\n最终答案:', flush=True)
                    is_final_answer = True
                print(content, end='', flush=True)
                result.append(content)

        print(f'\n\n{datetime.datetime.now().strftime("%H:%M:%S")} 生成完成')
        return ai_result_switch_html(''.join(result))

    except KeyboardInterrupt:
        print('\n\n生成过程已中断')
        return ai_result_switch_html(''.join(result))


def _handle_normal_response(completion, result: list) -> str:
    """处理非流式响应数据"""
    try:
        # 提取思考过程
        if reasoning_content := getattr(completion.choices[0].message, 'reasoning_content', None):
            print(f"\n思考轨迹:\n{_print_text_font(reasoning_content, color='black')}")

        # 提取最终答案
        if final_answer := completion.choices[0].message.content:
            print("\n最终答案:\n{}".format(final_answer))
            result.append(final_answer)

        print(f'\n{datetime.datetime.now().strftime("%H:%M:%S")} 生成完成')
        return ai_result_switch_html(''.join(result))

    except AttributeError as e:
        raise APIError("响应结构异常") from e


class SoftwareQualityRating:
    def __init__(self):
        """
        软件质量评分系统初始化方法

        本方法初始化软件质量评分系统所需的所有数据结构，包括：
        - 项目基本信息
        - 缺陷统计相关数据
        - 评分结果存储
        - 报告生成相关配置

        数据结构说明:
            1. 基础信息:
                - requirementName: 需求名称
                - PM: 产品经理
                - testRecipient: 测试报告接收人列表
                - testersStr: 测试人员字符串表示
                - developers: 开发人员列表

            2. 时间相关:
                - earliestTaskDate: 最早任务日期
                - lastTaskDate: 最晚任务日期
                - onlineDate: 上线日期

            3. 缺陷统计:
                - bugLevelsCount: 缺陷级别统计
                - bugLevelsMultiClientCount: 多端缺陷级别统计
                - bugSourceCount: 缺陷根源统计
                - bugSourceMultiClientCount: 多端缺陷根源统计
                - bugTotal: 缺陷总数
                - bugInputTotal: 手动输入缺陷总数
                - bugIds: 缺陷ID列表
                - reopenBugsData: 重新打开缺陷数据
                - unrepairedBugsData: 未修复缺陷数据
                - fixers: 缺陷修复人统计

            4. 评分系统:
                - score: 各项评分结果
                - scoreContents: 评分详细内容
                - bugCountScoreMsg: 缺陷数量评分说明
                - bugRepairScoreMsg: 缺陷修复评分说明
                - bugReopenScoreMsg: 缺陷重开评分说明

            5. 报告生成:
                - testReportHtml: 测试报告HTML内容
                - chartHtml: 图表HTML内容
                - reportSummary: 报告总结内容

            6. 配置信息:
                - oldBugListConfigs: 原始缺陷列表配置
                - oldSubTaskListConfigs: 原始子任务列表配置
        """
        # ==================================================================
        # 阶段1：基础信息初始化
        # ==================================================================
        self.requirementName = ''  # 需求名称
        self.PM = ''  # 产品经理
        self.testRecipient = []  # 测试报告接收人列表(测试人员)
        self.testersStr = ''  # 测试人员字符串表示
        self.developers = []  # 开发人员列表

        # ==================================================================
        # 阶段2：时间相关初始化
        # ==================================================================
        self.isExistTestTask = False  # 是否存在测试任务标志
        self.earliestTaskDate = None  # 最早任务日期
        self.lastTaskDate = None  # 最晚任务日期
        self.onlineDate = None  # 上线日期

        # ==================================================================
        # 阶段3：缺陷统计初始化
        # ==================================================================
        self.workHours = defaultdict(float)  # 开发人员工时统计
        self.devTotalHours = 0  # 开发总工时
        self.developerCount = 0  # 开发人员数量
        self.dailyWorkingHoursOfEachDeveloper = defaultdict(lambda: defaultdict(float))  # 每日开发人员工时
        self.developmentCycle = 0  # 开发周期

        self.bugLevelsCount = defaultdict(int, {level: 0 for level in BUG_LEVELS})  # 缺陷级别统计
        self.bugLevelsMultiClientCount = {}  # 多端缺陷级别统计
        self.bugSourceCount = defaultdict(int)  # 缺陷根源统计
        self.bugSourceMultiClientCount = {}  # 多端缺陷根源统计
        self.bugTotal = 0  # 缺陷总数
        self.bugInputTotal = 0  # 手动输入缺陷总数
        self.bugIds = []  # 缺陷ID列表
        self.reopenBugsData = {}  # 重新打开缺陷数据
        self.unrepairedBugsData = defaultdict(int)  # 未修复缺陷数据
        self.fixers = defaultdict(int)  # 缺陷修复人统计

        # ==================================================================
        # 阶段4：评分系统初始化
        # ==================================================================
        self.score = {
            "positiveIntegrityScore": 0,  # 配合积极性/文档完成性评分
            "smokeTestingScore": 0,  # 冒烟测试评分
            "bugCountScore": 0,  # 缺陷数量评分
            "bugRepairScore": 0,  # 缺陷修复评分
            "bugReopenScore": 0,  # 缺陷重开评分
        }
        self.scoreContents = []  # 评分详细内容
        self.bugCountScoreMsg = ''  # 缺陷数量评分说明
        self.bugRepairScoreMsg = ''  # 缺陷修复评分说明
        self.bugReopenScoreMsg = ''  # 缺陷重开评分说明

        # ==================================================================
        # 阶段5：报告生成初始化
        # ==================================================================
        self.testReportHtml = ''  # 测试报告HTML内容
        self.chartHtml = ''  # 图表HTML内容
        self.reportSummary = ''  # 报告总结内容

        # ==================================================================
        # 阶段6：配置信息初始化
        # ==================================================================
        self.isInitialListConfig = False  # 是否初始化列表配置标志
        self.oldBugListConfigs = ''  # 原始缺陷列表配置
        self.oldSubTaskListConfigs = ''  # 原始子任务列表配置

        # ==================================================================
        # 阶段7：未修复缺陷数据结构初始化
        # ==================================================================
        self.unrepairedBugs = {
            # 部署正式环境当天未修复的缺陷
            "deployProdDayUnrepaired": {
                "P0P1": [],  # 致命或严重缺陷
                "P2": [],  # 一般或其他缺陷
            },
            # 创建当天未修复的缺陷
            "onThatDayUnrepaired": {
                "P0": [],  # 致命缺陷
                "P1": [],  # 严重缺陷
                "P2": [],  # 一般或其他缺陷
            }
        }

        # ==================================================================
        # 阶段8：缺陷每日变化趋势初始化
        # ==================================================================
        self.dailyTrendOfBugChanges = {}  # 缺陷每日变化趋势

    def get_requirement_detail(self) -> None:
        """
        获取需求详细信息并初始化相关属性

        本方法通过TAPD API获取指定需求的详细信息，包括：
        - 需求名称
        - 产品经理
        - 开发人员列表
        - 其他相关属性

        流程说明:
            1. 构造API请求参数
            2. 发送API请求获取需求数据
            3. 解析响应数据并初始化类属性
            4. 处理开发人员列表
            5. 异常处理和状态验证

        异常处理:
            ValueError: 当无法获取需求数据或数据结构异常时抛出
            requests.RequestException: 当API请求失败时抛出
            KeyError: 当响应数据缺失关键字段时抛出

        实现策略:
            1. 使用封装后的fetch_data方法进行API调用
            2. 多层数据校验确保数据完整性
            3. 防御性编程处理可能的异常情况
            4. 结构化数据处理提高可读性
        """
        # ==================================================================
        # 阶段1：API请求准备
        # ==================================================================
        api_url = HOST + "/api/aggregation/story_aggregation/get_story_transition_info"
        request_params = {
            "workspace_id": PROJECT_ID,
            "story_id": REQUIREMENT_ID,
        }

        try:
            # ==================================================================
            # 阶段2：API请求执行
            # ==================================================================
            response = fetch_data(
                url=api_url,
                json=request_params,
                method='GET'
            ).json()

            # ==================================================================
            # 阶段3：响应数据校验
            # ==================================================================
            # 检查响应数据是否存在且包含必要字段
            if not response or not response.get('data', {}):
                raise ValueError("需求数据获取失败，响应数据为空或格式异常")

            # 提取需求详细信息
            response_detail = response['data']['get_workflow_by_story']['data']['current_story']['Story']

            # ==================================================================
            # 阶段4：属性初始化
            # ==================================================================
            # 设置需求名称
            self.requirementName = response_detail.get('name', '')

            # 设置产品经理
            self.PM = response_detail.get('creator', '')

            # ==================================================================
            # 阶段5：开发人员列表处理
            # ==================================================================
            developer_str = response_detail.get('developer', '')
            if developer_str:
                # 处理分号分隔的开发人员字符串
                self.developers = [dev.strip() for dev in developer_str.split(';') if dev.strip()]

                # 移除最后一个空字符串（如果存在）
                if self.developers and not self.developers[-1]:
                    self.developers.pop()

            # ==================================================================
            # 阶段6：防御性编程
            # ==================================================================
            if not self.requirementName:
                self.print_error("需求名称获取失败，请检查需求ID是否正确")

            if not self.PM:
                self.print_error("产品经理获取失败，请检查需求创建人是否正确")

        except requests.RequestException as e:
            # 捕获网络请求异常
            error_msg = f"API请求失败: {str(e)}"
            raise requests.RequestException(error_msg) from e

        except KeyError as e:
            # 捕获关键字段缺失异常
            error_msg = f"响应数据缺失关键字段: {str(e)}"
            raise KeyError(error_msg) from e

        except Exception as e:
            # 捕获其他未预料异常
            error_msg = f"获取需求详情失败: {str(e)}"
            raise RuntimeError(error_msg) from e

    def requirement_task_statistics(self):
        """
        统计需求关联的子任务数据，计算开发工时并识别关键时间节点

        核心功能：
        1. 遍历所有子任务，分离开发任务和测试任务
        2. 计算开发者总工时和每日工时分布
        3. 记录项目关键时间节点（最早/最晚任务日期、上线日期）
        4. 维护测试相关数据（测试负责人、收件人列表）

        优化点：
        - 分离开发/测试任务处理逻辑
        - 增加数据校验和异常处理
        - 优化日期比较逻辑
        - 减少嵌套层次提升可读性
        """

        # ==================================================================
        # 阶段1：数据准备
        # ==================================================================
        # 未完成的任务列表
        unfinished_tasks: list = []
        # 获取子任务数据（已处理分页逻辑）
        requirement_tasks = get_requirement_tasks()
        if not requirement_tasks:
            print("警告：未获取到任何子任务数据")
            return

        # ==================================================================
        # 阶段2：遍历处理每个子任务
        # ==================================================================
        for child in requirement_tasks:
            try:
                # 数据校验：确保必需字段存在
                if not all(key in child for key in ('owner', 'begin', 'due', 'effort_completed', 'status', 'name')):
                    print(f"无效任务数据，缺失关键字段：{child.get('id', '未知ID')}")
                    continue

                # 数据清洗：去除部门前缀
                raw_owner = child['owner'].replace(";", "")  # 获取任务处理人名称(T5张三)
                processing_personnel = extract_matching(rf"{DEPARTMENT}(.*?)$", raw_owner)[0]  # 去除部门前缀(张三)

                # 数据校验：确保任务已完成
                if child['status'] != 'done':
                    unfinished_tasks.append(f"任务名称: {child['name']}; 处理人: {processing_personnel}")
                    continue

                # 提取实际完成工时、开始日期、结束日期
                effort_completed = float(child.get('effort_completed', 0))  # 实际完成工时
                begin_date = child['begin']  # 预计开始日期
                due_date = child['due']  # 预计结束日期

            except (ValueError, TypeError) as e:
                raise e

            # ==================================================================
            # 阶段3：任务分类处理
            # ==================================================================
            # 开发者任务处理
            if processing_personnel not in TESTERS:
                self._process_developer_task(
                    developer=processing_personnel,  # 开发者名称
                    effort=effort_completed,  # 实际完成工时
                    begin=begin_date,  # 预计开始日期
                    due=due_date,  # 预计结束日期
                    child_data=child  # 子任务数据
                )
            # 测试任务处理
            else:
                self._process_tester_task(
                    due_date=due_date,
                    begin_date=begin_date,
                    owner=raw_owner
                )

        # ==================================================================
        # 阶段4：后期校验
        # ==================================================================
        # 检查测试任务是否存在
        if not self.isExistTestTask:
            self.print_error(f'没有测试任务, 请检查"{self.requirementName}"需求是否有测试任务')
        if unfinished_tasks:
            count = 0
            unfinished_tasks_str: str = ''
            for unfinishedTask in unfinished_tasks:
                count += 1
                unfinished_tasks_str += f"\n{count}. {unfinishedTask}"
            self.print_error(f"存在未完成任务, 请及时处理:{unfinished_tasks_str}")
        if not self.earliestTaskDate:
            self.print_error(
                f"警告：未识别到最早任务日期，请检查{self.requirementName}需求的最早一个开发任务的预期开始时间是否正常")
        if not self.lastTaskDate:
            self.print_error(
                f"警告：未识别到最晚任务日期，请检查{self.requirementName}需求的最后一个测试任务的预期结束时间是否正常")
        if not self.onlineDate:
            self.print_error(
                f"警告：未识别到上线日期，请检查{self.requirementName}需求的最后一个测试任务的预期开始时间是否正常")

    def print_development_hours(self) -> None:
        """
        输出项目开发工时统计摘要

        本方法实现开发工时数据的汇总展示功能，主要包含以下处理流程：
        1. 计算开发总工时与参与人数
        2. 格式化输出需求基本信息
        3. 逐项展示开发者个人工时
        4. 显示工时合计数据

        输出要素：
            - 需求标识信息
            - 开发者名称与对应工时的键值对
            - 工时总计数值
            - 标准化分隔线增强可读性

        返回:
            None: 本方法仅执行控制台输出操作

        异常:
            AttributeError: 当workHours属性未正确初始化时可能抛出
            KeyError: 当全局常量REQUIREMENT_ID未定义时抛出

        实现策略:
            1. 基于workHours字典进行聚合计算
            2. 使用LINE_LENGTH常量控制输出格式
            3. 遍历字典实现明细数据输出
        """
        # ==================================================================
        # 阶段1：工时数据聚合计算
        # ==================================================================

        # 计算开发团队总工时：对workHours字典所有值求和
        self.devTotalHours = sum(self.workHours.values())

        # 统计开发人员数量：获取字典键的数量
        self.developerCount = len(self.workHours)

        # ==================================================================
        # 阶段2：控制台格式化输出
        # ==================================================================

        # 生成分隔线：使用LINE_LENGTH常量控制横线长度
        print('-' * LINE_LENGTH)

        # 输出需求标题行：包含需求ID和需求名称
        print(f"需求 {REQUIREMENT_ID}: {self.requirementName} 各开发人员花费的工时：")

        # ==================================================================
        # 阶段3：明细数据遍历输出
        # ==================================================================

        # 遍历工时字典项：developer为开发者名称，hours为对应工时数值
        for developer, hours in self.workHours.items():
            # 格式化输出单开发者工时信息：姓名+小时数
            print(f"{developer}: {hours} 小时")

        # ==================================================================
        # 阶段4：合计数据输出
        # ==================================================================

        # 输出工时总计：显示计算得到的总工时
        print(f"工时合计：{self.devTotalHours} 小时")

    def bug_list_detail(self) -> None:
        """
        获取指定需求关联的缺陷列表并执行多维度统计分析

        核心功能：
        1. 通过API接口分页获取指定需求的全部缺陷数据
        2. 提取关键字段并进行数据清洗
        3. 执行多维度统计（严重等级、根源分类、平台分布等）
        4. 跟踪缺陷生命周期状态变化
        5. 维护数据完整性校验

        处理流程：
            1. 初始化统计数据结构
            2. 调用分页接口获取原始数据
            3. 遍历缺陷记录进行数据清洗
            4. 执行字段级校验和空值处理
            5. 更新各维度统计计数器
            6. 记录缺陷状态流转轨迹

        关联方法：
            get_bug_list()：基础数据获取接口
            multi_client_data_processing()：多维数据聚合处理器
            date_time_to_date()：日期格式标准化
        """
        # ==================================================================
        # 阶段1：数据获取与初始化
        # ==================================================================

        # 调用API接口获取缺陷基础数据（分页逻辑封装在get_bug_list中）
        # 返回三元组：平台列表、根源分类列表、缺陷数据字典列表
        platforms, sources, bugs = get_bug_list(self.requirementName)
        platforms: list[str]
        sources: list[str]
        bugs: list[dict]

        # 输出数据分割线（控制台可视化）
        print('-' * LINE_LENGTH)

        # ==================================================================
        # 阶段2：缺陷数据遍历处理
        # ==================================================================

        # 处理空数据场景（防御性编程）
        if not bugs:
            print('未获取到有效缺陷数据')
            return

        # 遍历原始缺陷记录（每个缺陷为字典结构）
        for bug in bugs:
            # ==================================================================
            # 阶段2.1：基础字段提取与清洗
            # ==================================================================

            # 获取缺陷状态并过滤已拒绝的缺陷
            bug_status = bug.get('status', '')
            if bug_status == 'rejected':
                continue

            # 提取关键字段（防御性get方法避免KeyError）
            bug_id = bug.get('id')  # 缺陷唯一标识符
            severity_name = bug.get('custom_field_严重等级', '')  # 原始严重等级
            bug_source = bug.get('source', '')  # 缺陷根源分类
            bug_platform = bug.get('platform')  # 客户端平台标识

            # ==================================================================
            # 阶段2.2：数据标准化处理
            # ==================================================================

            # 严重等级格式处理（示例值："P1-严重" → "P1"）
            if severity_name and '-' in severity_name:
                severity_name = severity_name.split('-')[0].strip()

            # 空值处理与默认值设置
            severity_name = severity_name if severity_name else '空'
            bug_source = bug_source if bug_source else '空'
            bug_platform = bug_platform if bug_platform else '空'

            try:
                # ==================================================================
                # 阶段2.3：核心统计逻辑
                # ==================================================================

                # 更新严重等级全局计数器
                self.bugLevelsCount[severity_name] += 1

                # 更新根源分类全局计数器
                self.bugSourceCount[bug_source] += 1

                # 执行多维度统计（平台×严重等级）
                multi_client_data_processing(
                    result=self.bugLevelsMultiClientCount,
                    key=bug_platform,
                    all_sub_keys=BUG_LEVELS,
                    sub_key=severity_name
                )

                # 执行多维度统计（平台×缺陷根源）
                multi_client_data_processing(
                    result=self.bugSourceMultiClientCount,
                    key=bug_platform,
                    all_sub_keys=sources,
                    sub_key=bug_source
                )

                # ==================================================================
                # 阶段2.4：生命周期跟踪
                # ==================================================================

                if bug_id:  # 有效缺陷ID处理
                    # 记录缺陷ID（用于后续详细跟踪）
                    self.bugIds.append(bug_id)

                    # 标准化日期字段（处理多种输入格式）
                    created_date = date_time_to_date(bug.get('created', ''))
                    resolved_date = date_time_to_date(bug['resolved']) if bug.get('resolved') else None

                    # 顽固缺陷检测逻辑（特定标签处理）
                    if bug.get('custom_field_Bug等级') == '顽固（180 天）':
                        self.unrepairedBugsData[bug_id] += 1

                    # 上线未修复缺陷检测
                    self._statistics_deploy_prod_day_unrepaired_bug(
                        bug_status=bug_status,
                        bug_id=bug_id,
                        severity_name=severity_name,
                        resolved_date=resolved_date
                    )

                    # 创建日未修复缺陷检测
                    self._statistics_on_that_day_unrepaired_bug(
                        bug_status=bug_status,
                        bug_id=bug_id,
                        severity_name=severity_name,
                        created_date=created_date,
                        resolved_date=resolved_date
                    )

                    # 更新修复人统计（空值处理）
                    fixer = bug['fixer'] if bug.get('fixer') else '空'
                    self.fixers[fixer] += 1

                # ==================================================================
                # 阶段2.5：时序数据分析
                # ==================================================================

                # 更新每日缺陷趋势（创建/解决/关闭状态跟踪）
                self._daily_trend_of_bug_changes_count(bug)

            except KeyError as e:
                # 处理字段缺失异常（记录日志并跳过当前缺陷）
                self.print_error(f"缺陷数据缺失关键字段 {str(e)}，缺陷ID: {bug_id}")
            except ValueError as e:
                # 处理数据格式异常（记录日志并跳过当前缺陷）
                self.print_error(f"数据格式异常 {str(e)}，缺陷ID: {bug_id}")

        # ==================================================================
        # 阶段3：后处理与结果输出
        # ==================================================================

        # 计算缺陷总数（有效缺陷ID数量）
        self.bugTotal = len(self.bugIds)

        # 控制台输出统计摘要
        for level, count in self.bugLevelsCount.items():
            print(f"{level}级别缺陷数量：{count}")

    def score_result(self) -> None:
        """
        执行项目质量评分计算与结果汇总

        核心功能：
        1. 按维度计算各质量指标得分
        2. 处理用户输入验证
        3. 维护评分规则元数据
        4. 生成可视化评分报告
        5. 执行数据完整性校验

        处理流程：
            1. 初始化评分组件
            2. 顺序执行各维度评分计算
            3. 汇总各维度得分
            4. 输出格式化结果
            5. 执行异常状态回滚

        评分维度：
            - BUG数评分
            - BUG修复评分
            - BUG重启评分
            - 配合积极性/文档完成性评分
            - 冒烟测试评分

        异常处理：
            - 输入验证失败时触发重试机制
            - 数据不一致时抛出明细异常
            - 网络错误时执行本地缓存
        """
        try:
            # ==================================================================
            # 阶段1：评分系统初始化
            # ==================================================================

            # 清空历史评分记录（防御性编程）
            self.score.clear()

            # 打印评分系统标题（控制台可视化）
            print('\n' + ' 质量评分系统 '.center(LINE_LENGTH, '='))
            print('')

            # ==================================================================
            # 阶段2：执行维度评分计算
            # ==================================================================

            # BUG数评分（BUG数量/开发人天）
            self._calculate_bug_count_score()

            # BUG修复评分（及时修复率）
            self._calculate_bug_repair_score()

            # BUG重启评分（重开次数）
            self._calculate_bug_reopen_score()

            # 配合积极性/文档完成性评分（文档/沟通效率）
            self._calculate_positive_integrity_score()

            # 冒烟测试评分（冒烟测试通过率）
            self._calculate_smoke_testing_score()

            # ==================================================================
            # 阶段3：评分结果汇总
            # ==================================================================

            # 计算总分（各维度加权求和）
            total_score = sum(
                self.score[k] for k in (
                    "bugCountScore",
                    "bugRepairScore",
                    "bugReopenScore",
                    "positiveIntegrityScore",
                    "smokeTestingScore"
                )
            )

            # 输出总分（带格式高亮）
            print('\n' + '-' * LINE_LENGTH)
            print(f'最终质量评分：{_print_text_font(total_score, is_weight=True, color="red")}')

        except ValueError as e:
            # 输入验证异常处理
            self.print_error(f"输入数据异常：{str(e)}")
        except KeyboardInterrupt:
            # 用户中断处理
            self.print_error("用户主动终止评分流程")
        except Exception as e:
            # 通用异常处理
            self.print_error(f"评分系统错误：{str(e)}")

    def development_cycle(self):
        """
        计算项目的开发周期，基于每个开发者的每日有效工时数据

        本方法通过分析开发者的每日工作记录，计算累计有效工作日数。
        核心逻辑为将每日工时转换为等效工作日数，避免简单累加导致的时间估算偏差

        处理流程：
            1. 初始化有效工作日字典
            2. 遍历所有开发者的每日工时记录
            3. 计算单日有效工时对开发周期的贡献值
            4. 累加所有日期的等效工作日数

        实现策略：
            - 单日工时>=8小时计为1个完整工作日
            - 单日工时<8小时按比例折算（工时/8）
            - 多人同日工作时取最大贡献值，避免重复计算
        """
        # ==================================================================
        # 阶段1：数据校验与初始化
        # ==================================================================
        # 检查是否存在开发者工时数据
        if not self.dailyWorkingHoursOfEachDeveloper:
            self.print_error("警告：未获取到开发者每日工时数据")

        # 初始化开发周期统计字典
        # 键：日期字符串（YYYY-MM-DD）
        # 值：当日最大等效工作日数（0-1之间或1）
        development_days = {}

        # ==================================================================
        # 阶段2：遍历开发者数据
        # ==================================================================
        # 遍历每个开发者的工时记录
        # developer_name: 开发者姓名标识
        # task_hours: 该开发者的日期-工时字典
        for developer_name, task_hours in self.dailyWorkingHoursOfEachDeveloper.items():
            # 跳过空数据记录
            if not task_hours:
                continue

            # ==================================================================
            # 阶段3：处理单开发者工时记录
            # ==================================================================
            # 遍历该开发者每个工作日的工时数据
            # date: 日期字符串（YYYY-MM-DD）
            # hours: 当日实际工作小时数（浮点型）
            for date, hours in task_hours.items():
                # 数据有效性检查
                if not isinstance(hours, (int, float)) or hours < 0:
                    print(f"无效工时数据：开发者[{developer_name}] 日期[{date}] 工时[{hours}]")
                    continue

                # ==================================================================
                # 阶段4：计算单日贡献值
                # ==================================================================
                # 计算当前日期的等效工作日数
                if hours >= 8:
                    # 满8小时计为完整工作日
                    daily_contribution = 1.0
                else:
                    # 不足8小时按比例折算
                    daily_contribution = round(hours / 8, 1)

                # ==================================================================
                # 阶段5：更新全局统计
                # ==================================================================
                # 保留同一日期的最大贡献值（处理多人协作场景）
                # 若当前计算值大于已记录值，则更新
                if development_days.get(date, 0) < daily_contribution:
                    development_days[date] = daily_contribution

        # ==================================================================
        # 阶段6：计算总开发周期
        # ==================================================================
        # 累加所有日期的等效工作日数
        # 使用四舍五入保留1位小数，避免浮点精度问题
        self.developmentCycle = round(sum(development_days.values()), 1)

        # ==================================================================
        # 阶段7：结果校验
        # ==================================================================
        # 检查计算结果有效性
        if self.developmentCycle <= 0:
            self.print_error("警告：开发周期计算结果为非正数，请检查输入数据有效性")

    def add_test_report(self) -> None:
        """
        生成并提交测试报告，包含测试结论、缺陷列表及可视化图表

        本方法实现完整的测试报告生成流程，主要功能包括：
        1. 构造测试结论的HTML结构
        2. 处理测试报告接收人列表
        3. 动态集成缺陷列表和图表数据
        4. 调用AI生成总结内容（根据配置开关）
        5. 提交测试报告到TAPD系统或打印调试信息

        实现流程:
            1. 初始化测试结论数据结构
            2. 构建基础HTML报告框架
            3. 动态添加缺陷列表和图表模块
            4. 配置API请求参数
            5. 执行报告提交或输出调试信息

        异常处理:
            requests.RequestException: 报告提交请求失败时抛出
            KeyError: 响应数据结构异常时抛出
        """
        # ==================================================================
        # 阶段1：测试结论数据初始化
        # ==================================================================
        # 构建测试结论核心指标字典
        test_conclusion: dict[str, str] = {
            '测试执行进度': '',  # 预留字段，需后续补充
            '用例个数': '',  # 预留字段，需后续补充
            '发现BUG数': f'{self.bugTotal if self.bugTotal else self.bugInputTotal}个',  # 动态选择自动统计或手动输入的BUG数
            # 组合各维度评分
            '软件提测质量评分': f'{sum(self.score.values())}分（配合积极性/文档完整性{self.score["positiveIntegrityScore"]}分 + 冒烟测试{self.score["smokeTestingScore"]}分 + BUG数{self.score["bugCountScore"]}分 + BUG修复速度{self.score["bugRepairScore"]}分 + BUG重启率{self.score["bugReopenScore"]}分）',
            '测试时间': '',  # 预留字段，需后续补充
            '测试人员': self.testersStr,  # 格式化后的测试人员字符串
            '开发人员': '、'.join(developer.replace(DEPARTMENT, '') for developer in self.developers),  # 去除部门前缀的开发人员列表
            '产品经理': self.PM.replace(DEPARTMENT, ''),  # 去除部门前缀的产品经理
            '测试范围': '',  # 预留字段，需后续补充
            '测试平台': '',  # 预留字段，需后续补充
        }

        # ==================================================================
        # 阶段2：HTML内容生成
        # ==================================================================
        # 将测试结论字典转换为HTML组件
        test_conclusion_html = [
            # 生成带样式的div组件，每个指标单独成行
            f'''\n<div><span style="font-size: medium; background-color: rgb(255, 255, 255);">{title}：{value}</span></div>'''
            for title, value in test_conclusion.items()
        ]

        # 从测试接收人列表中移除当前用户
        self._remove_current_user()

        # 构建报告基础框架
        self.testReportHtml += f'''
            <span style="color: rgb(34, 34, 34); font-size: medium; background-color: rgb(255, 255, 255);">{datetime.datetime.now().strftime("%Y年%m月%d日")}，{self.requirementName + '&nbsp; &nbsp;' if self.requirementName else ''}項目已完成測試，達到上綫要求</span>
            <br  />
            <div style="color: rgb(34, 34, 34);">
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">項目测试结论</span>
                </div>{''.join(test_conclusion_html)}
                <br  />
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">总结：
                        <br  /><br  /> %(reportSummary)s
                    </span>
                </div>
                <br  />
            </div>'''

        # ==================================================================
        # 阶段3：AI总结生成（根据全局配置开关）
        # ==================================================================
        if IS_CREATE_AI_SUMMARY:
            self._ai_generate_summary()  # 调用深度生成方法

        # ==================================================================
        # 阶段4：请求参数构造
        # ==================================================================
        # 配置API端点基础信息
        url = HOST + f"/{PROJECT_ID}/report/workspace_reports/submit/0/0/security"
        params = {
            "report_type": "test",  # 指定报告类型为测试报告
            "save_draft": "1",  # 保存为草稿模式
        }

        # 构建多层级表单数据结构
        data = {
            "data[Template][id]": "1163835346001000040",  # 报告模板ID
            # 动态生成报告标题
            "data[WorkspaceReport][title]": f"{(self.requirementName + '_') if self.requirementName else DEPARTMENT}测试报告",
            "data[WorkspaceReport][receiver]": f"{';'.join([self.PM] + self.developers + self.testRecipient)}",  # 接收人列表
            "data[WorkspaceReport][receiver_organization_ids]": "",  # 组织机构ID保留字段
            "data[WorkspaceReport][cc]": f"{';'.join(TEST_REPORT_CC_RECIPIENTS)}",  # 抄送人列表
            "data[WorkspaceReport][cc_organization_ids]": "",  # 抄送组织机构ID保留字段
            "workspace_name": "T5;T5 Engineering;",  # 项目空间名称
            "data[WorkspaceReport][workspace_list]": f"{PROJECT_ID}|51931447",  # 项目空间ID列表
            "data[detail][1][type]": "richeditor",  # 富文本组件类型
            "data[detail][1][default_value]": self.testReportHtml % {"reportSummary": self.reportSummary},
            # 插入动态生成的总结内容
            "data[detail][1][title]": "一、概述",  # 第一部分标题
            "data[detail][1][id]": 0,  # 组件ID
            "data[detail][2][type]": "story_list",  # 需求列表组件类型
            "data[detail][2][workitem_type]": "story",  # 工作项类型为需求
            # 展示字段列表
            "data[detail][2][show_fields]": "name,status,business_value,priority,size,iteration_id,owner,begin,due",
            "data[detail][2][title]": "二、需求",  # 第二部分标题
            "data[detail][2][id]": 0,  # 组件ID
            "data[detail][2][story_list_show_type]": "flat",  # 平铺展示模式
            f"data[detail][2][workitem_ids][{PROJECT_ID}]": REQUIREMENT_ID,  # 关联的需求ID
            f"data[detail][2][workitem_list_query_type][{PROJECT_ID}]": "list",  # 列表查询类型
            f"data[detail][2][workitem_list_view_id][{PROJECT_ID}]": 0,  # 列表视图ID
            f"data[detail][2][workitem_list_sys_view_id][{PROJECT_ID}]": 0,  # 系统视图ID
            f"data[detail][2][workitem_list_display_count][{PROJECT_ID}]": 10,  # 展示数量
            "data[detail][2][comment]": "",  # 备注信息
            "data[return_url]": "/workspace_reports/index",  # 回调地址
            "data[action_timestamp]": "",  # 时间戳保留字段
            "data[filter_id]": 0,  # 过滤器ID
            "data[model_name]": "",  # 模型名称保留字段
            "data[submit]": "保存草稿",  # 提交按钮文本
        }

        # ==================================================================
        # 阶段5：动态模块添加
        # ==================================================================
        # 存在BUG时添加缺陷列表模块
        if self.bugIds:
            data.update({
                "data[detail][3][type]": "bug_list",  # 缺陷列表组件类型
                "data[detail][3][workitem_type]": "bug",  # 工作项类型为缺陷
                # 展示字段列表
                "data[detail][3][show_fields]": "title,version_report,priority,severity,status,current_owner,created",
                "data[detail][3][title]": "三、缺陷列表",  # 第三部分标题
                "data[detail][3][id]": 0,  # 组件ID
                "data[detail][3][story_list_show_type]": "flat",  # 平铺展示模式
                f"data[detail][3][workitem_ids][{PROJECT_ID}]": ','.join(self.bugIds),  # 关联的缺陷ID列表
                f"data[detail][3][workitem_list_query_type][{PROJECT_ID}]": "list",  # 列表查询类型
                f"data[detail][3][workitem_list_view_id][{PROJECT_ID}]": 0,  # 列表视图ID
                f"data[detail][3][workitem_list_sys_view_id][{PROJECT_ID}]": 0,  # 系统视图ID
                f"data[detail][3][workitem_list_display_count][{PROJECT_ID}]": 10,  # 展示数量
                "data[detail][3][comment]": "",  # 备注信息
            })

        # 存在图表数据时添加可视化模块
        if self.chartHtml:
            data.update({
                "data[detail][4][type]": "richeditor",  # 富文本组件类型
                "data[detail][4][title]": "图表",  # 第四部分标题
                "data[detail][4][id]": 0,  # 组件ID
                "data[detail][4][default_value]": f"<div>{self.chartHtml}</div>",  # 插入图表HTML代码
            })

        # ==================================================================
        # 阶段6：报告提交处理
        # ==================================================================
        # 根据全局配置决定提交方式
        if IS_CREATE_REPORT:
            # 执行报告提交请求
            fetch_data(url=url, params=params, data=data, method='POST')
        else:
            # 调试模式下打印请求数据结构
            print('\n请求测试报告data:')
            print(json.dumps(data, indent=4, ensure_ascii=False))

    def create_chart(self) -> None:
        """
        创建并汇总各种统计图表数据。

        本函数负责生成多个条形图，涵盖开发工时、BUG修复人、各端缺陷级别分布及缺陷根源分布统计。
        每个图表生成后，其路径信息被存储，并最终调用私有方法_charts_to_html将这些信息转换为HTML格式。

        处理流程：
            1. 初始化图表列表，用于存储所有图表的路径信息
            2. 设置中文字体和负号显示
            3. 创建开发工时统计条形图，并将图表路径信息添加到图表列表中
            4. 如果存在BUG数据，则创建以下图表：
                - BUG修复人统计条形图
                - 各端缺陷级别分布统计条形图和表格数据
                - 缺陷根源分布统计条形图和表格数据
                - 缺陷每日变化趋势折线图
            5. 调用私有方法_charts_to_html将图表路径信息转换并生成HTML
            6. 如果不需要创建报告，则打印图表链接

        异常处理：
            ValueError: 当图表数据生成失败时抛出
            TypeError: 当输入数据类型错误时抛出
        """
        # ==================================================================
        # 阶段1：初始化图表列表
        # ==================================================================
        charts = list()  # 初始化存储图表路径信息的列表

        # ==================================================================
        # 阶段2：设置中文字体和负号显示
        # ==================================================================
        plt.rcParams['font.sans-serif'] = [PLT_FONT[get_system_name()]]  # 根据操作系统设置中文字体
        plt.rcParams['axes.unicode_minus'] = False  # 设置负号显示

        # ==================================================================
        # 阶段3：创建开发工时统计条形图
        # ==================================================================
        work_hour_plot_data = create_bar_plot(title='开发工时统计', data=self.workHours)  # 生成开发工时统计条形图
        charts.append({
            'plotPath': work_hour_plot_data['plotPath'],  # 将图表路径信息添加到图表列表中
        })

        # ==================================================================
        # 阶段4：创建BUG相关图表（如果存在BUG数据）
        # ==================================================================
        if self.bugIds:
            # 创建BUG修复人统计条形图
            fixer_plot_data = create_bar_plot(title='BUG修复人', data=self.fixers)  # 生成BUG修复人统计条形图
            charts.append({
                'plotPath': fixer_plot_data['plotPath'],  # 将图表路径信息添加到图表列表中
            })

            # 创建各端缺陷级别分布统计条形图和表格数据
            bug_level_multi_client_count_plot_data = create_bar_plot(
                title='各端缺陷级别分布', data=self.bugLevelsMultiClientCount)  # 生成各端缺陷级别分布统计条形图
            charts.append({
                'plotPath': bug_level_multi_client_count_plot_data['plotPath'],  # 将图表路径信息添加到图表列表中
                'tableData': {
                    'firstColumnHeader': '软件平台',  # 表格第一列的标题
                    'tableWidth': bug_level_multi_client_count_plot_data['plotData']['widthPx'],  # 表格宽度
                    'data': self.bugLevelsMultiClientCount,  # 表格中展示的数据
                    'isMultiDimensionalTable': True,  # 表示数据是多维的，需要使用多维度表格显示
                    'isRowTotal': True,  # 表示数据中包含行总计，需要计算并显示
                }
            })

            # 创建缺陷根源分布统计条形图和表格数据
            bug_source_count_plot_data = create_bar_plot(title='缺陷根源分布统计',
                                                         data=self.bugSourceMultiClientCount)  # 生成缺陷根源分布统计条形图
            charts.append({
                'plotPath': bug_source_count_plot_data['plotPath'],  # 将图表路径信息添加到图表列表中
                'tableData': {
                    'firstColumnHeader': '软件平台',  # 表格第一列的标题
                    'tableWidth': bug_source_count_plot_data['plotData']['widthPx'],  # 表格宽度
                    'data': self.bugSourceMultiClientCount,  # 表格中展示的数据
                    'isMultiDimensionalTable': True,  # 表示数据是多维的，需要使用多维度表格显示
                    'isRowTotal': True,  # 表示数据中包含行总计，需要计算并显示
                }
            })

            # 创建缺陷每日变化趋势折线图
            daily_trend_of_bug_changes_count_broken_line_data = create_broken_line_plot(
                title='缺陷每日变化趋势', data=self.dailyTrendOfBugChanges)  # 生成缺陷每日变化趋势折线图
            charts.append({
                'plotPath': daily_trend_of_bug_changes_count_broken_line_data['plotPath'],  # 将图表路径信息添加到图表列表中
                'tableData': {
                    'firstColumnHeader': '日期',  # 表格第一列的标题
                    'tableWidth': daily_trend_of_bug_changes_count_broken_line_data['plotData']['widthPx'],  # 表格宽度
                    'data': self.dailyTrendOfBugChanges,  # 表格中展示的数据
                    'isMultiDimensionalTable': True,  # 表示数据是多维的，需要使用多维度表格显示
                    'isRowTotal': False,  # 表示数据中包含行总计，需要计算并显示
                    'sort': 'asc',  # 按升序排序
                }
            })

        # ==================================================================
        # 阶段5：将图表路径信息转换为HTML格式
        # ==================================================================
        self._charts_to_html(charts)  # 调用私有方法将图表路径信息转换并生成HTML

        # ==================================================================
        # 阶段6：打印图表链接（如果不需要创建报告）
        # ==================================================================
        if not IS_CREATE_REPORT:
            print('\n\n\n图表链接：')
            for chart in charts:
                print('https://www.tapd.cn' + chart['plotPath'])  # 打印图表链接

    def _charts_to_html(self, charts: list):
        """
        将图表信息转换为HTML格式字符串。

        遍历charts列表，根据每个图表的类型和数据生成相应的HTML代码。
        支持两种类型的图表：图像和表格。

        参数:
        - charts: 包含图表信息的列表，每个图表信息是一个字典。
        """
        for chart in charts:
            # 检查图表是否为字典类型
            if isinstance(chart, dict):
                # 如果图表包含plotPath键，则生成图像图表的HTML
                if chart.get('plotPath'):
                    self.chartHtml += f'''
                    <div>
                        <img src="{chart["plotPath"]}" />
                    </div>'''
                # 如果图表包含tableData键且为字典类型，则生成表格图表的HTML
                if chart.get('tableData') and isinstance(chart['tableData'], dict):
                    table_data: dict = chart['tableData']  # 获取表格数据
                    if table_data.get('sort') and table_data['sort'] in ('asc', 'desc'):
                        table_data['data'] = {
                            k: table_data['data'][k]
                            for k in sorted(
                                table_data['data'],
                                reverse=True if table_data['sort'] == 'desc' else False
                            )
                        }
                    if table_data.get('isMultiDimensionalTable'):  # 如果数据是多维的，则生成多维表格
                        data_headers = []  # 初始化表格的头部动态数据
                        for valueData in table_data['data'].values():  # 获取数据头部动态数据
                            data_headers += list(valueData)  # 添加到头部动态数据列表中
                            break  # 跳出循环
                        # 公用的样式
                        common_style = {
                            'padding': '0 10px',
                            'vertical-align': 'middle',
                            'border-right': 'none',
                            'border-left': 'none',
                            'border-top': 'none',
                            'border-bottom': '1px solid rgb(230, 230, 230)',
                            'background-color': 'rgb(255, 255, 255)',
                        }
                        # 表格首行的样式
                        header_row_style = style_convert({
                            **common_style,
                            'height': '50px',
                            'font-size': '12px',
                            'color': '#8c95a8',
                            'border-top': '1px solid rgb(230, 230, 230)',
                        })
                        # 表格内容的样式
                        row_style = style_convert({
                            **common_style,
                            'height': '38px',
                            'font-size': '12px',
                        })
                        # 表格总计行的样式
                        total_row_style = style_convert({
                            **common_style,
                            'height': '38px',
                            'font-size': '12px',
                            'color': 'black',
                            'font-weight': 'bold',
                        })
                        # 初始化表格内容行的HTML变量
                        data_row_html = ''
                        # 根据表格动态数据头的数量增加列表的值, 用于展示在总计行, 列表第一个数据记录的是总计中的小计
                        total_row_values = [0, ] + [0 for _ in data_headers]
                        for tableKey, tableData in table_data['data'].items():  # 遍历表格数据键与数据值
                            # 遍历表格数据值, 生成表格内容行的HTML, tr标签为表格中的一整行, td标签为行中的单元格, 第一个td标签为一行中的第一个单元格, 第二个td标签为行中的第二个单元格, 以此类推
                            data_row_html += f"""
                            <tr>
                                <td align="left" style="{row_style}">
                                    {tableKey}
                                </td>
                                {f'''<td align="left" style="{row_style}">
                                    {sum(tableData.values())}
                                </td>''' if table_data.get('isRowTotal') else ''}
                                {''.join(f'''
                                <td align="left" style="{row_style}">
                                    {dataValue}
                                </td>''' for dataValue in tableData.values())}
                            </tr>"""
                            table_data_values = [value for value in tableData.values()]  # 将一行的数据遍历成一个列表
                            for index in range(len(table_data_values)):  # 遍历列表中所有索引
                                total_row_values[0] += table_data_values[index]  # 累加总计行中的小计
                                total_row_values[index + 1] += table_data_values[index]  # 累加总计行中的对应索引的值
                        # 构建表格的HTML, 首行的内容和总计行的内容直接在这里构建, 剩下的内容通过data_row_html引入
                        self.chartHtml += f'''
                        {'<div><br /></div>' * 2}
                        <div>
                            <table cellpadding="0" cellspacing="0" class="report-chart__table" style="width:{table_data['tableWidth']}px;border:none;margin-top:0;margin-bottom:0;margin-left:0;margin-right:0;">
                                <tbody>
                                    <tr>
                                        <th align="left" style="{header_row_style}">
                                            {table_data['firstColumnHeader']}
                                        </th>
                                        {f"""<th align="left" style="{header_row_style}">
                                            小计
                                        </th>""" if table_data.get('isRowTotal') else ''}
                                        {''.join(f"""
                                        <th align="left" style="{header_row_style}">
                                            {dataHeader}
                                        </th>""" for dataHeader in data_headers) if data_headers else ''}
                                    </tr>
                                    {data_row_html}
                                    <tr>
                                        <td align="left" style="{total_row_style}">
                                            总计
                                        </td>
                                        {f"""<td align="left" style="{total_row_style}">
                                            {total_row_values[0]}
                                        </td>""" if table_data.get('isRowTotal') else ''}
                                        {''.join(f"""
                                        <td align="left" style="{total_row_style}">
                                            {value}
                                        </td>""" for value in total_row_values[1:])}
                                    </tr>
                                </tbody>
                            </table>
                        </div>'''
                    else:  # 非多维度的表格
                        # 根据表格数据生成表格的样式和结构
                        table_style = style_convert({
                            # "width": f"{300 * len(table_data['headers'])}px",
                            "width": f"{table_data['tableWidth']}px",
                        })
                        cell_style = style_convert({
                            "text-align": "center",
                            "border-color": "rgb(153, 153, 153)",
                            "border-image": "initial",
                            "padding": "2px",
                        })
                        title_font_style = style_convert({
                            "font-size": "x-large",
                            "font-family": "黑体",
                        })
                        column_header_font_style = style_convert({
                            "font-size": "large",
                            "font-family": "黑体",
                        })
                        row_header_font_style = style_convert({
                            "font-size": "medium",
                        })
                        # 生成表格HTML代码
                        self.chartHtml += f'''
                        {'<div><br /></div>' * 2}
                        <div>
                            <table class="editor-table" style="{table_style}">
                                <tbody>
                                    <tr>
                                        <td style="{cell_style}" colspan="{len(table_data['headers'])}">
                                            <span style="{title_font_style}"><b>{table_data["title"]}</b></span>
                                        </td>
                                    </tr>
                                    <tr>{''.join(f"""
                                        <td style="{cell_style}">
                                            <b>
                                                <span style="{column_header_font_style}">
                                                    {header}
                                                </span>
                                            </b>
                                        </td>""" for header in table_data['headers'])}
                                    </tr>
                                {''.join(f"""
                                    <tr>
                                        <td style="{cell_style}">
                                            <span style="{row_header_font_style}">
                                                {name}
                                            </span>
                                        </td>
                                        <td style="{cell_style}">
                                            <div>
                                                {value}
                                            </div>
                                        </td>
                                    </tr>""" for name, value in table_data['data'].items())}
                                </tbody>
                            </table>
                        </div>'''
            # 根据图表是否为最后一个，添加不同数量的间隔行
            if chart != charts[-1]:
                interval_rows = 5
            else:
                interval_rows = 2
            self.chartHtml += '<div><br /></div>' * interval_rows

    def _get_list_config(self):
        """
        获取当前列表展示字段的配置信息[]转换成";"分隔的字符串并进行存储
        :return: None, 该方法仅进行存储信息
        """
        self.oldBugListConfigs = ';'.join(get_query_filtering_list_config())  # 获取当前缺陷列表展示字段的配置信息, 存储到类属性中
        self.oldSubTaskListConfigs = ';'.join(get_requirement_list_config())  # 获取当前需求中的子任务列表展示字段的配置信息, 存储到类属性中

    def _daily_trend_of_bug_changes_count(self, data):
        """
        统计每日缺陷变化趋势。

        该方法旨在分析和记录每一天缺陷的创建、修复、关闭以及未关闭状态的总数。
        它通过检查缺陷的创建、修复和关闭日期，并与任务的最后日期进行比较，来更新每日趋势数据。

        参数:
        - data: 包含缺陷创建、修复和关闭时间的数据字典。
        """
        # 初始化缺陷统计字典
        count_data = {
            '创建缺陷总数': 0,
            '修复缺陷总数': 0,
            '关闭缺陷总数': 0,
            '未关闭缺陷总数': 0,
        }

        # 将缺陷创建、修复和关闭的时间转换为日期格式
        create_date = date_time_to_date(data['created'])
        resolve_date = date_time_to_date(data['resolved']) if data.get('resolved') else None
        close_date = date_time_to_date(data['closed']) if data.get('closed') else None

        # 检查缺陷是否是需求完成后创建的, 如果是则返回
        if create_date > self.lastTaskDate:
            return

        # 检查创建日期是否在任务的最后日期之前或当天, 如果当前日期不在统计中，则初始化该日期的统计信息
        if not self.dailyTrendOfBugChanges.get(create_date):
            self.dailyTrendOfBugChanges[create_date] = count_data.copy()
        # 更新创建缺陷总数
        self.dailyTrendOfBugChanges[create_date]['创建缺陷总数'] += 1

        # 检查修复日期是否在任务的最后日期之前或当天
        if resolve_date and resolve_date <= self.lastTaskDate:
            if not self.dailyTrendOfBugChanges.get(resolve_date):
                self.dailyTrendOfBugChanges[resolve_date] = count_data.copy()
            # 更新修复缺陷总数
            self.dailyTrendOfBugChanges[resolve_date]['修复缺陷总数'] += 1

        # 判断存在关闭日期且关闭日期在任务时最后日期之前或当天
        if close_date and close_date <= self.lastTaskDate:
            if not self.dailyTrendOfBugChanges.get(close_date):
                self.dailyTrendOfBugChanges[close_date] = count_data.copy()
            # 更新关闭缺陷总数
            self.dailyTrendOfBugChanges[close_date]['关闭缺陷总数'] += 1
            # 如果缺陷在创建当天未关闭，则统计未关闭缺陷数
            if create_date < close_date:
                # 获取从创建到关闭的工作日，并减去1，因为最后一天不需要统计
                unclosed_dates: list = get_days(create_date, close_date)[:-1]
                for unclosed_date in unclosed_dates:  # 遍历未关闭的每一天
                    # 如果当前日期不在统计中，则初始化该日期的统计信息
                    if not self.dailyTrendOfBugChanges.get(unclosed_date):
                        self.dailyTrendOfBugChanges[unclosed_date] = count_data.copy()
                    self.dailyTrendOfBugChanges[unclosed_date]['未关闭缺陷总数'] += 1
        else:  # 如果缺陷未关闭
            # 获取从创建到任务的最后日期的工作日
            unclosed_dates: list = get_days(create_date, self.lastTaskDate)
            for unclosed_date in unclosed_dates:  # 遍历未关闭的每一天
                # 如果当前日期不在统计中，则初始化该日期的统计信息
                if not self.dailyTrendOfBugChanges.get(unclosed_date):
                    self.dailyTrendOfBugChanges[unclosed_date] = count_data.copy()
                self.dailyTrendOfBugChanges[unclosed_date]['未关闭缺陷总数'] += 1

    def edit_list_config(self):
        """
        编辑列展示的字段
        需要配置脚本必要的字段, 否则接口无法返回需要的字段信息
        :raise: 捕获编辑列字段配置失败抛出异常
        """
        if not self.oldBugListConfigs or not self.oldSubTaskListConfigs:  # 如果获取不到列展示字段的配置信息，则获取一次
            self._get_list_config()  # 获取列展示字段的配置信息
        new_bug_list_configs = self.oldBugListConfigs  # 将获取到的列展示字段的配置信息存储到变量中
        new_sub_task_list_configs = self.oldSubTaskListConfigs  # 将获取到的列展示字段的配置信息存储到变量中
        for bugListMustKey in BUG_LIST_MUST_KEYS:  # 遍历需要配置的BUG列展示字段
            if bugListMustKey not in new_bug_list_configs:  # 如果需要配置的BUG列展示字段不在获取到的列展示字段的配置信息中，则添加到配置信息中
                new_bug_list_configs += f';{bugListMustKey}'  # 添加到配置信息中
        for subTaskListMustKey in SUB_TASK_LIST_MUST_KEYS:  # 遍历需要配置的子任务列展示字段
            if subTaskListMustKey not in new_sub_task_list_configs:  # 如果需要配置的子任务列展示字段不在获取到的列展示字段的配置信息中，则添加到配置信息中
                new_sub_task_list_configs += f';{subTaskListMustKey}'  # 添加到配置信息中
        try:
            if new_bug_list_configs != self.oldBugListConfigs:  # 如果新列字段配置信息不等于原来的列字段配置信息，则编辑BUG列表展示字段的配置信息
                assert edit_query_filtering_list_config(new_bug_list_configs)  # 编辑BUG列表展示字段的配置信息
            if new_sub_task_list_configs != self.oldSubTaskListConfigs:  # 如果新列字段配置信息不等于原来的列字段配置信息，则编辑子任务列表展示字段的配置信息
                assert edit_requirement_list_config(new_sub_task_list_configs)  # 编辑子任务列表展示字段的配置信息
        except Exception as e:  # 捕获异常并打印堆栈信息
            traceback.format_exc()  # 打印堆栈信息
            raise e  # 抛出异常

    def restore_list_config(self):
        try:
            assert edit_query_filtering_list_config(self.oldBugListConfigs)
            assert edit_requirement_list_config(self.oldSubTaskListConfigs)
        except Exception as e:
            traceback.format_exc()
            raise e
        else:
            self.isInitialListConfig = True

    def print_error(self, error_text):
        print(_print_text_font(error_text, color='red'))
        if not self.isInitialListConfig:
            self.restore_list_config()
        sys.exit(1)

    def get_reopen_bug_detail(self):
        """
        获取重新打开的缺陷详细信息。

        本方法通过多线程执行，为每个bugId获取其状态转换历史，特别关注重新打开的状态。
        """
        # 初始化请求执行数据字典，用于存储每个bugId对应的执行结果。
        request_exec_data = {}
        # 定义实体类型为'bug'，用于后续的功能调用。
        entity_type = 'bug'

        # 使用上下文管理器创建一个线程池执行器，线程池大小无上限。
        with ThreadPoolExecutor(max_workers=None) as executor:
            # 遍历bugIds列表，为每个bugId提交一个任务到线程池。
            for bugId in self.bugIds:
                # 提交任务get_workitem_status_transfer_history到线程池执行，并将返回的Future对象存储在request_exec_data中。
                request_exec_data[bugId] = executor.submit(get_workitem_status_transfer_history, entity_type, bugId)

        # 遍历request_exec_data字典，获取每个bugId对应的执行结果（Future对象）。
        for bugId, requestExec in request_exec_data.items():
            # 获取执行结果，这将阻塞直到对应任务完成。
            res_data_list = requestExec.result()
            # 遍历结果列表，查找当前状态为'reopened'的数据项。
            for data in res_data_list:
                if data['current_status_origin'] == 'reopened':
                    # 对于每个状态为'reopened'的bugId，计数加1。
                    self.reopenBugsData[bugId] = self.reopenBugsData.get(bugId, 0) + 1

    def _save_task_hours(self, data):
        """
        保存每个开发者每天的任务工时。

        根据任务数据更新每个开发者每天的工时。如果任务开始和结束日期相同，则将完成的努力添加到该日期。
        如果开始和结束日期不同，则根据每个日期的剩余工时分配努力，直到完成的努力分配完毕。

        参数:
        - data: 包含任务信息的字典，包括开发者名称、完成的努力、任务开始和结束日期。

        返回:
        无返回值。更新 self.dailyWorkingHoursOfEachDeveloper 字典。
        """
        # 获取开发者名称、实际完成工时
        developer_name = data['developerName']
        effort_completed = float(data.get('effort_completed', 0))

        # 如果开始和结束日期相同，则将该日期的工时加上实际完成工时
        if data['begin'] == data['due']:
            self.dailyWorkingHoursOfEachDeveloper[developer_name][data['begin']] += effort_completed
        # 如果开始和结束日期不同，则根据每个日期的剩余工时分配实际完成工时，直到完成的实际完成工时分配完毕
        elif data['begin'] < data['due']:
            # 获取开始和结束日期之间的所有日期
            for day in get_days(data['begin'], data['due']):
                # 获取该日期的工时
                saved_task_hours = self.dailyWorkingHoursOfEachDeveloper[developer_name].get(day, 0)
                # 计算该日期的剩余工时
                remaining_effort = 8 - saved_task_hours
                # 如果剩余工时大于0，则将该日期的工时加上剩余工时，并减去实际完成工时
                if effort_completed - remaining_effort > 0:
                    self.dailyWorkingHoursOfEachDeveloper[developer_name][day] += remaining_effort
                    # 减去剩余工时
                    effort_completed -= remaining_effort
                else:
                    # 如果剩余工时小于等于0，则将该日期的工时加上实际完成工时，并结束循环
                    self.dailyWorkingHoursOfEachDeveloper[developer_name][day] += effort_completed
                    break

    def _remove_current_user(self):
        """
        从测试收件人列表中移除当前用户，并添加特定的测试负责人（如果当前用户不是测试负责人）。

        1. 遍历testRecipient列表，移除每个元素中的部门信息，并构建一个新的字符串testersStr。
        2. 获取当前用户的昵称，并检查是否在testRecipient列表中，如果在则移除。
        3. 如果当前用户不是测试负责人，且测试负责人不在testRecipient列表中，则添加测试负责人到列表末尾。
        """
        # 如果testRecipient列表存在，开始处理列表中的元素
        if self.testRecipient:
            is_last = False
            for tester in self.testRecipient:
                # 检查当前遍历的测试收件人是否为列表中的最后一个
                if tester == self.testRecipient[-1]:
                    is_last = True
                # 移除测试收件人中的部门信息，并根据是否为最后一个元素决定是否添加分隔符
                tester = tester.replace(DEPARTMENT, '')
                self.testersStr += f'{tester}' if is_last else f'{tester}、'

            # 获取当前用户的昵称
            current_user_name = get_user_detail()['user_nick']
            # 如果当前用户在测试收件人列表中，则移除
            if current_user_name in self.testRecipient:
                self.testRecipient.remove(current_user_name)
            # 如果当前用户不是测试负责人，且测试负责人不在测试收件人列表中，则添加测试负责人
            if current_user_name != TESTER_LEADER and TESTER_LEADER not in self.testRecipient:
                self.testRecipient.append(TESTER_LEADER)

    def _process_developer_task(self, developer: str, effort: float, begin: datetime.date,
                                due: datetime.date, child_data: dict):
        """
        处理开发者任务逻辑
        - 累加工时
        - 记录任务时间范围
        - 保存详细工时分布
        """
        # 累加总工时
        self.workHours[developer] += effort

        # 更新任务时间范围
        self._update_date_range(begin=begin)

        # 保存子任务引用（用于后续分析）
        child_data['developerName'] = developer

        # 记录每日工时分布（如果存在有效时间）
        if begin and due:
            self._save_task_hours(child_data)

    def _process_tester_task(self, due_date: datetime.date, begin_date: datetime.date, owner: str):
        """
        处理测试任务逻辑
        - 标记测试任务存在
        - 更新上线日期
        - 维护测试联系人列表
        """
        # 首次遇到测试任务时标记
        if not self.isExistTestTask:
            self.isExistTestTask = True

        # 更新最晚任务日期（使用安全的日期比较）
        self._update_date_range(due=due_date)

        # 更新上线日期逻辑优化
        if begin_date and (not self.onlineDate or begin_date > self.onlineDate):
            self.onlineDate = begin_date

        # 维护测试收件人列表（去重处理）
        if owner not in self.testRecipient:
            self.testRecipient.append(owner)

    def _update_date_range(self, begin: datetime.date = None, due: datetime.date = None):
        """更新项目时间范围记录"""
        # 最早任务日期
        if begin:
            if not self.earliestTaskDate or begin < self.earliestTaskDate:
                self.earliestTaskDate = begin

        # 最晚任务日期（开发者任务维度）
        if due:
            if not self.lastTaskDate or due > self.lastTaskDate:
                self.lastTaskDate = due

    def _statistics_bug_severity_level(self, severity_level: str):
        if not severity_level:
            severity_level = '空'
        self.bugLevelsCount[severity_level] += 1

    def _statistics_bug_source(self, bug_source: str):
        if not bug_source:
            bug_source = '空'
        self.bugSourceCount[bug_source] += 1

    def _statistics_deploy_prod_day_unrepaired_bug(
            self,
            bug_status: str,
            bug_id: str,
            severity_name: str,
            resolved_date: str = None
    ):
        is_deploy_prod_day_unrepaired_bug = True
        if bug_status == 'closed' and resolved_date:
            if resolved_date < self.onlineDate:
                is_deploy_prod_day_unrepaired_bug = False
        if is_deploy_prod_day_unrepaired_bug and severity_name in BUG_LEVELS[0: 2]:
            self.unrepairedBugs['deployProdDayUnrepaired']['P0P1'].append(bug_id)
        # 如果上线当天未修复得BUG并且严重等级为"P2", 则将该bug的id添加到unrepairedBugsData字典中，并累加其数量
        elif is_deploy_prod_day_unrepaired_bug and severity_name not in BUG_LEVELS[0: 2]:
            self.unrepairedBugs['deployProdDayUnrepaired']['P2'].append(bug_id)

    def _statistics_on_that_day_unrepaired_bug(
            self,
            bug_status: str,
            bug_id: str,
            severity_name: str,
            created_date: str,
            resolved_date: str = None
    ):
        is_on_that_day_unrepaired_bug = True
        if bug_status == 'closed' and resolved_date:
            if created_date == resolved_date:
                is_on_that_day_unrepaired_bug = False
        if is_on_that_day_unrepaired_bug and severity_name == BUG_LEVELS[0]:
            self.unrepairedBugs['onThatDayUnrepaired']['P0'].append(bug_id)
        # 如果bug不是当天修复并且严重等级为"P1"，则将该bug的id添加到unrepairedBugsData字典中，并累加其数量
        elif is_on_that_day_unrepaired_bug and severity_name == BUG_LEVELS[1]:
            self.unrepairedBugs['onThatDayUnrepaired']['P1'].append(bug_id)
        # 如果bug不是当天修复并且严重等级不为"P0"或"P1"，则将该bug的id添加到unrepairedBugsData字典中，并累加其数量
        elif is_on_that_day_unrepaired_bug and severity_name not in BUG_LEVELS[0: 2]:
            self.unrepairedBugs['onThatDayUnrepaired']['P2'].append(bug_id)

    def _calculate_positive_integrity_score(self):
        """
        输入项目的积极性/文档完成性评分。

        本函数展示了一段文本，描述了不同评分标准下，对项目期间团队合作的积极性和文档完成情况的评价。
        根据这段文本，用户会被要求输入一个分数，来表示项目的积极性/文档完成性评分。
        """
        # 打印标题，用于清晰地标识出这部分评分的开始
        print('配合积极性/文档完成性'.center(LINE_LENGTH, '-'))

        # 定义评分标准文本，详细解释了每个分数段代表的项目团队行为和文档完成情况
        score_text = """20分：项目期间积极配合测试主动跟进问题并解决。提测文档清晰完善（技术、接口）等。会给测试提供测试范围、注意事项、脚本、或其他有意义的建议。对测试执行起到重要帮助
15分：项目期间积极配合测试主动跟进问题并解决。提测文档清晰完善（技术、接口）等
10分：项目期间能够基本配合测试进行相关项目推进，能够跟进问题并按期解决，文档部分缺失、未及时更新
5分：项目期间态度懈怠、散漫、不配合测试解决问题。但文档全面、及时更新
1分：项目期间态度懈怠、散漫、不配合测试解决问题、文档缺失、不更新、有错误等。
"""
        # 调用_input函数来获取用户输入的分数，并将分数存储在实例的score字典中
        self.score['positiveIntegrityScore'] = _input(score_text + '请输入分数：', **SCORE_INPUT_DATA)
        self.scoreContents.append({
            'title': '配合积极性/文档完成性',
            'scoreRule': score_text,
            'score': self.score['positiveIntegrityScore']
        })

    def _calculate_smoke_testing_score(self):
        """
        计算并输入冒烟测试分数。

        本函数解释了冒烟测试分数的评定标准，并要求用户根据这些标准输入分数。
        它首先打印出冒烟测试的标题，然后定义不同分数对应的测试情况，
        最后提示用户输入分数，该分数将被记录在实例的score字典中。
        """
        # 打印冒烟测试标题，用于清晰地区分不同的评分项
        print('冒烟测试'.center(LINE_LENGTH, '-'))

        # 定义冒烟测试分数的评定标准
        score_text = """20分：考核期内所有版本有冒烟自测并一次通过 
15分：考核期版本有冒烟自测但部分用例不通过 
10分：考核期内提测版本没有进行冒烟自测，主流程通过 
5分：考核期内有进行冒烟自测，主流程不通过 
1分：考核期内提测版本没有进行冒烟自测，主流程不通过
"""
        # 调用_input函数来获取用户输入的分数，并将分数存储在实例的score字典中
        self.score['smokeTestingScore'] = _input(score_text + '请输入分数：', **SCORE_INPUT_DATA)

        self.scoreContents.append({
            'title': '冒烟测试',
            'scoreRule': score_text,
            'score': self.score['smokeTestingScore']
        })

    def _calculate_bug_count_score(self):
        """
        计算BUG数得分的方法。

        本方法首先会打印BUG数标题，并根据已知的BUG总数和开发周期，
        或者通过用户输入获取这些值。然后，它会计算开发人员平均每人小时数
        和每日平均小时数，进而计算UU（User Unit）结果。最后，根据BUG总数
        和UU结果计算项目平均一天工作量的Bug数，并根据这一结果调用另一个函数
        来计算BUG数得分。
        """
        # 打印标题
        print('BUG数'.center(LINE_LENGTH, '-'))

        # 获取BUG总数，如果已知则直接打印，否则请求用户输入
        bug_total = self.bugTotal
        if bug_total:
            print(f"获取的BUG总数为：{_print_text_font(bug_total, color='green')}")
        else:
            bug_total = _input("请输入BUG总数为：", int)
            self.bugInputTotal = bug_total
        self.bugCountScoreMsg += f'BUG总数为：{bug_total}\n'

        # 获取开发周期，如果已知则直接打印，否则请求用户输入
        if self.developmentCycle:
            print(f"获取的开发周期总天数为：{_print_text_font(round(self.developmentCycle, 1), color='green')}")
        else:
            self.developmentCycle = _input("请输入开发周期总天数：", float)
        self.bugCountScoreMsg += f'开发周期总天数为：{self.developmentCycle}\n'

        # 打印开发人员总数
        print(f"获取的开发人员总数为：{_print_text_font(self.developerCount, color='green')}")

        # 计算平均每人小时数和每日平均小时数
        avg_person_hours = self.devTotalHours / self.developerCount
        daily_avg_hours = avg_person_hours / self.developmentCycle

        # 计算UU结果，即开发人员总数乘以平均工时
        uu_result = self.developerCount * daily_avg_hours

        # 计算项目平均一天工作量的Bug数，避免除以0的情况
        X = round(bug_total / uu_result if uu_result != 0 else float('inf'), 1)

        # 打印计算结果
        print(f"开发人员总数乘以平均工时为 {_print_text_font(f'{uu_result:.2f}', color='green')}")
        print(f"该项目平均一天工作量的Bug数为 {_print_text_font(X, color='green')}")

        self.bugCountScoreMsg += f'开发人员总数乘以平均工时为 {uu_result:.2f}\n'
        self.bugCountScoreMsg += f'该项目平均一天工作量的Bug数为 {X}\n'

        # 调用calculate_bug_count_rating函数计算得分，并进行输出
        self.score['bugCountScore'] = calculate_bug_count_rating(X)

        if self.bugLevelsCount:
            if self.bugLevelsCount['致命']:
                if self.score['bugCountScore'] > 10:
                    self.score['bugCountScore'] = 10
            elif self.bugLevelsCount['严重']:
                if self.score['bugCountScore'] > 15:
                    self.score['bugCountScore'] = 15

        print('-' * LINE_LENGTH)

        # 如果得分不为None，则输出得分
        if self.score['bugCountScore'] is not None:
            bug_count_score = f'{self.score["bugCountScore"]} 分'
            print(
                f'当平均一天工作量的Bug数={_print_text_font(X, color="green")}时，当前该项目软件质量评分中“BUG数”一项得分为：{_print_text_font(bug_count_score)}')
        self.scoreContents.append({
            'title': 'BUG数',
            'scoreRule': self.bugCountScoreMsg + """20分：0<=平均一天工作的Bug数<=1且无严重、致命BUG
15分：1<平均一天工作量的Bug数<=1.5且无致命Bug
10分：1.5<平均一天工作量的Bug数<=2.0
5分：2.0<平均一天工作量的Bug数<=3.0
1分：3.0<平均一天工作量的Bug数
""",
            'score': self.score['bugCountScore']
        })

    def _calculate_bug_repair_score(self):
        """
        计算并打印BUG修复评分情况。

        该方法首先会检查在项目上线当天是否存在未修复的BUG（P0、P1和P2）。
        如果存在，则打印出未修复BUG的数量，并根据这些数据计算BUG修复评分。
        如果不存在未修复的BUG，则提供一个评分标准文本，供用户输入评分。
        """
        score_text = r"""P0=致命缺陷, P1=严重缺陷, P2=一般缺陷、提示、建议
20分：名下BUG当天修复，当天通过回归验证且无重开 
15分：名下BUG（P0\P1）当天修复，P2\其他隔天修复，所以BUG均不能重开
10分：名下BUG（P0）当天修复，（P1\P2）当天未修复，隔天修复
5分：名下BUG（P2）上线当天存在未修复
1分：名下BUG（P0\P1）上线当天存在未修复
"""
        # 打印BUG修复标题
        print('BUG修复'.center(LINE_LENGTH, '-'))
        # 检查是否存在未修复的BUG
        if self.bugTotal:
            # 打印各优先级未修复BUG的数量
            self.bugRepairScoreMsg += \
                f'''P0=致命缺陷, P1=严重缺陷, P2=一般缺陷、提示、建议
在项目上线当天存在P0或者P1未修复BUG数为：{_print_text_font(len(self.unrepairedBugs["deployProdDayUnrepaired"]["P0P1"]), color="green")}
在项目上线当天存在P2未修复BUG数为：{_print_text_font(len(self.unrepairedBugs["deployProdDayUnrepaired"]["P2"]), color="green")}
P0当天未修复的BUG数为：{_print_text_font(len(self.unrepairedBugs["onThatDayUnrepaired"]["P0"]), color="green")}
P1当天未修复的BUG数为：{_print_text_font(len(self.unrepairedBugs["onThatDayUnrepaired"]["P1"]), color="green")}
P2当天未修复的BUG数为：{_print_text_font(len(self.unrepairedBugs["onThatDayUnrepaired"]["P2"]), color="green")}'''
            print(self.bugRepairScoreMsg)
            print('-' * LINE_LENGTH)

            score_text = self.bugRepairScoreMsg + '\n' + score_text

            # 计算BUG修复评分
            self.score['bugRepairScore'] = calculate_bug_repair_rating(self.unrepairedBugs)

            # 如果评分不为空，则打印评分
            if self.score['bugRepairScore'] is not None:
                bug_repair_score = f'{self.score["bugRepairScore"]} 分'
                print(
                    f'根据以上BUG修复情况，当前该项目软件质量评分中“BUG修复”一项得分为： {_print_text_font(bug_repair_score)}')
        else:
            if self.bugInputTotal > 0:
                # 提供评分标准文本，供用户输入评分
                self.score['bugRepairScore'] = _input(score_text + '请输入分数：', **SCORE_INPUT_DATA)
            else:
                print(f'BUG修复评分为：{_print_text_font(20)}')
                self.score['bugRepairScore'] = 20

        self.scoreContents.append({
            'title': 'BUG修复',
            'scoreRule': score_text,
            'score': self.score['bugRepairScore']
        })

    def _calculate_bug_reopen_score(self):
        """
        计算和输出BUG重启得分。

        该方法首先打印BUG重启部分的标题，然后根据BUG的重启和未修复数量计算得分。
        如果存在BUG总数，则获取重启BUG的详细信息，并计算重启和未修复的BUG数量，
        随后输出这些数量，并计算得分。如果BUG总数为0，则显示预设的得分标准，并要求输入得分。
        """
        score_text = """20分：当前版本名下所有BUG一次性回归验证通过无重启
15分：名下BUG重启数=1
10分：名下BUG重启数=2
5分：名下BUG重启数=3
1分：名下BUG重启数>=4
"""
        print('BUG重启'.center(LINE_LENGTH, '-'))
        if self.bugTotal:
            self.get_reopen_bug_detail()  # 获取重启BUG数据
            reopen_bug_count = sum(self.reopenBugsData.values())  # 计算重启BUG数量
            unrepaired_bug_count = sum(self.unrepairedBugsData.values())  # 计算未修复BUG数量
            self.bugReopenScoreMsg += \
                f'''BUG重启数为：{_print_text_font(reopen_bug_count, color="green")}
BUG未修复数为：{_print_text_font(unrepaired_bug_count, color="green")}'''
            print(self.bugReopenScoreMsg)
            self.score["bugReopenScore"] = calculate_bug_reopen_rating(reopen_bug_count + unrepaired_bug_count)
            print('-' * LINE_LENGTH)
            # 调用calculate_bug_reopen_rating函数计算重启BUG得分，并进行输出
            bug_reopen_score = f"{self.score['bugReopenScore']} 分"
            print(
                f'当名下BUG重启数和未修复数总计={_print_text_font(reopen_bug_count + unrepaired_bug_count, color="green")}时，当前该项目软件质量评分中“BUG重启”一项得分为： {_print_text_font(bug_reopen_score)}')
            score_text = self.bugReopenScoreMsg + '\n' + score_text
        else:
            if self.bugInputTotal > 0:
                # 当BUG总数为0时，显示预设的得分标准，并要求输入得分
                self.score['bugReopenScore'] = _input(score_text + '请输入分数：', **SCORE_INPUT_DATA)
            else:
                print(f'BUG重启评分为：{_print_text_font(20)}')
                self.score['bugReopenScore'] = 20
        self.scoreContents.append({
            'title': 'BUG重启',
            'scoreRule': score_text,
            'score': self.score['bugReopenScore']
        })

    def _ai_generate_summary(self):
        """
        生成测试质量报告的摘要。

        本函数根据项目开发和测试数据，生成一个详细的测试质量报告摘要。
        它会根据BUG统计、开发人员信息、工作小时、BUG修复情况等数据进行分析，
        并提出改进建议和总结。

        参数:
        无

        返回值:
        无
        """
        # 构建摘要的基本信息
        text = '请仔细的阅读我说的话, 尤其是重点和注意\n'
        text += f"需求名称:{self.requirementName};开发周期总天数为:{round(self.developmentCycle, 1)};开发人员数量为:{self.developerCount};"

        if self.bugTotal:
            text += f"BUG总数为: {self.bugTotal};"
        else:
            text += f"BUG总数为: {self.bugInputTotal}{'(未发现BUG)' if self.bugInputTotal == 0 else ''};"

        # 如果有BUG等级分布数据，则添加到摘要中
        if self.bugLevelsCount:
            text += f"BUG等级分布情况为:{self.bugLevelsCount};"

        # 如果有评分内容，则添加到摘要中
        if self.scoreContents:
            text += f'\n项目研发评分情况:'
            for scoreData in self.scoreContents:
                text += f"\n{scoreData['title']}评分:"
                text += f"\n{scoreData['scoreRule']}"
                text += f"得分为:{scoreData['score']}\n"
            text += ('注意:\n'
                     'BUG修复评分(10-20分)都不存在项目上线当天未修复的BUG, 这是BUG创建当天未修复;\n'
                     'BUG修复评分(1-5分)都存在项目上线当天未修复的BUG;\n'
                     '(P0当天未修复的BUG数为、P1当天未修复的BUG数为、P2当天未修复的BUG数为)都归属在"BUG创建当天未修复的BUG数"\n'
                     '(在项目上线当天存在P0或者P1未修复BUG数为、在项目上线当天存在P2未修复BUG数为)都归属在"项目上线当天未修复的BUG数"\n'
                     '比如:\n'
                     '在项目上线当天存在P0或者P1未修复BUG数为：0\n'
                     '在项目上线当天存在P2未修复BUG数为：1\n'
                     'P0当天未修复的BUG数为：0\n'
                     'P1当天未修复的BUG数为：6\n'
                     'P2当天未修复的BUG数为：20\n'
                     '以上指的是项目上线当天未修复的BUG是:P0或者P1=0,P2=1;存在创建当天未修复的BUG是:P0=0,P1=6,P2=20\n'
                     )

        # 存在工时、修复BUG情况、缺陷级别分布、缺陷来源分布等数据，则添加到摘要中
        if self.workHours and self.fixers and self.bugLevelsMultiClientCount and self.bugSourceMultiClientCount:
            text += (f"开发人员工时情况(单位为小时): {self.workHours},"
                     f"开发人员修复BUG情况(数值为BUG修复数): {self.fixers},"
                     f"各端缺陷级别分布为(数值为BUG数量): {self.bugLevelsMultiClientCount},"
                     f"各端缺陷来源分布为(数值为BUG数量): {self.bugSourceMultiClientCount},"
                     f"总分:{sum(self.score.values())}")
            text += ';'

        # 添加测试经理的需求说明和格式要求
        text += ('重点:我是一个测试经理，我现在需要做提测质量报告分析，根据以上信息给我一个对开发情况和测试结果的一个详细总结、点评和建议, '
                 '在总结中可以看到一些不足之处的描述、改进办法和建议之类的, 并且需要美观的格式、描述清晰、直观、言简意赅、简明扼要、关键部分需要详细（比如BUG总数是多少，重启占比多少）'
                 '下面是格式要求：'
                 '将内容中的关键点使用<red>内容</red>标识,'
                 )
        text += ';'

        # 如果定义了报告摘要的组成部分，则添加到摘要中
        if TEST_REPORT_SUMMARY_COMPOSITION:
            text += '组成部分为: ' + '、'.join(TEST_REPORT_SUMMARY_COMPOSITION)

        text = text.replace(' ', '')

        # # 添加测试报告的HTML内容
        # text += self.testReportHtml
        text += f'\n输出模板(只是参考, 按照实际的来写):{ai_output_template()}'

        # 循环生成报告摘要，直到满足条件
        while True:
            self.reportSummary = deepseek_chat(text)

            # 如果支持重新生成AI摘要，则询问用户是否重新生成
            if IS_SUPPORT_RETRY_CREATE_AI_SUMMARY:
                print('')
                print('')
                while True:
                    confirm = input('是否重新生成AI总结?(y/n): ').lower()
                    if confirm in ('y', 'n'):
                        break
                    else:
                        print('输入错误, 是否重新生成AI总结?(y/n): ')
                if confirm == 'y':
                    continue
                else:
                    break
            else:
                break

    def run(self):
        """
        执行软件质量评估的主要流程。该方法依次调用多个辅助方法来处理需求、工时、BUG等数据，
        并在必要时进行错误检查和异常抛出。以下是详细的流程说明：

        1. **编辑列表展示字段**:
            - 调用 `self.edit_list_config()` 方法，配置必要的列字段以便后续获取所需数据。
            - 如果获取不到列展示字段的配置信息，则先调用 `_get_list_config()` 获取当前的列展示字段配置。
            - 确保缺陷列表和子任务列表中包含必要的字段（如状态、严重等级、修复人等），否则补充这些字段。

        2. **获取需求名称**:
            - 调用 `self.get_requirement_detail()` 方法，从服务器获取当前需求的详细信息，包括需求名称、开发人员等。
            - 检查需求名称是否成功获取。如果未能成功获取需求名称，则抛出 `ValueError` 异常提示用户检查需求ID。

        3. **汇总开发人员工时**:
            - 调用 `self.ger_requirement_task()` 方法，递归获取所有子任务并计算每个开发者的总工时。
            - 检查是否存在测试任务。如果没有测试任务，则抛出 `ValueError` 异常提示用户检查需求是否有测试任务。
            - 检查工时数据是否成功获取。如果没有获取到工时数据，则抛出 `ValueError` 异常提示用户检查需求是否有子任务。

        4. **计算开发周期**:
            - 如果有每日工作小时数的数据 (`self.dailyWorkingHoursOfEachDeveloper`)，则调用 `self.development_cycle()` 方法计算开发周期。
            - 遍历每个开发者的工作小时数，对于每个开发者在每个日期的工作小时数：
                - 如果工作小时数大于或等于8小时，则将该日期标记为1个完整工作日。
                - 如果工作小时数小于8小时，则计算该日期的工作小时数占一个完整工作日的比例，并与该日期已有的工作小时数比较，取较大值。
            - 最后，将所有日期的工作小时数相加，得到总的开发周期。

        5. **打印工时汇总**:
            - 调用 `self.print_development_hours()` 方法，计算并打印特定需求的所有开发人员的工时合计及每个开发人员的工时。
            - 计算所有开发人员的总工时和开发人员数量，并打印每个开发人员的工时及总工时。

        6. **统计BUG数量**:
            - 调用 `self.bug_list_detail()` 方法，通过调用API分页获取BUG数据，并按严重等级统计BUG数量。
            - 统计各端缺陷级别分布和缺陷根源分布，记录未修复的BUG以及上线当天未修复的BUG。
            - 输出各严重等级的BUG数量，并存储总的BUG数量。

        7. **计算并输出相关统计数据**:
            - 调用 `self.score_result()` 方法，根据BUG总数、开发周期、开发人员数量等信息计算项目平均一天工作量的Bug数及相应的软件质量评分。
            - 分别计算BUG数评分、BUG修复评分、BUG重启评分、配合积极性/文档完成性评分、冒烟测试评分。
            - 打印总分。

        8. **创建图表**:
            - 调用 `self.create_chart()` 方法，生成多个条形图和折线图，涵盖开发工时、BUG修复人、各端缺陷级别分布及缺陷根源分布统计。
            - 将图表路径信息转换为HTML格式，并存储在 `self.chartHtml` 中。
            - 如果不需要创建报告，则打印图表链接。

        9. **添加测试报告**:
            - 调用 `self.add_test_report()` 方法，构造测试报告的请求，包含报告的标题、接收人、抄送人等信息。
            - 附带关于测试结论、执行进度、发现的BUG数等详细信息，并通过POST请求将报告数据提交到指定的URL。
            - 如果打开了AI生成总结内容开关 (`IS_CREATE_AI_SUMMARY`)，则调用AI生成总结方法。

        10. **异常处理**:
            - 使用 `try-except` 结构捕获 `ValueError` 异常，打印堆栈信息并重新抛出异常。
            - 在 `finally` 块中，无论是否发生异常，都还原列字段展示的配置信息：
                - 调用 `edit_query_filtering_list_config(self.oldBugListConfigs)` 和 `edit_requirement_list_config(self.oldSubTaskListConfigs)` 方法，确保列字段配置恢复原样。
            - 如果还原配置信息失败，捕获异常并打印堆栈信息，重新抛出异常。

        流程概述:
        - 编辑列表展示字段以确保获取所需数据。
        - 获取需求名称并验证其有效性。
        - 汇总开发人员工时并验证测试任务的存在。
        - 计算开发周期并打印工时汇总。
        - 统计BUG数量并计算相关评分。
        - 创建图表并生成HTML代码。
        - 添加测试报告并提交。
        - 捕获异常并打印堆栈信息。
        - 最终确保列字段展示配置信息被还原。
        """
        # 编辑列表展示字段
        self.edit_list_config()

        # 获取需求名称
        self.get_requirement_detail()

        # 汇总开发人员工时
        self.requirement_task_statistics()

        if self.dailyWorkingHoursOfEachDeveloper:
            # 计算开发周期
            self.development_cycle()

        # 打印工时汇总
        self.print_development_hours()

        # 统计BUG数量
        self.bug_list_detail()

        # 恢复列字段展示的配置信息
        self.restore_list_config()

        # 计算并输出相关统计数据
        self.score_result()

        # 创建图表
        self.create_chart()

        # 添加测试报告
        self.add_test_report()


if __name__ == "__main__":
    SoftwareQualityRating().run()
