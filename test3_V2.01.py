# 2025年3月9日00:35:14

"""
1、加入各大评分项的分数以及内容传给ds进行分析
2、分析结果汇总全部放进测试报告里的“总结”后
3、针对每个图标相关的代码和数据，一个一个的丢给DS进行分析
4、最后统筹加入优化代码  添加注释
"""

# 导入必要的库
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from openai import OpenAI
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

IS_CREATE_REPORT = False  # 是否创建报告
IS_CREATE_AI_SUMMARY = False  # 是否创建AI总结
IS_SUPPORT_RETRY_CREATE_AI_SUMMARY = True  # 是否支持重试创建AI总结, 生成完成后可input进行重新生成
OPEN_AI_MODEL = '百炼v3'  # deepseek模型名称，目前支持：v3、r1、百炼r1、百炼v3
# OPEN_AI_KEY = 'sk-00987978d24e445a88f1f5a57944818b'  # OpenAI密钥  deepseek官方
# OPEN_AI_URL = 'https://api.deepseek.com/v1'  # OpenAI的URL  deepseek官方
OPEN_AI_KEY = 'sk-a5ae4633515d448e9bbbe03770712d4e'  # OpenAI密钥  百炼
OPEN_AI_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'  # OpenAI的URL  百炼r1
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

# 创建一个CloudScraper实例，用于模拟浏览器请求
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',  # 模拟的浏览器类型为Chrome
        'platform': 'windows',  # 模拟的平台为Windows
        'desktop': True,  # 模拟桌面环境，而非移动设备
    }
)

# matplotlib.use('Agg')

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
            range_max, y_interval = calculation_plot_y_max_height(max_bar_height)

            # 设置Y轴刻度位置及标签
            plt.yticks(
                range(0, range_max + 1, y_interval),  # 生成等间隔刻度位置
                labels=[str(x) for x in range(0, range_max + 1, y_interval)]  # 生成纯数字标签
            )

            # 设置y轴的最大值
            max_height = range_max

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
            error_detail = f"无法将输入 '{raw_input}' 转换为 {type_name} 类型"
            print(_print_text_font(f"\n格式错误：{error_detail}\n", color='red'))

        except Exception as e:  # 防御性编程，捕获其他未预料异常
            # 打印通用错误提示（理论上不会执行到这里）
            print(_print_text_font("\n发生未预期的错误，请重新输入\n", color='red'))


def _print_text_font(text: str, is_weight: bool = False, color: str = 'red') -> str:
    """
    生成带有指定颜色和字重的ANSI转义序列格式化文本

    该函数通过ANSI转义码实现在终端输出彩色文本，支持8种基础颜色和字体加粗效果。
    返回的字符串可直接用于print()函数，在支持ANSI转义的终端中显示彩色文本。

    参数详解:
        text (str):
            需要格式化的文本内容。支持任意字符串，包含多行文本和特殊字符。
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
        requests.HTTPError: HTTP状态码非2xx时抛出
        ValueError: 响应数据解析异常时抛出
        KeyError: 响应数据结构缺失关键字段时抛出

    实现逻辑:
        1. 动态构建API请求URL和鉴权参数
        2. 通过统一请求方法fetch_data发送GET请求
        3. 校验响应状态码和数据完整性
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

    try:
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

        # 显式检查HTTP状态码（fetch_data已处理非200状态码，此处为防御性校验）
        # 触发HTTPError时将中断流程
        response.raise_for_status()

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


def get_requirement_list_config():
    """
    获取tapd需求列表展示的列字段信息, 用于编辑列字段配置
    :return: 已json格式返回接口响应的data信息
    """
    url = HOST + '/api/basic/userviews/get_show_fields'
    params = {
        "id": REQUIREMENT_LIST_ID,
        "workspace_id": PROJECT_ID,
        "location": "/prong/stories/stories_list",
        "form": "show_fields",
    }
    response = fetch_data(url, params=params, method='GET').json()
    if response and response.get('data', dict).get('fields', list):
        return response['data']['fields']
    else:
        return


def edit_requirement_list_config(custom_fields: str):
    """
    编辑"需求"列表中展示的列字段
    :param custom_fields: 配置需要展示出来的列字段, 示例: id;title;name;status
    :return: 如果接口返回成功时, 返回True, 否则False
    """
    url = HOST + '/api/basic/userviews/edit_show_fields'
    data = {
        "id": REQUIREMENT_LIST_ID,
        "custom_fields": custom_fields,
        "workspace_id": PROJECT_ID,
        "location": "/search/get_all/bug",
    }
    response = fetch_data(url, json=data, method='POST').json()
    if response and response.get('meta', {}).get('message', str) == 'success':
        return True
    else:
        return False


def get_query_filtering_list_config():
    """
    获取tapd"查询过滤"列表展示的列字段信息, 用于编辑列字段配置
    :return: 已json格式返回接口响应的data信息
    """
    url = HOST + '/api/search_filter/search_filter/get_show_fields'
    data = {
        "workspace_ids": [
            PROJECT_ID
        ],
        "location": "/search/get_all/bug",
        "form": "show_fields",
    }
    response = fetch_data(url, json=data, method='POST').json()
    if response and response.get('data', dict).get('fields', list):
        return response['data']['fields']
    else:
        return


def edit_query_filtering_list_config(custom_fields: str):
    """
    编辑"查询过滤"列表中展示的列字段
    :param custom_fields: 配置需要展示出来的列字段, 示例: id;title;name;status
    :return: 如果接口返回成功时, 返回True, 否则False
    """
    url = HOST + '/api/search_filter/search_filter/edit_show_fields'
    data = {
        "custom_fields": custom_fields,
        "location": "/search/get_all/bug",
    }
    response = fetch_data(url, json=data, method='POST').json()
    if response and response.get('meta', {}).get('message', str) == 'success':
        return True
    else:
        return False


def get_user_detail():
    """
    获取当前用户信息
    :return: 用户信息
    """
    # 获取用户信息的URL
    url = HOST + '/api/aggregation/user_and_workspace_aggregation/get_user_and_workspace_basic_info'

    # 发送GET请求并获取响应数据，然后将其解析为JSON格式
    response = fetch_data(url, method='GET').json()

    # 返回解析后的JSON数据
    return response


def fetch_data(url, params=None, data=None, json=None, files=None, method='GET'):
    """
    发送HTTP请求并处理响应。

    本函数根据指定的URL和请求方法发送HTTP请求，并处理可能的请求失败情况。
    如果请求失败，将重试最多3次。如果重试次数超过3次，程序将退出。

    参数:
    - url (str): 目标URL。
    - params (dict, optional): URL参数。
    - data (dict, optional): 发送的数据，适用于POST请求。
    - json (dict, optional): 发送的JSON数据，适用于POST请求。
    - files (dict, optional): 发送的文件，适用于POST请求。
    - method (str, optional): 请求方法，默认为'GET'。

    返回:
    - response: HTTP响应对象。
    """
    # 初始化重试计数
    retry_count = 0
    # 无限循环，直到成功或失败退出
    while retry_count <= 3:
        # 如果重试次数在1到3之间，打印重试信息
        if retry_count > 0:
            print(f'正在重试请求(重试{retry_count}次): {url}')
        try:
            # 根据请求方法发送HTTP请求
            response = scraper.request(method, url, params=params, data=data, json=json, files=files)
            # 检查响应状态码
            response.raise_for_status()
        # 捕获HTTP请求异常
        except requests.RequestException as e:
            # 打印错误信息
            print(f"请求失败: {e}")
            # 更新重试计数
            retry_count += 1
        else:
            # 检查响应状态码以确定是否需要更新cookie
            if response.status_code == 403 or (
                    response.status_code == 200 and "meta" in response.text and "20002" in response.text):
                print('cookie已失效, 正在获取新的cookie')
                # 调用get_session_id函数以获取新的cookie
                get_session_id()
                print('cookie已更新')
                # 更新重试计数
                retry_count += 1
            else:
                # 如果重试次数大于0，打印重试成功信息
                if retry_count > 0:
                    print(f"重试请求成功: {url}")
                # 返回response 对象
                return response
    # 如果重试次数超过3次，打印错误信息并退出程序
    print(f"请求失败，重试次数过多，程序退出; url: {url}")
    sys.exit()


def _ai_result_label_switch_html_label(
        result: str,
        old_text: str = None,
        re_exp: str = None,
        new_text: str or list[str] or tuple[str] = None
) -> str:
    """
    根据给定的条件替换字符串中的特定文本。

    :param result: 原始结果字符串。
    :param old_text: 需要被替换的旧文本。
    :param re_exp: 正则表达式，用于匹配需要替换的文本。
    :param new_text: 替换后的文本，可以是字符串，也可以是包含两个字符串的列表或元组。
    :return: 替换后的结果字符串。
    """
    # 当提供了正则表达式和新的文本，并且新的文本是列表或元组时
    if re_exp and new_text is not None and isinstance(new_text, (list, tuple)):
        # 从正则表达式中提取需要替换的旧文本
        old_texts: list[str] = re_exp.replace('\\', '').split('.*?')
        # 使用正则表达式提取匹配的文本
        re_results: list[str] = extract_matching(re_exp, result)
        # 遍历匹配的文本，进行替换
        for reResult in re_results:
            re_result: str = reResult.replace(old_texts[0], '').replace(old_texts[1], '')
            result = result.replace(reResult, new_text[0] + re_result + new_text[1])
    # 当提供了旧文本和新的文本，并且新的文本是字符串时
    elif old_text and new_text is not None and isinstance(new_text, str):
        # 直接替换旧文本为新文本
        result = result.replace(old_text, new_text)
    # 返回替换后的结果
    return result


def ai_result_switch_html(result: str) -> str:
    """
    将AI结果中的特定文本格式转换为HTML格式。

    该函数通过一系列的文本替换操作，将AI输出结果中的特定文本标记转换为相应的HTML标签，
    以便在网页等环境中更好地显示和格式化这些结果。

    参数:
    result (str): AI输出的原始文本结果，包含特定的文本格式。

    返回:
    str: 转换为HTML格式后的文本结果。
    """
    # 移除井号，不进行文本替换，仅作为标记移除
    result = _ai_result_label_switch_html_label(result=result, old_text='#', new_text='')
    # 将换行符替换为HTML的换行标签，以在网页中正确显示换行
    result = _ai_result_label_switch_html_label(result=result, old_text='\n', new_text='<br/>')
    # 将三个短横线替换为HTML的水平线标签，用于分隔内容
    result = _ai_result_label_switch_html_label(result=result, old_text='---', new_text='<hr>')
    # 将空格替换为HTML的非断行空格实体，以在网页中正确显示空格
    result = _ai_result_label_switch_html_label(result=result, old_text=' ', new_text='&nbsp;')
    # 将制表符替换为四个非断行空格实体，以近似表示制表符的缩进效果
    result = _ai_result_label_switch_html_label(result=result, old_text='\t', new_text='&nbsp;' * 4)
    # 将<red>...</red>标记内的文本转换为红色显示，增加视觉强调效果
    result = _ai_result_label_switch_html_label(
        result=result,
        re_exp=r'<red>.*?</red>',
        new_text=('<span style="color:#ff3b30;">', '</span>')
    )
    # 将三个星号包围的文本转换为HTML的三级标题，提高文本的层次感
    result = _ai_result_label_switch_html_label(
        result=result,
        re_exp=r'\*\*\*.*?\*\*\*',
        new_text=('<h3>', '</h3>')
    )
    # 将两个星号包围的文本转换为HTML的粗体文本，增强文本的强调效果
    result = _ai_result_label_switch_html_label(
        result=result,
        re_exp=r'\*\*.*?\*\*',
        new_text=('<b>', '</b>')
    )
    # 返回转换完成的HTML格式文本
    return result


def ai_output_template() -> str:
    template = """***一、总体评价***
▶ 项目最终评分为XX分（满分100），整体质量处于XX水平。XXXXXXXXXXXXXXXXXXXX
---
***二、核心亮点***
▶ **XXXXXX**：XXXXXXXX
▶ **XXXXXX**：XXXXXXXX
---
***三、主要不足与改进建议***
▶ **XXXXXXX**
    ▷ XXXXXXXXXX
    ▷ <red>建议</red>：XXXXXXXXXXXX
▶ **XXXXXXX**
    ▷ XXXXXXXXXX
    ▷ <red>建议</red>：XXXXXXXXXXXX
▶ **XXXXXXX**
    ▷ XXXXXXXXXX
    ▷ <red>建议</red>：XXXXXXXXXXXX
---
***四、后续优化重点***
▶ **XXXXXXXX**：XXXXXXXX
▶ **XXXXXXXX**：XXXXXXXX
---
***五、风险预警***
▶ XXXXXXXXXXXXXXXXX"""
    return template


def deepseek_chat(content: str):
    """
    根据用户输入的内容，使用DeepSeek模型生成回复。

    参数:
    content (str): 用户输入的内容。

    返回:
    str: 由DeepSeek模型生成的回复内容，经过HTML转义。
    """
    # 初始化结果变量和模型变量
    result = ''
    model = ''
    # 打印用户输入的内容
    print(content)
    open_ai_model = OPEN_AI_MODEL.lower()
    # 根据环境变量OPEN_AI_MODEL的值选择合适的模型
    if open_ai_model == 'v3':
        model = 'deepseek-chat'
    elif open_ai_model == 'r1':
        model = 'deepseek-reasoner'
    elif open_ai_model == '百炼r1':
        model = 'deepseek-r1'
    elif open_ai_model == '百炼v3':
        model = 'deepseek-v3'

    # 如果模型变量为空，说明OPEN_AI_MODEL配置错误
    if not model:
        print('OPEN_AI_MODEL配置错误')
        return result

    # 初始化OpenAI客户端
    client = OpenAI(
        api_key=OPEN_AI_KEY,
        base_url=OPEN_AI_URL
    )

    # 打印模型生成开始的提示信息
    print(f'{model}生成中, 请稍等...')
    # 创建chat completion
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'user', 'content': content}
        ],
        stream=OPEN_AI_IS_STREAM_RESPONSE,  # 流式响应开关，True=流式响应，False=普通响应
        # temperature=0.1,  # 模型采样温度，取值范围[0,1]，越小越 deterministic，越大越 stochastic。
        # top_p=0.5,  # 模型采样 nucleus probability，取值范围[0,1]，越大越 stochastic。
        # max_tokens=1024,  # 最大输出长度，取值范围[1, 4096]。
    )

    # 根据是否是流式响应，选择不同的处理方式
    if OPEN_AI_IS_STREAM_RESPONSE:
        # 初始化标志变量
        is_reasoning_content: bool = False
        is_content: bool = False
        # 处理流式响应
        for chunk in completion:  # 流式响应用这个
            response_delta = dict(chunk.choices[0].delta)
            reasoning_content: str = response_delta.get('reasoning_content')
            content: str = chunk.choices[0].delta.content
            # 处理思考过程内容
            if reasoning_content is not None:
                if not is_reasoning_content:
                    is_reasoning_content = True
                    print('\n\n思考过程：')
                print(reasoning_content, end='')
            # 处理最终答案内容
            if content is not None:
                if not is_content:
                    is_content = True
                    print('\n\n最终答案：')
                print(content, end='')
                result += content
    else:
        # 处理非流式响应
        # 打印思考过程
        print("\n思考过程：")
        print(completion.choices[0].message.reasoning_content)
        # 打印最终答案
        print("\n最终答案：")
        result += completion.choices[0].message.content
        print(result)

    # 返回经过HTML转义的结果
    return ai_result_switch_html(result)


def extract_matching(pattern, owner):
    """
    使用正则表达式提取文本中匹配的模式。

    参数:
    pattern (str): 正则表达式模式，用于定义需要提取的字符串格式。
    owner (str): 要从中提取匹配模式的文本内容。

    返回:
    list: 包含所有匹配模式的字符串列表。
    """
    # 编译正则表达式模式以提高效率
    regex = re.compile(pattern)
    # 使用编译后的正则表达式查找所有匹配项
    match = regex.findall(owner)
    # 返回所有匹配项的列表
    return match


def get_days(start_date, end_date, is_workday=True):
    """
    获取指定日期范围内的所有日期或工作日。

    :param start_date: 起始日期，可以是字符串或date对象
    :param end_date: 结束日期，可以是字符串或date对象
    :param is_workday: 是否仅返回工作日，默认为True
    :return: 日期列表，根据is_workday参数决定是否包含所有日期或仅工作日
    """
    # 如果输入的日期是字符串，则将其转换为date对象
    if isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    # 如果输入的日期是字符串，则将其转换为date对象
    if isinstance(end_date, str):
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    # 创建一个生成器，用于遍历给定范围内的所有日期
    days = [start_date + datetime.timedelta(n) for n in range((end_date - start_date).days + 1)]
    # 如果仅返回工作日，则过滤掉非工作日
    if is_workday:
        days = [datetime.datetime.strftime(day, '%Y-%m-%d') for day in days if calendar.is_workday(day)]
    # 返回日期列表
    return days


def encrypt_password_zero_padding(password):
    """
    使用AES加密算法和零字节填充技术来加密密码。

    该函数首先生成一个随机密钥和一个随机IV（初始化向量）。然后，它创建一个AES加密器对象。
    接着，它对输入的密码进行零字节填充，以确保其长度是AES块大小的倍数。最后，它使用加密器对象加密
    填充后的密码，并返回加密后的密码、IV和密钥，所有这些都经过了Base64编码。

    参数:
    password (str): 需要加密的密码。

    返回:
    dict: 包含加密后的密码、IV和密钥的字典，所有这些都经过了Base64编码。
    """
    # 生成随机密钥和IV
    key = os.urandom(32)
    iv = os.urandom(16)

    # 创建AES加密器对象
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    # 创建加密器对象
    encryptor = cipher.encryptor()

    # 使用零字节填充技术对密码进行填充
    block_size = algorithms.AES.block_size // 8
    # 填充密码
    padded_data = password.encode('utf-8') + b'\x00' * (block_size - len(password) % block_size)
    # 加密数据
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # 返回Base64编码后的密文、IV和密钥
    return {
        'data[Login][password]': base64.b64encode(ciphertext).decode('utf-8'),
        'data[Login][encrypt_iv]': base64.b64encode(iv).decode('utf-8'),
        'data[Login][encrypt_key]': base64.b64encode(key).decode('utf-8')
    }


def switch_numpy_data(data: dict) -> tuple:
    """
    将给定的字典数据转换为NumPy数组，同时提取并生成对应的标签。

    参数:
    data: dict - 包含数据的字典，其中值可以是字典或数字。

    返回:
    tuple - 包含标签列表和转换后的NumPy数组的元组。
    """
    # 初始化标签列表
    labels: list[str] = []
    # 初始化新的数据字典，用于存储转换后的数据
    new_data: dict[str, list[int or float]] = {}

    # 遍历原始数据字典的值
    for value in data.values():
        # 如果值是一个字典，则进一步处理
        if isinstance(value, dict):
            # 遍历子字典的键值对
            for subKey, subValue in value.items():
                # 如果子键不在标签列表中，则添加到列表中
                if subKey not in labels:
                    labels.append(subKey)
                # 如果当前子键对应的列表不存在，则初始化
                if not new_data.get(subKey):
                    new_data[subKey] = []
                # 将子值添加到对应子键的列表中
                new_data[subKey].append(subValue)
        # 如果值是一个整数或浮点数，则将其添加到特殊键'_'对应的列表中
        elif isinstance(value, int) or isinstance(value, float):
            # 如果特殊键'_'对应的列表不存在，则初始化
            if not new_data.get('_'):
                new_data['_'] = []
            # 将值添加到特殊键'_'对应的列表中
            new_data['_'].append(value)
    # 将新数据字典的值转换为NumPy数组
    np_data = np.array(list(new_data.values()))
    # 返回标签列表和转换后的NumPy数组
    return labels, np_data


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
    return range_max, y_interval


def calculate_plot_width(keys: list, fig: plt.Figure, bar_width: float = 0.073):
    """
    根据名称列表和图形对象来计算和设置柱状图的宽度。

    :param keys: 名称列表，用于确定柱状图的名称长度和数量。
    :param fig: matplotlib 图形对象，用于设置图形的宽度。
    :param bar_width: 单个柱子的基础宽度。
    :return: 返回调整后的柱子宽度和图形宽度的字典。
    """
    # 计算最长的名称长度
    max_key_length = max(len(key) for key in keys)
    # 获取柱状图数据的数量
    num_bars = len(keys)

    # 根据最长名称长度和柱子数量调整图形宽度
    base_width = 0  # 基础宽度
    # 名称长度影响因子
    key_length_factor = max_key_length * 1.0
    # 柱子数量影响因子
    bar_count_factor = num_bars * 0.3

    # 设置图片最小宽度和最大宽度
    min_width = 9
    max_width = 20
    # 计算最终的宽度
    desired_width = min(max(base_width + key_length_factor + bar_count_factor, min_width), max_width)

    # # 设置柱子最小宽度和最大宽度
    # bar_max_width: float = 0.13

    # 计算最终的柱子宽度
    # if num_bars == 1:
    #     desired_bar_width = bar_width
    # else:
    #     # desired_bar_width = bar_width + (bar_width * (1 / num_bars))
    #     # desired_bar_width = 0.24
    #     desired_bar_width = 0.36
    desired_bar_width = bar_width + num_bars * 0.057

    # 设置图形的尺寸
    fig.set_size_inches(desired_width, 4.8)

    # 设置 x 轴的限制
    plt.xlim(-1, num_bars)

    # 返回调整后的柱子宽度和图形宽度的字典
    return desired_bar_width, {'width': desired_width}


@create_plot
def create_bar_plot(title, data: dict):
    """
    创建一个条形图。

    参数:
    - title: 图表的标题。
    - data: 包含图表数据的字典，其中键是类别名称，值是每个类别的数值列表。

    返回:
    - desired_width_data: 计算出的图表宽度数据。
    - labels: 图表的标签列表。
    - title: 图表的标题。
    - max_total_height: 最大条形的总高度。
    - ax: matplotlib Axes对象，用于绘制图表。
    """
    # 获取数据的键，即类别名称
    keys = list(data.keys())

    # 创建图表对象
    fig, ax = plt.subplots()
    # 类型注释，帮助IDE和代码阅读者理解变量类型
    fig: plt.Figure
    ax: plt.Axes

    # 计算理想的条形宽度和图表宽度数据
    desired_bar_width, desired_width_data = calculate_plot_width(keys, fig)
    # 类型注释
    desired_bar_width: float
    desired_width_data: dict

    # 将数据转换为numpy数组，便于处理，并获取标签
    labels, np_data = switch_numpy_data(data)
    # 类型注释
    labels: list[str]
    np_data: np.ndarray
    # 计算每个类别条形的总高度
    np_data_heights = np_data.sum(axis=0)

    # 初始化底部位置，用于堆叠条形图
    bottoms = np.zeros(len(keys))

    # 遍历每个数据序列，绘制堆叠条形图
    for i in range(len(np_data)):
        bars = ax.bar(
            keys,  # x轴名称
            np_data[i],  # 数据值
            width=desired_bar_width,  # 柱子宽度
            bottom=bottoms,  # 底部位置
            color=PLOT_COLORS[i],  # 柱子颜色
            label=labels[i] if labels else None,  # 条形标签, 如果labels为空，则不显示标签
        )
        # 更新底部位置
        bottoms += np_data[i]
        # 如果有多个数据序列，为每个条形添加数值标签
        if len(np_data) > 1:
            for index, bar in enumerate(bars):  # 遍历每个条形
                yval = int(bar.get_height())  # 获取条形的高度
                if yval and yval != np_data_heights[index]:  # 如果高度不为0且不等于总高度，则添加数值标签
                    # 添加数值标签, 设置位置和颜色等属性
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_y() + yval / 2, str(yval),
                            ha='center', va='center', color='white', fontsize=9)

    # 计算每个类别的总高度
    total_heights = np.sum(np_data, axis=0)
    # 为每个类别添加总高度的标签
    for i, total_height in enumerate(total_heights):
        if total_height:
            ax.text(keys[i], total_height, round(total_height, 2), ha='center', va='bottom')
    # 返回相关数据和图表对象
    return {
        'desiredWidthData': desired_width_data,
        'labels': labels,
        'title': title,
        'maxBarHeight': int(max(total_heights)),
        'ax': ax,
    }


@create_plot
def create_broken_line_plot(title, data: dict):
    """
    创建折线图。

    对给定的数据进行排序，并将其转换为适合numpy的数据格式。然后在创建的图表上绘制折线图，并对其进行注释。

    参数:
    - title: 图表的标题。
    - data: 包含折线图数据的字典，键为时间点，值为各个标签的数据。

    返回:
    - desired_width_data: 计算出的图表宽度数据。
    - labels: 图表折线的标签列表。
    - title: 图表的标题。
    - max_value: 数据中的最大值。
    - ax: matplotlib的Axes对象，用于绘制图表。
    """
    # 对数据进行排序，以确保时间线上的数据是有序的
    data = dict(sorted(data.items()))
    keys = list(data.keys())

    # 将数据转换为适合numpy的数据格式
    labels, np_data = switch_numpy_data(data)
    labels: list[str]
    np_data: np.ndarray

    # 创建图表
    fig, ax = plt.subplots()
    fig: plt.Figure
    ax: plt.Axes

    # 计算图表的宽度
    desired_bar_width, desired_width_data = calculate_plot_width(keys, fig)

    # 初始化已注释点的集合，避免重复注释
    annotated_points = set()

    # 遍历每一条折线，进行绘制和注释
    for index in range(len(labels)):
        ax.plot(
            keys,  # x轴数据
            np_data[index],  # y轴数据
            marker='o',  # 点的形状
            label=labels[index],  # 折线标签
        )
        # 对每一个点进行检查和注释
        for i, (date, value) in enumerate(zip(keys, np_data[index])):
            point = (date, value)  # 点坐标
            if point not in annotated_points:  # 如果点没有被注释过，则进行注释
                ax.annotate(
                    f'{value}',  # 注释文本
                    (date, value - 0.5),  # 注释位置
                    textcoords="offset points",  # 坐标系
                    xytext=(0, 10),  # 注释偏移
                    ha='center',  # 水平居中
                    fontsize=9,  # 注释字体大小
                )
                annotated_points.add(point)  # 将点添加到已注释的点集合中

    # 返回相关数据和图表对象
    return {
        'desiredWidthData': desired_width_data,
        'labels': labels,
        'title': title,
        'maxBarHeight': np.max(np_data),
        'ax': ax,
    }


def upload_file(file):
    """
    上传文件到指定的URL，并返回上传后的文件路径或信息。

    参数:
    file (file-like object): 要上传的文件对象。

    返回:
    str: 上传成功后的文件路径或信息。
    """
    # 定义上传文件的URL
    url = 'https://tdl.tapd.cn/tbl/apis/qmeditor_upload.php'

    # 定义上传文件时携带的参数，包括相对路径、前缀等信息
    params = {
        "1": "1",
        "show_relative_path": "1",
        "relative_base_path": "/tfl/",
        "image_prefix": "tapd_63835346_",
        "ie_domain_fix": "itemRich"
    }

    # 将要上传的文件封装到字典中，以便后续使用multipart/form-data形式上传
    files = {"UploadFile": file}

    # 定义POST请求的data数据，包含操作模式、尺寸限制等参数
    data = {
        "sid": "sid",
        "fun": "add",
        "mode": "download",
        "widthlimit": "0",
        "heightlimit": "0",
        "sizelimit": "0",
    }

    # 发起POST请求上传文件，并获取响应对象
    upload_file_res = fetch_data(url=url, params=params, data=data, files=files, method='POST')

    # 从响应文本中提取匹配的文件路径或信息，并返回
    return extract_matching(r"\);</script>(.*?)$", upload_file_res.text)[0]


def date_time_to_date(date_time_str: str):
    """
    将日期时间转换为日期格式, 示例: 2024-10-12 20:52 --> 2024-10-12
    :param date_time_str: "2024-10-12 20:52"
    :return: "2024-10-12"
    """
    date_time = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
    return date_time.strftime('%Y-%m-%d')


def style_convert(style_data: dict):
    """
    接受样式参数dict, 转换成str
    :param style_data: 样式参数dict
    :return: 样式参数str
    """
    style_str = ''
    for key, value in style_data.items():
        style_str += f'{key}: {value};'
    return style_str


def multi_client_data_processing(
        result: dict,
        key: str or None,
        all_sub_key: list,
        sub_key: str or None,
        all_key: list = None
):
    """
    处理多客户端数据的函数，用于统计不同key和sub_key的出现次数。

    参数:
    - result: 一个字典，存储处理结果。
    - key: 主键，如果为None，则默认为'空'。
    - all_sub_key: 一个包含所有可能的子键的列表。
    - sub_key: 子键，如果为None，则默认为'空'。
    - all_key: 一个包含所有可能的主键的列表，用于初始化结果字典。

    返回值:
    无返回值，直接更新result字典。
    """

    # 初始化null_count，用于统计空子键的数量
    null_count = 0

    # 初始化key和sub_key，如果它们为None，则分别默认为'空'
    key = key if key else '空'
    sub_key = sub_key if sub_key else '空'

    # 如果子键为空，则增加null_count
    if sub_key == '空':
        null_count += 1

    # 如果all_key和result都存在，但result为空，则初始化result，确保每个主键和子键的计数都从0开始
    if all_key and not result:
        result.update({data: {data: 0 for data in all_sub_key} for data in all_key})

    # 检查当前key是否在result中，如果不在，则添加该key，并初始化其子键的计数
    if not result.get(key):
        result[key] = {data: 0 for data in all_sub_key}

    # 更新当前key和sub_key的计数
    result[key][sub_key] = result[key].get(sub_key, 0) + 1

    # 如果null_count大于0，则遍历result中的每个key，如果key对应的子键中没有'空'，则添加'空'的计数为0
    if null_count > 0:
        for key, value in result.items():
            if value.get('空') is None:
                value['空'] = 0


def dict_add_total(data: dict):
    """
    接受字典, 添加总数字段
    :param data: 字典
    :return: 添加总数后的字典
    """
    new_data = data.copy()
    new_data['总数'] = sum(data.values())
    return new_data


def get_system_name():
    """
    获取当前系统的名称。

    该函数通过调用platform.system()方法来获取当前系统的名称，
    并根据返回值判断是macOS系统还是Windows系统。

    Returns:
        str: 系统的名称，可能为'macOS'或'windows'。
    """
    # 获取当前系统的名称
    system_name = platform.system()
    # 判断系统名称并返回对应的系统标识
    if system_name == 'Darwin':
        return 'macOS'
    elif system_name == 'Windows':
        return 'windows'


class SoftwareQualityRating:
    def __init__(self):
        """
        初始化项目管理器类的构造方法。

        设置初始值和空数据结构，用于后续的项目管理操作。
        """
        # 初始化项目需求名称为空字符串
        self.requirementName = ''
        # 初始化产品经理为空字符串
        self.PM = ''
        # 初始化测试收件人员列表为空列表(用于在测试报告中填写的测试收件人员)
        self.testRecipient = []
        # 初始化测试人员列表为空字符串(用于在测试报告概要中填写的测试人员)
        self.testersStr = ''
        # 初始化开发人员列表为空列表
        self.developers = []
        # 初始化是否存在测试任务标志为False
        self.isExistTestTask = False
        # 初始化最早任务时间为None
        self.earliestTaskDate = None
        # 初始化最晚任务时间为None
        self.lastTaskDate = None
        # 初始化上线时间为None
        self.onlineDate = None
        # 初始化工作小时数的字典，用于记录各个开发者工作小时数
        self.workHours = {}
        # 初始化开发总小时数为0
        self.devTotalHours = 0
        # 初始化缺陷级别数量为空字典
        self.bugLevelsCount = {}
        # 初始化缺陷级别多端数量为空字典
        self.bugLevelsMultiClientCount = {}
        # 初始化缺陷根源数量为空字典
        self.bugSourceCount = {}
        # 初始化缺陷根源多端数量为空字典
        self.bugSourceMultiClientCount = {}
        # 初始化缺陷总数为0
        self.bugTotal = 0
        # 初始化缺陷输入总数为0
        self.bugInputTotal = 0
        # 初始化缺陷ID列表为空列表
        self.bugIds = []
        # 初始化重新打开的缺陷列表为空字典
        self.reopenBugsData = {}
        # 初始化未修复的缺陷列表为空字典
        self.unrepairedBugsData = {}
        # 初始化开发者数量为0
        self.developerCount = 0
        # 初始化每个开发者的工作小时为空字典
        self.dailyWorkingHoursOfEachDeveloper = {}
        # 初始化开发周期为0
        self.developmentCycle = 0
        # 初始化缺陷修复者信息为空字典
        self.fixers = {}
        # 初始化原的缺陷列表配置为空字符串
        self.oldBugListConfigs = ''
        # 初始化原的子任务列表配置为空字符串
        self.oldSubTaskListConfigs = ''
        # 初始化缺陷修复趋势为空字典
        self.dailyTrendOfBugChanges = {}
        # 初始化未修复的缺陷列表为空字典
        self.unrepairedBugs = {
            # 部署正式环境当天未修复的缺陷
            "deployProdDayUnrepaired": {
                "P0P1": [],  # 致命或严重缺陷
                "P2": [],  # 一般或其他缺陷
            },
            #  创建当天未修复的缺陷
            "onThatDayUnrepaired": {
                "P0": [],  # 致命缺陷
                "P1": [],  # 严重缺陷
                "P2": [],  # 一般或其他缺陷
            }
        }
        # 初始化评分结果
        self.score = {
            "positiveIntegrityScore": 0,
            "smokeTestingScore": 0,
            "bugCountScore": 0,
            "bugRepairScore": 0,
            "bugReopenScore": 0,
        }
        # 初始化评分结果内容
        self.scoreContents = []
        # 测试报告html
        self.testReportHtml = ''
        # 图表html
        self.chartHtml = ''
        # 缺陷数量分数描述
        self.bugCountScoreMsg = ''
        # 缺陷修复分数描述
        self.bugRepairScoreMsg = ''
        # 缺陷重新打开分数描述
        self.bugReopenScoreMsg = ''
        # 初始化报告总结内容为空字符串
        self.reportSummary = ''

    def get_requirement_detail(self):
        """
        获取需求的名称。

        本函数通过调用fetch_data函数，从指定的URL中以POST方法获取需求数据。
        需要传递项目ID和需求ID等参数来定位具体的需求信息。

        Raises:
            ValueError: 当没有成功获取到需求数据时抛出异常。
        """
        # 调用fetch_data函数获取需求数据。
        response = fetch_data(
            url=HOST + "/api/aggregation/story_aggregation/get_story_transition_info",
            json={
                "workspace_id": PROJECT_ID,
                "story_id": REQUIREMENT_ID,
            },
            method='GET'
        ).json()

        # 检查response是否为空，如果为空则抛出ValueError异常。
        if not response and response.get('data', {}):
            raise ValueError("需求数据获取失败")

        response_detail = response['data']['get_workflow_by_story']['data']['current_story']['Story']  # 获取需求详细信息
        self.requirementName = response_detail['name']  # 获取需求名称
        if response_detail.get('developer'):  # 如果开发者不为空，则将开发者列表添加到self.developers中
            if ';' in response_detail['developer']:  # 如果开发者列表中包含';'，则将开发者列表拆分为列表
                self.developers = response_detail['developer'].split(';')  # 将开发者列表拆分为列表
                del self.developers[-1]  # 删除列表中的最后一个空字符元素
            else:  # 如果开发者列表中不包含';'，则将开发者列表添加到self.developers中
                self.developers.append(response_detail['developer'])  # 将开发者列表添加到self.developers中
        self.PM = response_detail['creator'] if response_detail.get('creator') else ''  # 获取产品经理

    def ger_requirement_task(self):
        """
        获取开发任务信息并计算每个开发者的工时及开发周期。

        本函数通过调用API递归地获取所有子任务，计算每个开发者的总工时，
        并确定整个项目的开发周期（开始日期到结束日期）。
        """

        # 初始化页码和每页大小
        page = 1
        page_size = 100

        # 循环获取所有子任务
        while True:
            # 调用fetch_data函数获取子任务数据
            data = fetch_data(
                HOST + "/api/entity/stories/get_children_stories",
                {
                    "workspace_id": PROJECT_ID,
                    "story_id": REQUIREMENT_ID,
                    "page": page,
                    "per_page": page_size,
                    "sort_name": "due",
                    "order": "asc",
                }
            ).json()

            # 如果没有获取到数据或没有子任务数据，则打印错误信息并退出循环
            if not data or not data.get('data') or not data['data'].get('children_list'):
                print("数据获取失败或没有更多数据")
                break

            # 遍历子任务列表，获取每个任务的开发人员名称和工时
            for child in data['data']['children_list']:
                # 获取开发人员名称(带有部门名称)
                owner = child['owner'].replace(";", "")
                # 获取开发人员名称和工时
                processing_personnel = extract_matching(r"\d(.*?)$", owner)[0]
                # 获取完成的工时
                worked_hours = float(child.get('effort_completed', 0))

                # 获取任务的开始日期、结束日期
                begin = child.get('begin')
                due = child.get('due')

                # 如果处理人不在测试人员名单中，累加工时
                if processing_personnel and processing_personnel not in TESTERS:
                    # 将开发人员名称和工时保存到字典中
                    child['developerName'] = processing_personnel
                    # 将工时累加到字典中
                    self.workHours[processing_personnel] = self.workHours.get(processing_personnel, 0) + worked_hours
                    # 如果任务有开始日期、结束日期, 记录项目任务的最早日期和最晚日期
                    if begin and due:
                        if not self.earliestTaskDate or begin < self.earliestTaskDate:  # 如果当前任务的开始日期小于最早任务日期，则更新最早任务日期
                            self.earliestTaskDate = begin  # 更新最早任务日期
                        # 如果任务有开始日期、结束日期和完成工时，则保存到字典中
                        if child.get('effort_completed'):
                            # 调用_save_task_hours方法保存任务工时信息
                            self._save_task_hours(child)

                if processing_personnel in TESTERS:  # 如果处理人是测试人员，则更新开发周期
                    # 如果是第一次遇到测试任务，更新为存在测试任务标志
                    if not self.isExistTestTask:
                        self.isExistTestTask = True
                    if not self.lastTaskDate or due > self.lastTaskDate:  # 如果当前任务的结束日期大于最晚任务日期，则更新最晚任务日期
                        self.lastTaskDate = due  # 更新最晚任务日期
                    if not self.onlineDate or begin > self.onlineDate:  # 如果当前任务的开始日期大于上线日期，则更新上线日期
                        self.onlineDate = begin  # 更新上线日期
                    if owner not in self.testRecipient:  # 如果测试人员不在测试人员名单中，则添加到测试人员名单中
                        self.testRecipient.append(owner)  # 添加到测试人员名单中
            # 如果子任务列表的长度小于每页大小，则说明已经获取到了所有子任务，退出循环
            if len(data['data']['children_list']) < page_size:
                break

            # 增加页码
            page += 1

    def print_summary(self):
        """
        打印项目工时摘要。

        本函数计算并打印特定需求的所有开发人员的工时合计及每个开发人员的工时。
        它首先计算总工时和开发人员数量，然后打印出每个开发人员的工时及总工时。
        """
        # 计算所有开发人员的总工时
        self.devTotalHours = sum(self.workHours.values())
        # 计算开发人员的数量
        self.developerCount = len(self.workHours)
        # 打印分隔线，用于区分不同的摘要信息
        print('-' * LINE_LENGTH)
        # 打印需求ID和该需求下所有开发人员的工时信息
        print(f"需求 {REQUIREMENT_ID}: {self.requirementName} 各开发人员花费的工时：")
        # 遍历字典，打印每个开发人员的工时
        for developer, hours in self.workHours.items():
            print(f"{developer}: {hours} 小时")
        # 打印总工时
        print(f"工时合计：{self.devTotalHours} 小时")

    def bug_list_detail(self):
        """
        获取BUG列表详情

        通过调用API分页获取BUG数据，并按严重等级统计BUG数量。

        Attributes:
            page (int): 当前页码。
            page_size (int): 每页数据量。
            bugs (list): 用于存储所有BUG数据的列表。
        """
        # 初始化页码和每页大小，初始化bugs列表
        page = 1
        page_size = 100
        bugs = []
        platforms = []
        sources = []
        # 循环获取所有BUG数据
        while True:
            # 调用fetch_data函数获取BUG数据
            response = fetch_data(
                url=HOST + "/api/search_filter/search_filter/search",
                json={
                    "workspace_ids": PROJECT_ID,
                    "search_data": "{\"data\":[{\"id\":\"5\",\"fieldLabel\":\"关联需求\",\"fieldOption\":\"like\",\"fieldType\":\"input\",\"fieldSystemName\":\"BugStoryRelation_relative_id\",\"value\":\"" + self.requirementName + "\",\"fieldIsSystem\":\"1\",\"entity\":\"bug\"}],\"optionType\":\"AND\",\"needInit\":\"1\"}",
                    "obj_type": "bug",
                    "hide_not_match_condition_node": "0",
                    "hide_not_match_condition_sub_node": "1",
                    "page": page,
                    "perpage": str(page_size),
                    "order_field": "created",
                },
                method='POST'
            ).json()

            # 检查数据是否成功获取
            if not response.get('data', {}):
                print("BUG数据获取失败")
                # 退出循环
                return
            else:
                project_special_fields_dict = response.get('data').get('project_special_fields', {}).get(PROJECT_ID, {})
                if not platforms:
                    platforms = [platform['value'] for platform in project_special_fields_dict.get('platform', [])]
                if not sources:
                    sources = [platform['value'] for platform in project_special_fields_dict.get('source', [])]
                # 将获取到的BUG数据添加到bugs列表中
                bugs += response.get('data', {}).get('list', [])
                # 判断是否达到最后一页
                if len(response.get('data', {}).get('list', [])) < page_size:
                    # 退出循环
                    break
                else:
                    # 增加页码
                    page += 1

        print('-' * LINE_LENGTH)

        # 统计BUG数量
        if not bugs:  # 如果没有bug，则打印未获取BUG数量
            print('未获取BUG数量')
            return

        self.bugLevelsCount = {level: 0 for level in BUG_LEVELS}  # 初始化一个字典，用于存储每个严重等级下的BUG数量
        for bug in bugs:  # 遍历每个BUG
            bug_status = bug.get('status')
            if bug_status != 'rejected':  # 如果BUG的状态不是"已拒绝"
                bug_id = bug.get('id')  # 获取BUG的ID
                severity_name = bug.get('custom_field_严重等级')  # 获取BUG的严重等级名称
                bug_source = bug.get('source')  # 获取BUG的缺陷根源信息
                bug_field_level = bug.get('custom_field_Bug等级')  # 获取BUG的BUG等级
                bug_platform = bug['platform'] if bug.get('platform') else '空'  # 获取BUG的软件平台, 如果为空，则设置为'空'
                fixer = bug['fixer'] if bug.get('fixer') else '空'
                if severity_name:  # 如果严重等级名称不为空，则累加该严重等级下的BUG数量
                    severity_name = severity_name[:2]
                    self.bugLevelsCount[severity_name] += 1
                else:  # 如果严重等级名称为空，则累加空严重等级下的BUG数量
                    self.bugLevelsCount['空'] = self.bugLevelsCount.get('空', 0) + 1
                if bug_source:  # 如果缺陷根源不为空，则累加该缺陷根源下的BUG数量
                    self.bugSourceCount[bug_source] = self.bugSourceCount.get(bug_source, 0) + 1
                else:  # 如果缺陷根源为空，则累加空缺陷根源下的BUG数量
                    self.bugSourceCount['空'] = self.bugSourceCount.get('空', 0) + 1
                self._daily_trend_of_bug_changes_count(bug)
                # 累加多客户端下各严重等级下的BUG数量
                multi_client_data_processing(
                    result=self.bugLevelsMultiClientCount,
                    sub_key=severity_name,
                    all_sub_key=BUG_LEVELS,
                    key=bug_platform,
                )
                # 累加多客户端下各缺陷根源下的BUG数量
                multi_client_data_processing(
                    result=self.bugSourceMultiClientCount,
                    sub_key=bug_source,
                    all_sub_key=sources,
                    key=bug_platform,
                )
                if bug_id:  # 如果bug的id不为空，则将该bug的id添加到bugIds列表中
                    self.bugIds.append(bug_id)  # 将bug的id添加到bugIds列表中
                    created_date = date_time_to_date(bug.get('created'))
                    if bug_status == 'closed':  # 如果bug的状态是"已关闭"
                        resolved_date = date_time_to_date(bug.get('resolved'))  # 获取bug的解决日期
                        # 如果解决日期大于等于最晚任务日期，则为上线当天存在的BUG, 如果没有记录上线时间, 则为False
                        is_deploy_prod_day_unrepaired_bug = resolved_date >= self.onlineDate if self.onlineDate else False
                        is_on_that_day_unrepaired_bug = created_date != resolved_date  # 如果创建日期不等于解决日期，则为当天未修复的bug
                    else:  # 如果bug的状态不是"已关闭", 则将该BUG算为上线当天存在的BUG和当天未修复的bug
                        is_on_that_day_unrepaired_bug = True
                        is_deploy_prod_day_unrepaired_bug = True
                    # 如果bug的Bug等级为"顽固（180 天）"，则将该bug的id添加到unrepairedBugsData字典中，并累加其数量
                    if bug_field_level and bug_field_level == '顽固（180 天）':
                        self.unrepairedBugsData[bug_id] = self.unrepairedBugsData.get(bug_id, 0) + 1
                    # 如果上线当天未修复的BUG并且严重等级为("P1"或者"P2"), 则将该bug的id添加到unrepairedBugsData字典中，并累加其数量
                    if is_deploy_prod_day_unrepaired_bug and severity_name in BUG_LEVELS[0: 2]:
                        self.unrepairedBugs['deployProdDayUnrepaired']['P0P1'].append(bug_id)
                    # 如果上线当天未修复得BUG并且严重等级为"P2", 则将该bug的id添加到unrepairedBugsData字典中，并累加其数量
                    elif is_deploy_prod_day_unrepaired_bug and severity_name not in BUG_LEVELS[0: 2]:
                        self.unrepairedBugs['deployProdDayUnrepaired']['P2'].append(bug_id)
                    # 如果bug不是当天修复并且严重等级为"P0"，则将该bug的id添加到unrepairedBugsData字典中，并累加其数量
                    if is_on_that_day_unrepaired_bug and severity_name == BUG_LEVELS[0]:
                        self.unrepairedBugs['onThatDayUnrepaired']['P0'].append(bug_id)
                    # 如果bug不是当天修复并且严重等级为"P1"，则将该bug的id添加到unrepairedBugsData字典中，并累加其数量
                    elif is_on_that_day_unrepaired_bug and severity_name == BUG_LEVELS[1]:
                        self.unrepairedBugs['onThatDayUnrepaired']['P1'].append(bug_id)
                    # 如果bug不是当天修复并且严重等级不为"P0"或"P1"，则将该bug的id添加到unrepairedBugsData字典中，并累加其数量
                    elif is_on_that_day_unrepaired_bug and severity_name not in BUG_LEVELS[0: 2]:
                        self.unrepairedBugs['onThatDayUnrepaired']['P2'].append(bug_id)
                self.fixers[fixer] = self.fixers.get(fixer, 0) + 1  # 将fixer添加到fixers字典中，并累加其数量

        # 输出各严重等级的BUG数量
        for severityName, count in self.bugLevelsCount.items():
            print(f"{severityName}BUG数量：{count}")

        # 存储总的BUG数量
        self.bugTotal = len(self.bugIds)

    def score_result(self):
        """
        计算项目统计信息，包括BUG总数、开发周期、开发人员数量等，
        并根据这些信息计算项目平均一天工作量的Bug数及相应的软件质量评分。
        """
        # 打印分隔线，用于区分不同部分的输出
        try:
            self._bug_count_score()  # BUG数评分
            self._bug_repair_score()  # BUG修复评分
            self._bug_reopen_score()  # BUG重启评分
            self._positive_integrity_score()  # 配合积极性/文档完成性评分
            self._smoke_testing_score()  # 冒烟测试评分
            print('-' * LINE_LENGTH)
            print(f'总分为: {_print_text_font(sum(self.score.values()), is_weight=True)}')  # 输出总分
        except ValueError as e:
            # 捕获ValueError异常，并输出错误信息
            print(f"输入错误: {e}")

    def development_cycle(self):
        """
        计算每个开发者的工作小时数，以确定开发周期。

        遍历每个开发者的工作小时数，对于每个开发者在每个日期的工作小时数，
        如果工作小时数大于或等于8小时，则将该日期标记为1个完整工作日。
        如果工作小时数小于8小时，则计算该日期的工作小时数占一个完整工作日的比例，
        并与该日期已有的工作小时数比较，取较大值。

        最后，将所有日期的工作小时数相加，得到总的开发周期。
        """
        # 检查是否有每个开发者的每日工作小时数
        if self.dailyWorkingHoursOfEachDeveloper:
            # 初始化一个字典来存储每个日期的开发工作小时数
            development_days = {}

            # 遍历每个开发者的工作小时数
            for developerName, taskHours in self.dailyWorkingHoursOfEachDeveloper.items():
                # 检查该开发者的任务小时数是否已定义
                if taskHours:
                    # 遍历该开发者的每个日期的工作小时数
                    for date, hours in taskHours.items():
                        # 检查工作小时数是否已定义，并且该日期的工作小时数是否小于1
                        if hours and development_days.get(date, 0) < 1:
                            # 如果工作小时数大于或等于8小时，则将该日期标记为1个完整工作日
                            if hours >= 8:
                                development_days[date] = 1
                            else:
                                # 否则，计算该日期的工作小时数占一个完整工作日的比例
                                daily_hours = round((hours / 8), 1)
                                # 如果计算出的工作小时数大于该日期已有的工作小时数，则更新该日期的工作小时数
                                if development_days.get(date, 0) < daily_hours:
                                    development_days[date] = daily_hours

            # 检查是否有计算出的开发工作小时数
            if development_days:
                # 遍历每个日期的工作小时数，将其累加到总的开发周期中
                for devHours in development_days.values():
                    self.developmentCycle += devHours

    def add_test_report(self):
        """
        添加测试报告。

        该方法负责生成和提交测试报告。它首先移除当前用户，然后构造测试报告的HTML内容，
        并根据条件调用AI生成总结或添加缺陷列表和图表。最后，根据配置决定是否提交测试报告。
        """
        # 测试人员列表中移除当前用户
        self._remove_current_user()

        # 测试报告-概要的html内容
        self.testReportHtml += f'''
            <span style="color: rgb(34, 34, 34); font-size: medium; background-color: rgb(255, 255, 255);">{datetime.datetime.now().strftime("%Y年%m月%d日")}，{self.requirementName + '&nbsp; &nbsp;' if self.requirementName else ''}項目已完成測試，達到上綫要求</span>
            <div style="color: rgb(34, 34, 34);">
                <span style="background-color: rgb(255, 255, 255);">
                    <br  />
                </span>
            </div>
            <div style="color: rgb(34, 34, 34);">
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">項目测试结论</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">测试执行进度：</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">用例个数：</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">发现BUG数：{self.bugTotal if self.bugTotal else self.bugInputTotal}个</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">软件提测质量评分：{sum(self.score.values())}分（配合积极性/文档完整性{self.score["positiveIntegrityScore"]}分 + 冒烟测试{self.score["smokeTestingScore"]}分 + BUG数{self.score["bugCountScore"]}分 + BUG修复速度{self.score["bugRepairScore"]}分 + BUG重启率{self.score["bugReopenScore"]}分）</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">测试时间：</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">测试人员：{self.testersStr}</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">开发人员：{'、'.join(developer.replace(DEPARTMENT, '') for developer in self.developers)}</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">产品经理：{self.PM.replace(DEPARTMENT, '')}</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">测试范围：</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">测试平台：</span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">
                        <br  />
                    </span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">总结：
                        <br  /><br  /> %(reportSummary)s
                    </span>
                </div>
                <div>
                    <span style="font-size: medium; background-color: rgb(255, 255, 255);">
                        <br  />
                    </span>
                </div>
            </div>'''

        # 如果打开了AI生成总结内容开关, 则调用AI生成总结方法
        if IS_CREATE_AI_SUMMARY:
            self._ai_generate_summary()  # 调用AI生成总结方法

        # 构造测试报告数据
        url = HOST + f"/{PROJECT_ID}/report/workspace_reports/submit/0/0/security"
        params = {
            "report_type": "test",
            "save_draft": "1",
        }
        # 构建测试报告请求体
        data = {
            "data[Template][id]": "1163835346001000040",
            "data[WorkspaceReport][title]": f"{(self.requirementName + '_') if self.requirementName else DEPARTMENT}测试报告",
            "data[WorkspaceReport][receiver]": f"{';'.join([self.PM] + self.developers + self.testRecipient)}",
            "data[WorkspaceReport][receiver_organization_ids]": "",
            "data[WorkspaceReport][cc]": f"{';'.join(TEST_REPORT_CC_RECIPIENTS)}",
            "data[WorkspaceReport][cc_organization_ids]": "",
            "workspace_name": "T5;T5 Engineering;",
            "data[WorkspaceReport][workspace_list]": f"{PROJECT_ID}|51931447",
            "data[detail][1][type]": "richeditor",
            "data[detail][1][default_value]": self.testReportHtml % {"reportSummary": self.reportSummary},
            "data[detail][1][title]": "一、概述",
            "data[detail][1][id]": 0,
            "data[detail][2][type]": "story_list",
            "data[detail][2][workitem_type]": "story",
            "data[detail][2][show_fields]": "name,status,business_value,priority,size,iteration_id,owner,begin,due",
            "data[detail][2][title]": "二、需求",
            "data[detail][2][id]": 0,
            "data[detail][2][story_list_show_type]": "flat",
            f"data[detail][2][workitem_ids][{PROJECT_ID}]": REQUIREMENT_ID,
            f"data[detail][2][workitem_list_query_type][{PROJECT_ID}]": "list",
            f"data[detail][2][workitem_list_view_id][{PROJECT_ID}]": 0,
            f"data[detail][2][workitem_list_sys_view_id][{PROJECT_ID}]": 0,
            f"data[detail][2][workitem_list_display_count][{PROJECT_ID}]": 10,
            "data[detail][2][comment]": "",
            "data[return_url]": "/workspace_reports/index",
            "data[action_timestamp]": "",
            "data[filter_id]": 0,
            "data[model_name]": "",
            "data[submit]": "保存草稿",
        }
        # 如果存在BUG ID，则添加BUG列表
        if self.bugIds:
            data.update({
                "data[detail][3][type]": "bug_list",
                "data[detail][3][workitem_type]": "bug",
                "data[detail][3][show_fields]": "title,version_report,priority,severity,status,current_owner,created",
                "data[detail][3][title]": "三、缺陷列表",
                "data[detail][3][id]": 0,
                "data[detail][3][story_list_show_type]": "flat",
                f"data[detail][3][workitem_ids][{PROJECT_ID}]": ','.join(self.bugIds),
                f"data[detail][3][workitem_list_query_type][{PROJECT_ID}]": "list",
                f"data[detail][3][workitem_list_view_id][{PROJECT_ID}]": 0,
                f"data[detail][3][workitem_list_sys_view_id][{PROJECT_ID}]": 0,
                f"data[detail][3][workitem_list_display_count][{PROJECT_ID}]": 10,
                "data[detail][3][comment]": "",
            })
        # 如果存在图表数据，则添加图表
        if self.chartHtml:
            data.update({
                "data[detail][4][type]": "richeditor",
                "data[detail][4][title]": "图表",
                "data[detail][4][id]": 0,
                "data[detail][4][default_value]": f"<div>{self.chartHtml}</div>",
            })
        # 如果打开了创建测试报告开关, 则提交测试报告请求
        if IS_CREATE_REPORT:
            fetch_data(url=url, params=params, data=data, method='POST')  # 提交测试报告请求
        else:  # 如果关闭了创建测试报告开关, 则打印测试报告data
            print('\n请求测试报告data:')
            print(json.dumps(data, indent=4, ensure_ascii=False))

    def create_chart(self):
        """
        创建并汇总各种统计图表数据。

        本函数负责生成多个条形图，涵盖开发工时、BUG修复人、各端缺陷级别分布及缺陷根源分布统计。
        每个图表生成后，其路径信息被存储，并最终调用私有方法_charts_to_html将这些信息转换为HTML格式。
        """
        # 初始化图表列表，用于存储所有图表的路径信息
        charts = list()

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = [PLT_FONT[get_system_name()]]

        # 设置负号显示
        plt.rcParams['axes.unicode_minus'] = False

        # 创建开发工时统计条形图，并将图表路径信息添加到图表列表中
        work_hour_plot_data = create_bar_plot(title='开发工时统计', data=self.workHours)
        charts.append({
            'plotPath': work_hour_plot_data['plotPath'],
        })

        if self.bugIds:
            # 创建BUG修复人统计条形图，并将图表路径信息添加到图表列表中
            fixer_plot_data = create_bar_plot(title='BUG修复人', data=self.fixers)
            charts.append({
                'plotPath': fixer_plot_data['plotPath'],
            })

            # 创建各端缺陷级别分布统计条形图和表格数据，并将图表路径信息和表格数据添加到图表列表中
            bug_level_multi_client_count_plot_data = create_bar_plot(
                title='各端缺陷级别分布', data=self.bugLevelsMultiClientCount)
            charts.append({
                'plotPath': bug_level_multi_client_count_plot_data['plotPath'],
                'tableData': {
                    'firstColumnHeader': '软件平台',  # 表格第一列的标题
                    'tableWidth': bug_level_multi_client_count_plot_data['plotData']['widthPx'],  # 表格宽度
                    'data': self.bugLevelsMultiClientCount,  # 表格中展示的数据
                    'isMultiDimensionalTable': True,  # 表示数据是多维的，需要使用多维度表格显示
                    'isRowTotal': True,  # 表示数据中包含行总计，需要计算并显示
                }
            })

            # 创建缺陷根源分布统计条形图和表格数据，并将图表路径信息和表格数据添加到图表列表中
            bug_source_count_plot_data = create_bar_plot(title='缺陷根源分布统计', data=self.bugSourceMultiClientCount)
            charts.append({
                'plotPath': bug_source_count_plot_data['plotPath'],
                'tableData': {
                    'firstColumnHeader': '软件平台',  # 表格第一列的标题
                    'tableWidth': bug_source_count_plot_data['plotData']['widthPx'],  # 表格宽度
                    'data': self.bugSourceMultiClientCount,  # 表格中展示的数据
                    'isMultiDimensionalTable': True,  # 表示数据是多维的，需要使用多维度表格显示
                    'isRowTotal': True,  # 表示数据中包含行总计，需要计算并显示
                }
            })

            # 创建缺陷每日变化趋势折线图，并将图表路径信息添加到图表列表中
            daily_trend_of_bug_changes_count_broken_line_data = create_broken_line_plot(
                title='缺陷每日变化趋势', data=self.dailyTrendOfBugChanges)
            charts.append({
                'plotPath': daily_trend_of_bug_changes_count_broken_line_data['plotPath'],
                'tableData': {
                    'firstColumnHeader': '日期',  # 表格第一列的标题
                    'tableWidth': daily_trend_of_bug_changes_count_broken_line_data['plotData']['widthPx'],  # 表格宽度
                    'data': self.dailyTrendOfBugChanges,  # 表格中展示的数据
                    'isMultiDimensionalTable': True,  # 表示数据是多维的，需要使用多维度表格显示
                    'isRowTotal': False,  # 表示数据中包含行总计，需要计算并显示
                }
            })

        # 调用私有方法将图表路径信息转换并生成HTML
        self._charts_to_html(charts)
        # 如果不需要创建报告，则打印图表链接
        if not IS_CREATE_REPORT:
            print('\n\n\n图表链接：')
            for chart in charts:
                print('https://www.tapd.cn' + chart['plotPath'])

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

        # 检查创建日期是否在任务的最后日期之前或当天
        if create_date <= self.lastTaskDate:
            # 如果当前日期不在统计中，则初始化该日期的统计信息
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

        # 如果该开发者没有任务数据，则创建一个空的字典
        if developer_name not in self.dailyWorkingHoursOfEachDeveloper:
            self.dailyWorkingHoursOfEachDeveloper[developer_name] = {}

        # 如果开始和结束日期相同，则将该日期的工时加上实际完成工时
        if data['begin'] == data['due']:
            self.dailyWorkingHoursOfEachDeveloper[developer_name][data['begin']] = \
                self.dailyWorkingHoursOfEachDeveloper[developer_name].get(data['begin'], 0) + effort_completed
        # 如果开始和结束日期不同，则根据每个日期的剩余工时分配实际完成工时，直到完成的实际完成工时分配完毕
        elif data['begin'] < data['due']:
            # 获取开始和结束日期之间的所有日期
            for day in get_days(data['begin'], data['due']):
                # 获取该日期的工时
                saved_task_hours = self.dailyWorkingHoursOfEachDeveloper[developer_name].get(day, 0)
                # 计算该日期的剩余工时
                remaining_effort = 8 - saved_task_hours
                # 如果日期是日期类型，则转换为字符串类型
                # if type(day) == datetime.date:
                #     day = day.strftime('%Y-%m-%d')
                # 如果剩余工时大于0，则将该日期的工时加上剩余工时，并减去实际完成工时
                if effort_completed - remaining_effort > 0:
                    self.dailyWorkingHoursOfEachDeveloper[developer_name][day] = \
                        self.dailyWorkingHoursOfEachDeveloper[developer_name].get(day, 0) + remaining_effort
                    # 减去剩余工时
                    effort_completed -= remaining_effort
                else:
                    # 如果剩余工时小于等于0，则将该日期的工时加上实际完成工时，并结束循环
                    self.dailyWorkingHoursOfEachDeveloper[developer_name][day] = \
                        self.dailyWorkingHoursOfEachDeveloper[developer_name].get(day, 0) + effort_completed
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
            current_user_name = get_user_detail()['data']['get_current_user_ret']['data']['user_nick']
            # 如果当前用户在测试收件人列表中，则移除
            if current_user_name in self.testRecipient:
                self.testRecipient.remove(current_user_name)
            # 如果当前用户不是测试负责人，且测试负责人不在测试收件人列表中，则添加测试负责人
            if current_user_name != TESTER_LEADER and TESTER_LEADER not in self.testRecipient:
                self.testRecipient.append(TESTER_LEADER)

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

    def _positive_integrity_score(self):
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

    def _smoke_testing_score(self):
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

    def _bug_count_score(self):
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
            'scoreRule': self.bugCountScoreMsg + """20分：0<=平均一天工作的Bug数<=1且无严重，致命BUG
15分：1<平均一天工作量的Bug数<=1.5且无致命Bug
10分：1.5<平均一天工作量的Bug数<=2.0
5分：2.0<平均一天工作量的Bug数<=3.0
1分：3.0<平均一天工作量的Bug数
""",
            'score': self.score['bugCountScore']
        })

    def _bug_repair_score(self):
        """
        计算并打印BUG修复评分情况。

        该方法首先会检查在项目上线当天是否存在未修复的BUG（P0、P1和P2）。
        如果存在，则打印出未修复BUG的数量，并根据这些数据计算BUG修复评分。
        如果不存在未修复的BUG，则提供一个评分标准文本，供用户输入评分。
        """
        score_text = r"""20分：名下BUG当天修复，当天通过回归验证且无重开 
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
                f'''P0=致命缺陷, P1=严重缺陷, P2=一般缺陷、提示、建议;创建当天未修复BUG不一定是指项目上线当天未修复BUG
在项目上线当天存在P0或者P1未修复BUG数为：{_print_text_font(len(self.unrepairedBugs["deployProdDayUnrepaired"]["P0P1"]), color="green")}
在项目上线当天存在P2未修复BUG数为：{_print_text_font(len(self.unrepairedBugs["deployProdDayUnrepaired"]["P2"]), color="green")}
P0未创建当天修复BUG数为：{_print_text_font(len(self.unrepairedBugs["onThatDayUnrepaired"]["P0"]), color="green")}
P1未创建当天修复BUG数为：{_print_text_font(len(self.unrepairedBugs["onThatDayUnrepaired"]["P1"]), color="green")}
P2未创建当天修复BUG数为：{_print_text_font(len(self.unrepairedBugs["onThatDayUnrepaired"]["P2"]), color="green")}'''
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

    def _bug_reopen_score(self):
        """
        计算和输出BUG重启得分。

        该方法首先打印BUG重启部分的标题，然后根据BUG的重启和未修复数量计算得分。
        如果存在BUG总数，则获取重启BUG的详细信息，并计算重启和未修复的BUG数量，
        随后输出这些数量，并计算得分。如果BUG总数为0，则显示预设的得分标准，并要求输入得分。
        """
        score_text = """20分：当前版本名下所有BUG一次性回归验证通过无重启
15分：名下BUG重启输=1
10分：名下BUG重启输=2
5分：名下BUG重启输=3
1分：名下BUG重启输>=4
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
        text = f"需求名称: {self.requirementName},开发周期总天数为：{round(self.developmentCycle, 1)},BUG总数为: {self.bugTotal},开发人员数量为: {self.developerCount};"

        # 如果有BUG等级分布数据，则添加到摘要中
        if self.bugLevelsCount:
            text += f"BUG等级分布情况为:{self.bugLevelsCount};"

        # 如果有评分内容，则添加到摘要中
        if self.scoreContents:
            text += '项目研发评分情况:'
            for scoreData in self.scoreContents:
                text += f"{scoreData['title']}评分:{scoreData['scoreRule']},得分为: {scoreData['score']};"

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
                 '项目上线当天未修复BUG数的数量才是项目上线当天未修复的BUG数, 创建当天未修复的BUG数不是指项目上线当天未修复的BUG;'
                 '下面是格式要求：'
                 # '不要有尾部的签名和日期, 内容不要带表格，1级标题直接从分析的各个类型开始，又重复写质量总结或者报告分析之类的标题了\n'
                 # '1级主题文字前后各加"***"并且加上序号(一、二、三、)，并且把2级主题字体加粗(需要加粗的字体前后各加**), 1级标题于下一个1级标题之间需要加分隔横线(用"---"来表示, 不要给我多三个以上的"-"), 不要在1级标题和1级标题的内容之间分隔横线\n'
                 # '1级主题下面的内容每一行开头统一使用"▶ "作为开头（不要给1级主题加）, 然后2级主题下面的内容每一行最前面用"    "四个空格来制造缩进效果并且统一使用"▷ "开头, 如果还有下层内容使用"        "八个空格并且使用"-"开头\n'
                 '将内容中的关键点使用<red>内容</red>标识,'
                 # '我需要将总结写进%(reportSummary)s中, 请给我合理的格式, 我只需要用来代替reportSummary的内容, 不要把%(reportSummary)s也写在内容中\n'
                 # '行尾最后内容中不要出现备注, 比如: "注: *********"\n'
                 # '内容正常返回就行, 不需要有html的标签, 我自己会处理\n'
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
            - 调用 `self.print_summary()` 方法，计算并打印特定需求的所有开发人员的工时合计及每个开发人员的工时。
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
        try:
            # 编辑列表展示字段
            self.edit_list_config()

            # 获取需求名称
            self.get_requirement_detail()

            # 检查需求名称是否获取成功
            if not self.requirementName:
                raise ValueError("需求名称获取失败, 请检查需求ID是否正确")

            # 汇总开发人员工时
            self.ger_requirement_task()

            # 检查测试任务是否存在
            if not self.isExistTestTask:
                raise ValueError(f'没有测试任务, 请检查"{self.requirementName}"需求是否有测试任务')

            # 检查工时数据是否获取成功
            if not self.workHours:
                raise ValueError("工时数据获取失败, 请检查需求是否有子任务")

            if self.dailyWorkingHoursOfEachDeveloper:
                # 计算开发周期
                self.development_cycle()

            # 打印工时汇总
            self.print_summary()

            # 统计BUG数量
            self.bug_list_detail()

            # 计算并输出相关统计数据
            self.score_result()

            # 创建图表
            self.create_chart()

            # 添加测试报告
            self.add_test_report()

        except ValueError as e:
            # 捕获ValueError异常并打印堆栈信息
            traceback.print_exc()
            raise e

        finally:
            # 还原列字段展示的配置信息
            try:
                assert edit_query_filtering_list_config(self.oldBugListConfigs)
                assert edit_requirement_list_config(self.oldSubTaskListConfigs)
            except Exception as e:
                # 捕获异常并打印堆栈信息
                traceback.print_exc()
                raise e


if __name__ == "__main__":
    SoftwareQualityRating().run()
