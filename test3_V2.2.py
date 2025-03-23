# 2025年03月23日23:25:59

# ==================================================================
# 导入标准库
# ==================================================================
import base64
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import datetime
import functools
from io import BytesIO
import json
import math
import os
import platform
import re
import sys
import time
import traceback
from typing import (Any, Dict, List, Optional, Tuple, TypeVar, Union)

# ==================================================================
# 导入第三方库
# ==================================================================
import chinese_calendar as calendar
import cloudscraper
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import matplotlib.pyplot as plt
import numpy as np
from openai import (APIError, APIConnectionError, APIStatusError, OpenAI)
import requests

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
# REQUIREMENT_ID = "1163835346001071668"  # 需求ID
# REQUIREMENT_ID = "1163835346001033609"  # 需求ID 中规中矩  警告：没有测试任务, 请检查"【中古屋住宅】競價服務新增按天結算測試（限台中）"需求是否有测试任务
# REQUIREMENT_ID = "1163835346001051222"  # 需求ID 较差的质量
# REQUIREMENT_ID = "1163835346001049795"  # 需求ID 较差的质量  开发周期也是很多小数点尾数
# REQUIREMENT_ID = "1163835346001055792"  # 需求ID 较差的质量
REQUIREMENT_ID = "1163835346001118124"  # 需求ID
# REQUIREMENT_ID = "1163835346001124542"  # 需
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

# 客户端列表，用于在提问阶段展示用户选择
CLIENTS = [
    'IOS',
    'Android',
    'PC',
    'H5',
    'API',
    'Flutter',
]

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
    "id",  # 子任务ID
    "name",  # 子任务名称
    "status",  # 状态
    "owner",  # 处理人
    "begin",  # 预计开始
    "due",  # 预计结束
    "effort_completed",  # 完成工时
]

# 评分输入数据的格式
SCORE_INPUT_DATA = {
    'input_type': int,  # 输入类型
    'allow_contents': [20, 15, 10, 5, 1]  # 评分输入数据的可选值
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
            required_keys: set = {'desiredWidthData', 'labels', 'title', 'maxBarHeight', 'ax'}
            if not required_keys.issubset(func_data.keys()):
                missing = required_keys - func_data.keys()
                raise ValueError(f"缺失必要的图表配置参数: {missing}")

            # ==================================================================
            # 数据解包与预处理
            # ==================================================================

            # 解包图表配置参数
            plot_data: dict[str, int or float] = func_data['desiredWidthData']  # 图表尺寸等元数据
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
            y_intervals: tuple[int] = calculation_plot_y_max_height(max_bar_height)

            # 设置Y轴刻度位置及标签
            plt.yticks(
                y_intervals,  # 生成等间隔刻度位置
                labels=[str(x) for x in y_intervals]  # 生成纯数字标签
            )

            # 设置y轴的最大值
            max_height: int = max(y_intervals)

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
    score_mapping: dict[tuple[int or float, int or float], int] = {
        (-1, 1): 20,  # 特殊处理负值情况，实际业务中X应为正数
        (1, 1.5): 15,  # 1 < X <= 1.5
        (1.5, 2): 10,  # 1.5 < X <= 2
        (2, 3): 5,  # 2 < X <= 3
        (3, float('inf')): 1  # X > 3
    }

    # 遍历所有评分区间
    for (lower, upper), score in score_mapping.items():
        lower: int or float
        upper: int or float
        score: int
        # 检查X是否在当前区间内（左开右闭）
        if lower < X <= upper:
            return score

    # 若未匹配任何区间（理论上不会执行到这里，因最后一个区间覆盖+∞）
    # 防御性编程：打印警告信息并返回None
    raise "错误：BUG密度值不在预期范围内，请检查输入数据有效性"


def calculate_bug_reopen_rating(X: int) -> int:
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
        X: int = int(X)
    except (ValueError, TypeError):
        raise TypeError("错误：输入值必须为可转换为整数的类型")

    # 处理负值输入（根据业务逻辑视为最差情况）
    try:
        assert X >= 0
    except AssertionError:
        raise ValueError("错误：缺陷重新打开次数不应为负数")

    # 定义评分映射字典（key为最大次数阈值，value为对应得分）
    score_mapping: dict[int, int] = {
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


def calculate_bug_repair_rating(unrepaired_bug: Dict[str, Any]) -> int or None:
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
    prod_day_unrepaired: dict[str, list[str]] = unrepaired_bug.get('deployProdDayUnrepaired', {})
    on_that_day_unrepaired: dict[str, list[str]] = unrepaired_bug.get('onThatDayUnrepaired', {})

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


def _input(
        text: str,
        input_type: type = None,
        allow_contents: List[Any] = None,
        re_format: str = None,
        re_prompts_format: str = None,
        is_delete_space: bool = False,
        is_strip: bool = True
) -> Any:
    """
    实现交互式输入验证框架，支持多维度输入校验

    本方法提供完整的输入验证解决方案，包含以下核心功能：
    1. 类型安全转换：自动处理输入类型转换及异常
    2. 值域校验：验证输入值是否在允许范围内
    3. 格式匹配：支持正则表达式格式验证
    4. 输入预处理：空格处理及字符串标准化

    参数:
        text (str):
            输入提示文本，显示在控制台的引导信息
            示例："请输入选项："

        input_type (type):
            目标数据类型，支持Python基础类型如int/float/str等
            None表示保留原始字符串类型

        allow_contents (List[Any]):
            允许的输入值白名单，None表示不限制输入范围
            示例：[1, 2, 3] 或 ["yes", "no"]

        re_format (str):
            正则表达式模式，用于验证输入格式
            示例：r"^[A-Za-z]+$" 验证纯字母输入

        re_prompts_format (str):
            格式验证失败时的友好提示文本
            示例："请输入字母组合"

        is_delete_space (bool):
            是否删除输入中的所有空格字符
            True时会将"a b"转换为"ab"

        is_strip (bool):
            是否移除输入首尾的空白字符
            True时会自动执行strip()处理

    返回:
        Any: 经过验证和类型转换后的输入值，类型由input_type参数决定

    异常:
        ValueError: 当输入内容无法转换为目标类型时抛出
        TypeError: 当输入值类型不符合白名单要求时抛出

    实现逻辑:
        1. 构建交互式输入循环，直到获得合法输入
        2. 执行输入预处理（空格处理）
        3. 进行类型转换验证
        4. 执行白名单范围校验
        5. 执行正则表达式格式验证
        6. 返回通过所有校验的合法值
    """
    # 构建可持续交互的输入验证循环
    while True:
        try:
            # ==================================================================
            # 阶段1：原始输入获取
            # ==================================================================

            # 显示引导信息并获取原始输入
            raw_input: str = input(text)

            # ==================================================================
            # 阶段2：输入预处理
            # ==================================================================

            # 执行首尾空白字符清理（当启用strip时）
            if is_strip:
                raw_input = raw_input.strip()

            # 执行全空格字符删除（当启用空格过滤时）
            if is_delete_space:
                raw_input = raw_input.replace(' ', '')

            # ==================================================================
            # 阶段3：类型转换处理
            # ==================================================================

            # 当指定目标类型时进行类型转换
            if input_type:
                # 尝试将输入转换为目标数据类型
                converted_value = input_type(raw_input)
            else:
                # 保持原始字符串类型不做转换
                converted_value = raw_input

            # ==================================================================
            # 阶段4：白名单验证
            # ==================================================================

            # 当存在允许值列表时执行范围校验
            if allow_contents:
                # 统一转换为小写进行大小写不敏感匹配（仅限字符串类型）
                for index, allowContent in enumerate(allow_contents):
                    if isinstance(allowContent, str):
                        allow_contents[index] = allowContent.lower()

                # 准备待校验值（字符串类型转小写）
                check_value = converted_value.lower() if isinstance(converted_value, str) else converted_value

                # 执行范围校验
                if check_value not in allow_contents:
                    # 生成可读性强的错误提示信息
                    allowed_values = ', '.join(map(str, allow_contents))
                    error_msg = f"输入值必须在 [{allowed_values}] 范围内"

                    # 输出红色字体错误提示并重新循环
                    print(_print_text_font(f"\n错误：{error_msg}\n", color='red'))
                    continue

            # ==================================================================
            # 阶段5：正则表达式校验
            # ==================================================================

            # 当存在正则表达式模式时执行格式验证
            if re_format and not re.fullmatch(re_format, converted_value):
                # 优先使用自定义提示信息，否则显示原始正则表达式
                format_prompt = re_prompts_format if re_prompts_format else re_format

                # 输出格式错误提示并重新循环
                print(_print_text_font(
                    f"\n格式错误：输入内容格式不匹配, 期望格式: {format_prompt}\n",
                    color='red'
                ))
                continue

            # ==================================================================
            # 阶段6：返回合法值
            # ==================================================================

            # 返回通过所有校验的合法值
            return converted_value

        except ValueError as ve:
            # ==================================================================
            # 异常处理：类型转换失败
            # ==================================================================

            # 获取目标类型名称用于错误提示
            type_name = input_type.__name__ if input_type else '字符串'
            error_detail = f"输入的内容数据类型不匹配, 期望为 {type_name} 类型"

            # 输出红色字体类型错误提示
            print(_print_text_font(f"\n格式错误：{error_detail}\n", color='red'))

        except Exception as e:
            # ==================================================================
            # 异常处理：未预料错误
            # ==================================================================

            # 全局异常兜底处理
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


def get_session_id() -> None:
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


def get_requirement_list_config() -> List[str]:
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


def get_query_filtering_list_config() -> List[str]:
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


def get_user_detail() -> Dict[str, Any]:
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
    生成标准化堆叠柱状图，支持多数据系列展示和智能标签布局

    本方法实现完整的堆叠柱状图生成流程，包含数据转换、视觉呈现、交互标签布局等功能。
    支持多层级数据展示，自动处理颜色分配、标签防重叠、数值标注等可视化细节。

    参数详解:
        title (str):
            图表主标题文本，用于描述图表的核心主题
            示例: "各模块缺陷分布统计"
            长度建议控制在40字符以内以确保可读性

        data (dict):
            多层嵌套的输入数据字典，结构要求：
            {
                "分类A": {"子类1": 10, "子类2": 20},  # 分类维度1的数据
                "分类B": {"子类1": 30, "子类3": 40},  # 分类维度2的数据
                "分类C": 50  # 直接数值将归入默认子类
            }
            字典键为字符串类型，值可为数值或嵌套字典

    返回:
        dict: 包含图表元数据的字典，结构为：
        {
            'desiredWidthData': dict,  # 图表尺寸配置数据
            'labels': list,           # 数据子类标签列表
            'title': str,             # 传递的标题文本
            'maxBarHeight': int,      # 最大柱状高度值
            'ax': plt.Axes            # Matplotlib坐标轴对象
        }

    异常:
        ValueError: 当输入数据为空或格式不兼容时抛出
        RuntimeError: 图表生成过程中发生不可恢复错误时抛出

    实现流程:
        1. 数据转换与格式化
        2. 数据完整性校验
        3. 图表基础框架构建
        4. 堆叠柱状图绘制
        5. 交互式标签布局
        6. 元数据封装返回
    """
    try:
        # ==================================================================
        # 阶段1：数据转换与格式化
        # ==================================================================
        # 将嵌套字典结构转换为NumPy数组和标签列表
        # labels: 子类名称列表，如['子类1','子类2','子类3']
        # np_data: 二维数组，行代表子类，列代表主分类
        labels, np_data = switch_numpy_data(data)

        # 提取主分类键列表，如['分类A','分类B','分类C']
        keys = list(data.keys())

        # 计算各主分类的总高度，用于顶部标签布局
        total_heights = np.sum(np_data, axis=0)

        # ==================================================================
        # 阶段2：数据完整性校验
        # ==================================================================
        # 防御空数据校验（主分类维度）
        if not keys:
            raise ValueError("输入数据字典不能为空")

        # 防御空数据校验（子类维度）
        if np_data.size == 0:
            raise ValueError("数据转换异常，请确认输入结构符合规范")

        # ==================================================================
        # 阶段3：图表基础框架构建
        # ==================================================================
        # 创建Matplotlib图形和坐标轴对象
        # fig: 整个图形容器对象
        # ax: 主要绘图区域对象
        fig, ax = plt.subplots()

        # 计算动态柱宽和图表尺寸参数
        # desired_bar_width: 单个柱子的宽度（基于分类数量自适应）
        # plot_data: 包含图表尺寸元数据的字典
        desired_bar_width, plot_data = calculate_plot_width(keys, fig)

        # ==================================================================
        # 阶段4：堆叠柱状图绘制
        # ==================================================================
        # 初始化堆叠基准线
        bottoms = np.zeros(len(keys))

        # 按子类层级逐层绘制
        for idx in range(np_data.shape[0]):
            # 绘制当前子类的柱状图序列
            bars = ax.bar(
                keys,  # X轴刻度标签
                np_data[idx],  # 当前子类数据值
                width=desired_bar_width,  # 动态计算的柱宽
                bottom=bottoms,  # 当前堆叠基准高度
                color=PLOT_COLORS[idx % len(PLOT_COLORS)],  # 循环使用预定义颜色
                label=labels[idx] if labels else None  # 图例标签文本
            )

            # 更新堆叠基准高度为当前层顶部
            bottoms += np_data[idx]

            # ==================================================================
            # 阶段5：交互式标签布局
            # ==================================================================
            # 仅当存在多层数据时添加内部标签
            if np_data.shape[0] > 1:
                # 遍历每个柱子添加数值标签
                for bar_index, (bar, value) in enumerate(zip(bars, np_data[idx])):
                    # 跳过零值和顶层值（顶层由总高度标签处理）
                    if value and value != total_heights[bar_index]:
                        # 计算标签位置（柱体中心偏下）
                        ax.text(
                            bar.get_x() + bar.get_width() / 2,  # X轴居中位置
                            bar.get_y() + value / 2,  # Y轴居中偏下
                            str(int(value)),  # 整型数值标签
                            ha='center',  # 水平居中
                            va='center',  # 垂直居中
                            color='white',  # 高对比度文本颜色
                            fontsize=9  # 适配柱体高度的字号
                        )

        # 添加总高度标签（每个主分类柱顶）
        for i, total in enumerate(total_heights):
            if total:  # 过滤零值情况
                ax.text(
                    i,  # X轴位置索引
                    total,  # Y轴顶部位置
                    str(round(total, 2)),  # 保留两位小数
                    ha='center',  # 水平居中
                    va='bottom'  # 垂直底部对齐
                )

        # ==================================================================
        # 阶段6：元数据封装返回
        # ==================================================================
        return {
            'desiredWidthData': plot_data,  # 图表尺寸配置
            'labels': labels,  # 子类标签列表
            'title': title,  # 传递的标题文本
            'maxBarHeight': math.ceil(max(total_heights)),  # 计算最大高度
            'ax': ax  # 坐标轴对象用于后续配置
        }

    except Exception as e:
        # 异常时强制释放图形资源
        plt.close('all')
        raise RuntimeError(f"图表生成流程异常终止: {str(e)}") from e


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
    """
    处理流式API响应数据，实时解析并输出AI生成内容

    该函数负责处理来自AI模型的流式响应数据，实现以下核心功能：
    1. 实时分离并展示推理过程与最终答案
    2. 动态更新生成内容缓冲区
    3. 处理用户中断操作
    4. 生成最终格式化输出

    参数:
        completion (generator): 流式响应生成器对象，包含分块传输的AI响应数据
        result (list): 内容缓冲区列表，用于累积最终答案内容

    返回:
        str: 经过HTML格式转换的完整生成内容

    异常处理:
        KeyboardInterrupt: 捕获用户中断信号，返回已生成内容

    实现流程:
        1. 初始化输出状态标识
        2. 遍历流式数据生成器
        3. 解析并分类响应内容
        4. 实时输出过程信息
        5. 处理异常中断
        6. 返回标准化结果
    """

    # ==================================================================
    # 阶段1：初始化输出控制参数
    # ==================================================================

    # 打印带时间戳的生成开始标记（精确到秒）
    print(f'\n{datetime.datetime.now().strftime("%H:%M:%S")} 生成开始')

    # 初始化状态追踪标识
    is_reasoning = False  # 推理过程输出状态标识
    is_final_answer = False  # 最终答案输出状态标识

    try:
        # ==================================================================
        # 阶段2：流式数据遍历处理
        # ==================================================================

        # 遍历流式响应中的每个数据块（chunk）
        for chunk in completion:

            # 从数据块中提取增量内容（delta）
            delta = chunk.choices[0].delta

            # 获取推理过程内容（可能为空字符串）
            reasoning_content = getattr(delta, 'reasoning_content', '')

            # 获取正式答案内容（可能为空字符串）
            content = getattr(delta, 'content', '')

            # ==================================================================
            # 阶段3：推理过程内容处理
            # ==================================================================

            # 检测到有效推理内容且尚未启动推理输出
            if reasoning_content:
                if not is_reasoning:
                    # 打印推理过程标题并换行
                    print('\n思考轨迹:', flush=True)
                    # 更新推理状态标识
                    is_reasoning = True
                # 持续输出推理内容（黑色字体）
                # 使用_print_text_font处理字体样式，实时刷新输出缓冲区
                print(_print_text_font(reasoning_content, color='black'), end='', flush=True)

            # ==================================================================
            # 阶段4：最终答案内容处理
            # ==================================================================

            # 检测到有效答案内容且尚未启动答案输出
            if content:
                if not is_final_answer:
                    # 打印答案标题（添加双换行分隔）
                    print('\n\n最终答案:', flush=True)
                    # 更新答案状态标识
                    is_final_answer = True
                # 持续输出答案内容
                # 直接输出原始内容，实时刷新输出缓冲区
                print(content, end='', flush=True)
                # 累积内容到结果缓冲区
                result.append(content)

                # ==================================================================
        # 阶段5：生成完成处理
        # ==================================================================

        # 打印带时间戳的完成标记
        print(f'\n\n{datetime.datetime.now().strftime("%H:%M:%S")} 生成完成')

        # 将缓冲区内容转换为HTML格式
        return ai_result_switch_html(''.join(result))

    except KeyboardInterrupt:
        # ==================================================================
        # 阶段6：中断异常处理
        # ==================================================================

        # 捕获用户中断信号（Ctrl+C）
        print('\n\n生成过程已中断')

        # 返回已累积的内容（转换为HTML格式）
        return ai_result_switch_html(''.join(result))


def _handle_normal_response(completion: Any, result: List[str]) -> str:
    """
    处理OpenAI API的非流式响应数据，提取关键信息并格式化输出

    该方法负责解析标准API响应结构，执行以下核心操作：
    1. 提取AI模型的中间思考过程（如支持）
    2. 获取最终生成的文本内容
    3. 执行结构化数据验证和异常处理
    4. 将原始文本转换为标准化HTML格式

    参数:
        completion (Any): OpenAI API响应对象，包含完整的响应数据结构
        result (List[str]): 累积生成结果的缓冲区列表，用于存储最终答案内容

    返回:
        str: 经过HTML格式转换的最终生成文本，可直接用于前端展示

    异常:
        ValueError: 当响应内容为空或无法解析时抛出

    实现逻辑:
        1. 响应数据解构与校验
        2. 中间过程信息提取（若存在）
        3. 最终答案内容提取与存储
        4. 响应内容格式化与异常处理
    """
    try:
        # ==================================================================
        # 阶段1：响应数据解构与校验
        # ==================================================================
        # 验证响应对象是否包含必要属性（防御性编程）
        if not hasattr(completion, 'choices') or len(completion.choices) == 0:
            raise AttributeError("响应对象缺少choices属性或内容为空")

        # 获取首个候选响应消息（假设单候选响应模式）
        message = completion.choices[0].message

        # ==================================================================
        # 阶段2：中间思考过程提取
        # ==================================================================
        # 使用安全属性获取方法提取推理内容（兼容字段不存在的情况）
        reasoning_content = getattr(message, 'reasoning_content', None)

        # 当存在中间推理过程时，进行格式化输出
        if reasoning_content:
            # 调用字体格式化工具，生成带颜色标记的文本
            formatted_reasoning = _print_text_font(
                text=reasoning_content,
                color='black'  # 使用黑色字体强调思考过程
            )
            # 输出带时间戳的思考轨迹日志
            print(f"\n思考轨迹:\n{formatted_reasoning}")

        # ==================================================================
        # 阶段3：最终答案内容处理
        # ==================================================================
        # 提取消息内容主体，处理可能的内容缺失情况
        final_answer = message.content if hasattr(message, 'content') else ''

        # 当存在有效内容时执行处理流程
        if final_answer:
            # 打印带时间戳的生成结果日志
            print("\n最终答案:\n{}".format(final_answer))
            # 将原始内容存入结果缓冲区
            result.append(final_answer)

        # ==================================================================
        # 阶段4：响应内容格式化
        # ==================================================================
        # 生成带时间戳的完成日志
        print(f'\n{datetime.datetime.now().strftime("%H:%M:%S")} 生成完成')

        # 将原始文本转换为HTML格式并返回
        return ai_result_switch_html(''.join(result))

    except Exception as unexpect_error:
        # ==================================================================
        # 异常处理：未知错误捕获
        # ==================================================================
        # 记录完整的错误堆栈信息
        error_trace = traceback.format_exc()
        # 生成带调试信息的错误报告
        raise RuntimeError(
            f"非流式响应处理异常: {str(unexpect_error)}\n追踪信息:{error_trace}"
        ) from unexpect_error


class SoftwareQualityRating:
    def __init__(self):
        """
        软件质量评分系统初始化方法

        本方法初始化软件质量评分系统所需的所有数据结构，包括：
        - 项目基础信息与人员配置
        - 时间周期相关数据
        - 缺陷全生命周期统计数据
        - 评分规则及结果存储
        - 报告生成相关配置
        - 系统运行状态跟踪

        数据结构说明:
            1. 基础信息模块:
                - requirementName: 需求名称（字符串）
                - PM: 产品经理姓名（字符串）
                - testRecipient: 测试报告接收人列表（邮件地址数组）
                - testersStr: 测试团队人员字符串表示（逗号分隔）
                - developers: 开发团队人员列表
                - subDemandTasks: 子需求任务列表（字典数组）
                - bugs: 缺陷数据集合（字典数组）
                - bugPlatforms: 缺陷平台列表（如iOS/Android）
                - bugSources: 缺陷根源分类列表（如代码/需求）
                - bugExistPlatforms: 缺陷实际存在平台列表

            2. 时间周期模块:
                - isInputOnlineDate: 上线日期输入方式标识（True=手动输入）
                - earliestTaskDate: 最早子任务开始日期（YYYY-MM-DD）
                - lastTaskDate: 最晚子任务结束日期（YYYY-MM-DD）
                - onlineDateDict: 多端分别上线日期字典（客户端类型为键）
                - onlineDate: 系统自动识别的上线日期

            3. 缺陷统计模块:
                - workHours: 开发人员工时统计（默认字典）
                - devTotalHours: 开发总工时（浮点数）
                - developerCount: 参与开发人数（整数）
                - dailyWorkingHoursOfEachDeveloper: 开发者每日工时明细（嵌套字典）
                - developmentCycle: 完整开发周期（自然日）

                - bugLevelsCount: 缺陷等级分布统计（默认字典）
                - bugLevelsMultiClientCount: 多客户端缺陷等级交叉统计
                - bugSourceCount: 缺陷根源分类统计
                - bugSourceMultiClientCount: 多客户端缺陷根源交叉统计
                - bugTotal: 缺陷总量统计
                - bugInputTotal: 手动录入缺陷数
                - bugIds: 缺陷ID集合
                - reopenBugsData: 缺陷重开情况统计（默认字典）
                - unrepairedBugsData: 未修复缺陷统计（默认字典）
                - fixers: 缺陷修复人员分布统计（默认字典）

            4. 评分系统模块:
                - score: 评分结果字典（包含五大维度评分）
                - scoreContents: 评分细则说明列表
                - bugCountScoreMsg: 缺陷数量维度评分说明
                - bugRepairScoreMsg: 缺陷修复质量评分说明
                - bugReopenScoreMsg: 缺陷重开率评分说明

            5. 报告生成模块:
                - testReportHtml: 测试报告HTML模板内容
                - chartHtml: 可视化图表HTML片段
                - reportSummary: 报告总结摘要内容

            6. 配置管理模块:
                - isInitialListConfig: 列表配置状态标识
                - oldBugListConfigStr: 原始缺陷列表配置快照
                - oldSubTaskListConfigStr: 原始子任务列表配置快照

            7. 缺陷跟踪模块:
                - unrepairedBugs: 未修复缺陷分级存储结构
                    - deployProdDayUnrepaired: 上线当天未修复缺陷（按严重等级分类）
                    - onThatDayUnrepaired: 创建当天未修复缺陷（按严重等级分类）

            8. 趋势分析模块:
                - dailyTrendOfBugChanges: 缺陷每日变化趋势数据
                    （记录每日新增/修复/关闭等状态变化）
        """
        # ==================================================================
        # 1.基础信息初始化
        # ==================================================================
        self.requirementName: str = ''  # 需求名称
        self.PM: str = ''  # 产品经理
        self.testRecipient: List[str] = []  # 测试报告接收人列表(测试人员)
        self.testersStr: str = ''  # 测试人员字符串表示
        self.developers: List[str] = []  # 开发人员列表
        self.subDemandTasks: List[Dict[str, Any]] = []  # 子需求任务列表
        self.bugs: List[Dict[str, Any]] = []  # 缺陷数据集合
        self.bugPlatforms: List[str] = []  # 缺陷平台列表
        self.bugSources: List[str] = []  # 缺陷根源分类列表
        self.bugExistPlatforms: List[str] = []  # 缺陷实际存在平台列表

        # ==================================================================
        # 2.时间相关初始化
        # ==================================================================
        self.isInputOnlineDate: bool = False  # 是否手动输入上线日期
        self.earliestTaskDate: str = ''  # 最早任务日期
        self.lastTaskDate: str = ''  # 最晚任务日期
        self.onlineDateDict: Dict[str, Any] = {}  # 上线日期  # 针对涉及多客户端分别上线，手动输入记录上线日期
        self.onlineDate: Any = None  # 上线日期  针对于程序自己去找最后一个测试任务的预计开始日期作为上线日期

        # ==================================================================
        # 3.缺陷统计初始化
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
        self.reopenBugsData = defaultdict(int)  # 重新打开缺陷数据
        self.unrepairedBugsData = defaultdict(int)  # 未修复缺陷数据
        self.fixers = defaultdict(int)  # 缺陷修复人统计

        # ==================================================================
        # 4.评分系统初始化
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
        # 5.报告生成初始化
        # ==================================================================
        self.testReportHtml = ''  # 测试报告HTML内容
        self.chartHtml = ''  # 图表HTML内容
        self.reportSummary = ''  # 报告总结内容

        # ==================================================================
        # 6.配置信息初始化
        # ==================================================================
        self.isInitialListConfig = True  # 是否初始化列表配置标志， True=列表配置为初始化， False=列表配置已被更新
        self.oldBugListConfigStr = ''  # 原始缺陷列表配置
        self.oldSubTaskListConfigStr = ''  # 原始子任务列表配置

        # ==================================================================
        # 7.未修复缺陷数据结构初始化
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
        # 8.缺陷每日变化趋势初始化
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
                self._print_error("警告：需求名称获取失败，请检查需求ID是否正确")

            if not self.PM:
                self._print_error("警告：产品经理获取失败，请检查需求创建人是否正确")

            # ==================================================================
            # 阶段7：展示可视化标题
            # ==================================================================
            print('\n' + f' 需求 {REQUIREMENT_ID}: {self.requirementName} '.center(LINE_LENGTH, '*'))

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

    def get_requirement_tasks(self) -> None:
        """
        递归获取指定需求的所有子任务信息并存储至实例变量，支持分页查询

        通过TAPD官方API接口，获取指定需求下的全量子任务数据并存储到self.subDemandTasks，
        数据包含但不限于：
        - 任务基础属性（ID、标题、状态）
        - 时间信息（预计开始、截止时间）
        - 工作量信息（完成工时）
        - 责任人信息

        数据存储:
            self.subDemandTasks: 结构化子任务数据列表，每个元素为包含子任务详细信息的字典
            示例结构:
            [
                {
                    "id": "1001",
                    "name": "接口开发任务",
                    "status": "in_progress",
                    "owner": "T5_张三",
                    "begin": "2025-03-01",
                    "due": "2025-03-05",
                    "effort_completed": 8.5,
                    ...
                },
                ...
            ]

        异常:
            requests.JSONDecodeError: 响应数据不符合JSON格式时抛出
            ValueError: 数据解析失败或关键字段缺失时抛出
            KeyError: 响应数据结构不符合预期时抛出

        实现流程:
            1. 初始化分页参数和存储结构
            2. 构建符合TAPD API规范的请求参数
            3. 分页获取数据并进行完整性校验
            4. 合并多页数据存储至实例变量
        """

        # ==================================================================
        # 阶段1：初始化分页参数
        # ==================================================================
        current_page: int = 1  # 当前请求页码，从第一页开始
        records_per_page: int = 100  # 每页请求数据量，TAPD API最大支持100条/页

        # ==================================================================
        # 阶段2：构建API请求基础参数
        # ==================================================================
        # 拼接完整的API端点URL（HOST为全局配置的TAPD域名）
        api_endpoint: str = f"{HOST}/api/entity/stories/get_children_stories"

        # 构造符合TAPD API规范的查询参数
        # - workspace_id: 项目空间唯一标识（从全局配置获取）
        # - story_id: 目标需求唯一标识（从全局配置获取）
        # - 分页参数(page/per_page)和排序参数(sort_name/order)
        base_params: Dict[str, Union[str, int]] = {
            "workspace_id": PROJECT_ID,
            "story_id": REQUIREMENT_ID,
            "page": current_page,
            "per_page": records_per_page,
            "sort_name": "due",  # 按截止时间字段排序
            "order": "asc"  # 升序排列(从最早到期到最晚到期)
        }

        # ==================================================================
        # 阶段3：分页请求循环
        # ==================================================================
        while True:
            # 发送API请求（使用封装的fetch_data方法处理重试和认证）
            # fetch_data已内置异常处理和会话管理功能
            api_response: requests.Response = fetch_data(
                url=api_endpoint,
                params=base_params,
                method="GET"
            )

            try:
                # ==================================================================
                # 阶段4：响应数据解析与校验
                # ==================================================================
                # 将响应内容解析为JSON格式（可能抛出JSONDecodeError）
                response_data: Dict = api_response.json()

                # 校验顶层数据结构（TAPD标准响应结构）
                if "data" not in response_data:
                    raise KeyError("API响应缺少核心数据域'data'字段")

                # 校验子任务列表字段存在性
                task_list_key: str = "children_list"
                if task_list_key not in response_data["data"]:
                    raise KeyError(f"响应数据缺失关键字段'{task_list_key}'")

                # 提取当前页任务数据并进行类型校验
                current_page_tasks: List[Dict] = response_data["data"][task_list_key]
                if not isinstance(current_page_tasks, list):
                    raise TypeError(
                        f"子任务数据格式异常，预期列表类型，实际类型：{type(current_page_tasks)}"
                    )

                # ==================================================================
                # 阶段5：数据累积与分页控制
                # ==================================================================
                # 合并当前页数据到总集合
                self.subDemandTasks.extend(current_page_tasks)

                # 判断分页终止条件：
                # 1. 当前页数据量小于每页请求量（说明是最后一页）
                # 2. 当前页数据量为零（异常情况保护）
                if len(current_page_tasks) < records_per_page or not current_page_tasks:
                    break

                # 更新分页参数准备下次请求
                base_params["page"] += 1  # 页码递增
                current_page = base_params["page"]  # 保持当前页码状态同步

            except requests.JSONDecodeError as decode_err:
                # 捕获JSON解析异常并附加调试信息
                raw_content: str = api_response.text[:200] + "..." if api_response.text else "空响应内容"
                error_msg: str = f"响应内容解析失败，原始内容：{raw_content}"
                raise ValueError(error_msg) from decode_err

            except KeyError as key_err:
                # 细化键缺失异常信息
                raise KeyError(f"数据结构异常，缺失关键字段：{str(key_err)}") from key_err

    def get_bug_list(self) -> None:
        """
        获取指定需求关联的缺陷列表并存储到类属性中，同时提取平台和根源的分类元数据

        核心功能：
        1. 通过TAPD搜索接口分页获取指定需求的所有缺陷数据
        2. 提取平台和根源的分类选项信息并存储到类属性
        3. 将完整的缺陷数据集存储到self.bugs类属性

        执行流程：
        1. 初始化分页参数和存储结构
        2. 构建符合TAPD接口规范的动态搜索条件
        3. 分页发送API请求并验证响应数据结构
        4. 提取平台和根源分类的元数据存储到self.bugPlatforms和self.bugSources
        5. 合并分页数据到self.bugs并进行完整性校验

        类属性更新：
            - self.bugPlatforms: 平台分类选项列表，按TAPD系统配置顺序排列
                                 示例：["iOS", "Android", "Web"]
            - self.bugSources: 缺陷根源分类选项列表，按TAPD系统配置顺序排列
                               示例：["代码错误", "需求变更", "环境配置"]
            - self.bugs: 缺陷数据字典列表，每个字典对应一个缺陷的完整字段数据
                         示例：[{"id": "BUG001", "title": "登录按钮无响应", ...}, ...]

        异常：
            ValueError: 当响应数据格式异常或关键字段缺失时抛出
            KeyError: 当接口返回数据结构不符合预期时抛出
            requests.JSONDecodeError: 当响应内容无法解析为JSON格式时抛出

        关联方法：
            fetch_data(): 执行API请求的核心方法，处理网络通信和基础错误重试
        """
        # ==================================================================
        # 阶段1：初始化分页参数
        # ==================================================================
        current_page: int = 1  # 当前请求页码，从第一页开始
        page_size: int = 100  # 每页请求数据量，使用TAPD API允许的最大值

        # ==================================================================
        # 阶段2：构建动态搜索条件
        # ==================================================================
        # 构造符合TAPD搜索接口规范的JSON查询条件
        # 关键字段说明：
        # - fieldSystemName: 指定搜索的字段为"关联需求"
        # - value: 使用输入的需求名称作为搜索值
        # - optionType: 使用逻辑与(AND)组合多个查询条件
        search_condition = json.dumps({
            "data": [{
                "id": "5",  # 条件ID，TAPD系统保留字段
                "fieldLabel": "关联需求",  # 界面显示的字段标签
                "fieldOption": "like",  # 使用模糊匹配操作符
                "fieldType": "input",  # 字段类型为文本输入
                "fieldSystemName": "BugStoryRelation_relative_id",  # 系统内部字段标识
                "value": self.requirementName,  # 搜索的目标需求名称
                "fieldIsSystem": "1",  # 标记为系统内置字段
                "entity": "bug"  # 查询实体类型为缺陷
            }],
            "optionType": "AND",  # 条件组合方式
            "needInit": "1"  # 需要初始化搜索条件标志
        })

        # ==================================================================
        # 阶段3：分页请求控制
        # ==================================================================
        # 构造基础请求参数模板，分页参数将在循环中动态更新
        base_request_data = {
            "workspace_ids": PROJECT_ID,  # 项目空间唯一标识
            "search_data": search_condition,  # 序列化的搜索条件
            "obj_type": "bug",  # 查询对象类型为缺陷
            "hide_not_match_condition_node": "0",  # 显示不匹配条件节点
            "hide_not_match_condition_sub_node": "1",  # 隐藏不匹配子节点
            "page": current_page,  # 当前页码参数
            "perpage": str(page_size),  # 每页数据量参数（字符串类型）
            "order_field": "created",  # 按缺陷创建时间升序排列
        }

        # 分页请求循环，直到获取全部数据
        while True:
            # ==================================================================
            # 阶段4：发送API请求
            # ==================================================================
            # 使用封装的fetch_data方法发送POST请求
            # 该方法已内置网络错误重试和会话管理功能
            response = fetch_data(
                url=f"{HOST}/api/search_filter/search_filter/search",
                json=base_request_data,
                method="POST"
            )

            try:
                # ==================================================================
                # 阶段5：响应数据处理
                # ==================================================================
                # 将响应内容解析为JSON格式（可能抛出JSONDecodeError）
                response_data: Dict[str, Any] = response.json()

                # 数据完整性校验：检查顶层data字段
                if "data" not in response_data:
                    raise KeyError("API响应缺少核心数据域'data'字段")

                # ==================================================================
                # 阶段6：元数据提取（仅在首次请求时执行）
                # ==================================================================
                if not self.bugPlatforms or not self.bugSources:
                    # 验证项目特殊字段结构
                    project_fields = response_data["data"].get("project_special_fields")

                    if project_fields:
                        if not isinstance(project_fields, dict):
                            raise ValueError("'project_special_fields'字段类型异常，预期字典类型")

                        # 获取当前项目的分类配置数据
                        project_config = project_fields.get(PROJECT_ID, {})

                        # 提取平台分类选项（防御性字段检查）
                        if "platform" in project_config and not self.bugPlatforms:
                            self.bugPlatforms = [
                                str(item["value"])  # 强制类型转换为字符串
                                for item in project_config["platform"]
                                if "value" in item
                            ]

                        # 提取根源分类选项（防御性字段检查）
                        if "source" in project_config and not self.bugSources:
                            self.bugSources = [
                                str(item["value"])  # 强制类型转换为字符串
                                for item in project_config["source"]
                                if "value" in item
                            ]

                # ==================================================================
                # 阶段7：缺陷数据处理
                # ==================================================================
                # 校验列表数据字段存在性
                if "list" not in response_data["data"]:
                    raise KeyError("响应数据缺失缺陷列表字段'list'")

                current_page_bugs = response_data["data"]["list"]

                # 数据类型二次校验（防御性编程）
                if not isinstance(current_page_bugs, list):
                    raise TypeError(
                        f"缺陷数据格式异常，预期列表类型，实际类型：{type(current_page_bugs)}"
                    )

                # 合并分页数据到总集合
                self.bugs.extend(current_page_bugs)

                # ==================================================================
                # 阶段8：分页终止判断
                # ==================================================================
                # 当前页数据量小于请求量时终止循环（最后一页）
                if len(current_page_bugs) < page_size:
                    break

                # 更新分页参数准备下次请求
                base_request_data["page"] += 1
                current_page = base_request_data["page"]

            except requests.JSONDecodeError as decode_err:
                # 捕获JSON解析异常并附加原始响应内容
                raw_content = response.text[:200] + "..." if response.text else "空响应内容"
                raise ValueError(
                    f"响应内容解析失败，原始内容：{raw_content}"
                ) from decode_err

    def get_all_list_data(self) -> None:
        """
        执行需求相关数据的全量获取与完整性校验流程

        本方法实现完整的质量控制流程，包含以下关键环节：
        1. 配置管理：临时修改列表视图配置以适配数据采集需求
        2. 数据采集：并发获取需求子任务和缺陷数据
        3. 完整性校验：多维度验证数据的业务合规性
        4. 错误处理：结构化收集和呈现数据质量问题

        流程架构：
            配置准备 -> 数据采集 -> 配置还原 -> 业务校验 -> 异常处理

        异常检测范围：
            - 子任务状态异常
            - 关键字段缺失
            - 测试任务完整性
            - 缺陷平台信息合规性

        关联方法：
            edit_list_config()：配置管理方法
            restore_list_config()：配置恢复方法
            _print_error()：标准化错误输出方法
        """
        # ==================================================================
        # 阶段1：初始化准备
        # ==================================================================
        # 定义结构化错误存储容器
        sub_demand_task_error: Dict[str, List[str]] = {}  # 子任务错误分类存储
        bug_error: Dict[str, List[str]] = {}  # 缺陷错误分类存储
        is_exist_test_task: bool = False  # 测试任务存在性标识

        # 打印流程启动标识
        print(' 前置准备 '.center(LINE_LENGTH, '='))

        # ==================================================================
        # 阶段2：视图配置管理
        # ==================================================================
        # 修改列表视图配置以适配数据采集需求
        self.edit_list_config()

        # ==================================================================
        # 阶段3：数据采集执行
        # ==================================================================
        # 执行数据获取流程（含进度提示）
        print('正在获取数据', end='')
        for i in range(3):  # 模拟进度指示
            time.sleep(1)
            print('.', end='')

        # 并发获取需求子任务和缺陷数据
        self.get_requirement_tasks()  # 需求子任务获取
        self.get_bug_list()  # 缺陷列表获取
        print('完成')  # 完成提示

        # ==================================================================
        # 阶段4：视图配置恢复
        # ==================================================================
        # 还原列表视图至原始配置
        self.restore_list_config()

        # ==================================================================
        # 阶段5：数据完整性校验
        # ==================================================================
        print('正在进行数据校验', end='')
        for i in range(3):  # 校验进度指示
            time.sleep(1)
            print('.', end='')

        # 校验子任务基础数据完整性
        if not self.subDemandTasks:
            self._print_error("失败\n警告：未获取任何子任务数据，请检查需求任务")

        # ==================================================================
        # 阶段6：子任务业务规则校验
        # ==================================================================
        # 遍历所有子任务进行多维度检查
        for subDemandTask in self.subDemandTasks:
            # 解构任务属性
            owner = subDemandTask['owner']

            # 校验点1：子任务状态合规性
            if subDemandTask['status'] != 'done':
                if 'undone' not in sub_demand_task_error:
                    sub_demand_task_error['undone'] = ['需求存在未完成的子任务：\n']
                sub_demand_task_error['undone'].append(
                    f"任务名称：{subDemandTask['name']}{f'，处理人：{owner}' if owner else ''}\n"
                )
                continue

            # 校验点2：关键字段完整性
            check_sub_demand_task_key_result = list(
                msg for key, msg in {
                    'begin': '预计开始日期',
                    'due': '预计结束日期',
                    'owner': '处理人',
                }.items() if not subDemandTask.get(key)
            )

            # 收集缺失字段信息
            if check_sub_demand_task_key_result:
                if 'lackValue' not in sub_demand_task_error:
                    sub_demand_task_error['lackValue'] = ['警告：需求存在关键字段缺失：\n']
                sub_demand_task_error['lackValue'].append(
                    f"任务名称：{subDemandTask['name']}，关键字段缺少值：{'、'.join(check_sub_demand_task_key_result)}\n"
                )

            # 校验点3：测试任务存在性
            if owner and owner.replace(DEPARTMENT, '').replace(';', '') in TESTERS and not is_exist_test_task:
                is_exist_test_task = True

        # ==================================================================
        # 阶段7：全局规则校验
        # ==================================================================
        # 校验测试任务全局存在性
        if not is_exist_test_task:
            sub_demand_task_error['nonExistentTestTask'] = ['警告：需求不存在测试任务，请完善需求任务！\n']

        # ==================================================================
        # 阶段8：缺陷数据校验
        # ==================================================================
        # 遍历所有缺陷进行合规性检查
        for bug in self.bugs:
            # 校验点1：缺陷平台信息完整性
            check_bug_key_result = list(
                msg for key, msg in {
                    'platform': '软件平台',
                }.items() if not bug.get(key)
            )

            # 收集平台信息缺失数据
            if check_bug_key_result:
                if 'lackValue' not in bug_error:
                    bug_error['lackValue'] = ['警告：BUG存在关键字段缺失：\n']
                bug_error['lackValue'].append(
                    f"BUG名称：{bug['name']}，关键字段缺少值：{'、'.join(check_bug_key_result)}\n"
                )

            # 记录存在的软件平台类型
            if bug['platform'] and bug['platform'] not in self.bugExistPlatforms:
                self.bugExistPlatforms.append(bug['platform'])

        # ==================================================================
        # 阶段9：异常信息整合输出
        # ==================================================================
        # 结构化整合错误信息
        if sub_demand_task_error or bug_error:
            error_texts: List[str] = []

            # 整合测试任务缺失错误
            if sub_demand_task_error.get('nonExistentTestTask'):
                error_texts.append(sub_demand_task_error['nonExistentTestTask'][0])

            # 整合未完成任务信息
            if sub_demand_task_error.get('undone') and len(sub_demand_task_error['undone']) > 1:
                error_texts.append('    '.join(sub_demand_task_error["undone"]))

            # 整合字段缺失信息
            if sub_demand_task_error.get('lackValue') and len(sub_demand_task_error['lackValue']) > 1:
                error_texts.append('    '.join(sub_demand_task_error["lackValue"]))

            # 整合缺陷字段缺失信息
            if bug_error.get('lackValue') and len(bug_error['lackValue']) > 1:
                error_texts.append('    '.join(bug_error["lackValue"]))

            # 统一输出错误信息
            self._print_error('失败\n' + ''.join(error_texts))

        # ==================================================================
        # 阶段10：流程完成确认
        # ==================================================================
        print('通过')


    def question_stage(self) -> None:
        """
        执行需求上线相关的客户端选择与日期输入流程

        该方法引导用户完成以下交互流程：
        1. 确认是否需要处理多客户端上线场景
        2. 选择涉及上线的客户端列表
        3. 验证客户端选择的有效性
        4. 收集各客户端的实际上线日期

        流程特性：
        - 支持多客户端批量选择
        - 提供可视化客户端选项菜单
        - 输入格式严格校验
        - 客户端与BUG数据一致性检查
        """
        # ==================================================================
        # 阶段1：初始化与基础校验
        # ==================================================================
        # 防御性检查：当不存在BUG数据时提前终止流程
        if not self.bugs:
            return

        # 初始化交互过程数据容器
        online_clients: List[str] = []
        error_numbers: List[str] = []

        # 打印阶段标题（居中显示）
        print(' 提问阶段 '.center(LINE_LENGTH, '='))

        # ==================================================================
        # 阶段2：用户交互-上线场景确认
        # ==================================================================
        # 获取多客户端上线场景确认
        is_multi_client_online: str = _input(
            '问题1: 是否存在不同客户端分开上线的任务或者是否需要手动输入上线日期?(y/n): ',
            input_type=str,
            allow_contents=['y', 'n']
        ).lower()

        # 处理否定应答场景
        if is_multi_client_online == 'n':
            return

        # ==================================================================
        # 阶段3：客户端选择处理
        # ==================================================================
        # 标记需要手动输入上线日期
        self.isInputOnlineDate = True

        # 构建客户端选择菜单文本
        question_client_select_text = '问题2: 涉及上线的客户端有哪些?\n'
        for idx, client in enumerate(CLIENTS, 1):
            question_client_select_text += f"{idx}. {client}\n"

        # 客户端选择输入循环
        while True:
            # 获取并清洗客户端序号输入
            client_number_str: str = _input(
                question_client_select_text + '输入序号并使用英文逗号隔开: ',
                input_type=str,
                is_delete_space=True
            )

            # 解析输入序号并验证有效性
            for client_number in client_number_str.split(','):
                if client_number:
                    # 非数字输入检测
                    if not client_number.isdigit():
                        online_clients.clear()
                        break
                    # 范围有效性校验
                    if len(CLIENTS) < int(client_number) or int(client_number) < 1:
                        error_numbers.append(client_number)
                    else:
                        online_clients.append(CLIENTS[int(client_number) - 1])

            # 错误输入处理
            if error_numbers:
                print(_print_text_font(f'输入错误, 请重新输入, 错误序号: {", ".join(error_numbers)}'))
                online_clients.clear()
                error_numbers.clear()
            elif not online_clients:
                print(_print_text_font('输入错误, 请重新输入'))
            else:
                # ==================================================================
                # 阶段4：客户端有效性校验
                # ==================================================================
                # 检查选择的客户端是否在BUG数据中存在
                error_clients = self._check_bug_client(online_clients)
                if error_clients:
                    online_clients.clear()
                    print(_print_text_font(f'BUG中存在未选择的客户端({"、".join(error_clients)})，请检查BUG单后重新选择'))
                else:
                    break

        # ==================================================================
        # 阶段5：在线日期收集
        # ==================================================================
        for number, onlineClient in enumerate(online_clients, 3):
            # 获取并格式化上线日期输入
            client_online_date: str = _input(
                f'问题{number}: 客户端{onlineClient}上线时间?(格式：2023-07-01): ',
                input_type=str,
                re_format=r'\d{4}-\d{1,2}-\d{1,2}',
                re_prompts_format='YYYY-MM-DD',
                is_delete_space=True,
            )
            # 存储日期数据（转换为date类型）
            self.onlineDateDict[onlineClient] = date_time_to_date(client_online_date)


    def requirement_task_statistics(self) -> None:
        """
        统计需求关联的子任务数据，计算开发工时并识别关键时间节点

        核心功能：
        1. 解析子任务数据，分离开发任务和测试任务
        2. 计算开发者总工时和每日工时分布
        3. 记录项目关键时间节点（最早/最晚任务日期、上线日期）
        4. 维护测试相关数据（测试负责人、收件人列表）

        参数:
            无，通过实例属性self.subDemandTasks获取子任务数据

        返回:
            无，结果直接更新实例属性

        异常:
            ValueError: 当子任务数据格式异常时抛出
            KeyError: 当子任务缺少必要字段时抛出
        """
        # ==================================================================
        # 阶段1：子任务数据遍历处理
        # ==================================================================
        for child in self.subDemandTasks:
            try:
                # ==================================================================
                # 步骤1.1：基础数据提取
                # ==================================================================
                # 获取任务处理人名称并去除部门前缀
                raw_owner = child['owner'].replace(";", "")  # 原始处理人格式示例：T5张三
                processing_personnel = extract_matching(rf"{DEPARTMENT}(.*?)$", raw_owner)[0]  # 提取纯用户名：张三

                # ==================================================================
                # 步骤1.2：工时数据转换
                # ==================================================================
                # 转换字符串类型工时数为浮点数，缺失值时默认为0
                effort_completed = float(child.get('effort_completed', 0))

                # ==================================================================
                # 步骤1.3：日期数据提取
                # ==================================================================
                # 获取任务计划时间范围（ISO 8601格式字符串）
                begin_date = child['begin']  # 预计开始日期
                due_date = child['due']  # 预计结束日期

            except (ValueError, TypeError) as e:
                # ==================================================================
                # 异常处理：数据转换失败
                # ==================================================================
                error_msg = f"子任务数据格式异常：{str(e)}\n问题数据：{json.dumps(child, indent=2)}"
                raise ValueError(error_msg) from e
            except KeyError as e:
                # ==================================================================
                # 异常处理：关键字段缺失
                # ==================================================================
                error_msg = f"子任务缺少必要字段：{str(e)}\n问题数据：{json.dumps(child, indent=2)}"
                raise KeyError(error_msg) from e

            # ==================================================================
            # 阶段2：任务分类处理
            # ==================================================================
            if processing_personnel not in TESTERS:
                # ==================================================================
                # 分支2.1：开发任务处理
                # ==================================================================
                # 收集开发者工时数据并更新开发周期
                self._process_developer_task(
                    developer=processing_personnel,
                    effort=effort_completed,
                    begin=begin_date,
                    due=due_date,
                    child_data=child
                )
            else:
                # ==================================================================
                # 分支2.2：测试任务处理
                # ==================================================================
                # 更新测试负责人信息并记录关键时间节点
                self._process_tester_task(
                    due_date=due_date,
                    begin_date=begin_date,
                    owner=raw_owner
                )

        # ==================================================================
        # 阶段3：后期数据校验
        # ==================================================================
        # 检查关键时间节点的数据完整性
        if not self.earliestTaskDate:
            self._print_error(f"警告：未识别到最早任务日期，请检查{self.requirementName}需求的开发任务预期开始时间")
        if not self.lastTaskDate:
            self._print_error(f"警告：未识别到最晚任务日期，请检查{self.requirementName}需求的测试任务预期结束时间")
        if not self.onlineDate and not self.isInputOnlineDate:
            self._print_error(f"警告：未识别到上线日期，请检查{self.requirementName}需求的测试任务预期开始时间")


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
        print(' 统计工时和缺陷 '.center(LINE_LENGTH, '='))
        print(' 各开发人员花费的工时 '.center(LINE_LENGTH, '-'))

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

        方法流程：
            1. 缺陷数据遍历处理：逐条处理缺陷记录并进行多维度统计
            2. 后处理与结果输出：汇总统计结果并输出关键指标

        核心处理逻辑：
            - 缺陷数据过滤：跳过状态为'rejected'的无效缺陷
            - 关键字段提取：ID、严重等级、缺陷根源、平台等核心字段
            - 数据标准化：统一字段格式，处理空值和异常数据
            - 多维度统计：按严重等级、根源分类、平台分布进行聚合统计
            - 生命周期跟踪：记录缺陷状态流转轨迹，检测未修复缺陷
            - 时序数据分析：跟踪每日缺陷创建/解决/关闭趋势

        异常处理：
            - KeyError：捕获字段缺失异常，记录日志并跳过当前缺陷
            - ValueError：处理数据格式异常，记录日志并跳过当前缺陷

        关联方法调用：
            get_bug_list()        : TAPD接口分页获取缺陷数据
            multi_client_data_processing() : 多客户端维度数据聚合
            date_time_to_date()   : 日期格式标准化处理器
            _statistics_deploy_prod_day_unrepaired_bug() : 上线未修复缺陷检测
            _statistics_on_that_day_unrepaired_bug() : 创建日未修复缺陷检测
            _daily_trend_of_bug_changes_count() : 缺陷状态时序分析

        数据结构说明：
            self.bugLevelsCount     : 缺陷严重等级计数器（P0/P1/P2）
            self.bugSourceCount     : 缺陷根源分类计数器
            self.bugLevelsMultiClientCount : 平台×严重等级矩阵统计
            self.bugSourceMultiClientCount : 平台×缺陷根源矩阵统计
            self.bugIds             : 有效缺陷ID集合
            self.unrepairedBugsData : 顽固缺陷跟踪字典
            self.fixers             : 缺陷修复人统计字典
        """
        # 控制台输出分割线（可视化模块边界）
        print(' 不同等级的缺陷的数量 '.center(LINE_LENGTH, '-'))

        # ==================================================================
        # 阶段1：缺陷数据遍历处理
        # ==================================================================

        # 空数据场景处理（防御性编程）
        if not self.bugs:
            print('未获取到有效缺陷数据')
            return

        # 遍历原始缺陷记录（每条记录为字典结构）
        for bug in self.bugs:
            # ==================================================================
            # 步骤1.1：基础字段提取与过滤
            # ==================================================================

            # 过滤已拒绝状态的缺陷（无效数据跳过）
            bug_status = bug.get('status', '')
            if bug_status == 'rejected':
                continue

            # ==================================================================
            # 步骤1.2：关键字段提取与清洗
            # ==================================================================

            # 提取核心字段（防御性get方法避免KeyError）
            bug_id = bug.get('id')  # 缺陷唯一标识符
            severity_name = bug.get('custom_field_严重等级', '')  # 原始严重等级
            bug_source = bug.get('source', '')  # 缺陷根源分类
            bug_platform = bug.get('platform')  # 客户端平台标识

            # ==================================================================
            # 步骤1.3：数据标准化处理
            # ==================================================================

            # 严重等级格式清洗（示例："P1-严重" → "P1"）
            if severity_name and '-' in severity_name:
                severity_name = severity_name.split('-')[0].strip()

            # 空值处理与默认值设置（保证统计完整性）
            severity_name = severity_name if severity_name else '空'
            bug_source = bug_source if bug_source else '空'
            bug_platform = bug_platform if bug_platform else '空'

            try:
                # ==================================================================
                # 步骤1.4：核心统计逻辑
                # ==================================================================

                # 更新全局统计计数器
                self.bugLevelsCount[severity_name] += 1  # 严重等级统计
                self.bugSourceCount[bug_source] += 1     # 缺陷根源统计

                # 执行多维度矩阵统计（平台×严重等级）
                multi_client_data_processing(
                    result=self.bugLevelsMultiClientCount,
                    key=bug_platform,
                    all_sub_keys=BUG_LEVELS,
                    sub_key=severity_name
                )

                # 执行多维度矩阵统计（平台×缺陷根源）
                multi_client_data_processing(
                    result=self.bugSourceMultiClientCount,
                    key=bug_platform,
                    all_sub_keys=self.bugSources,
                    sub_key=bug_source
                )

                # ==================================================================
                # 步骤1.5：缺陷生命周期跟踪
                # ==================================================================

                if bug_id:  # 仅处理有效缺陷ID
                    # 记录缺陷ID（用于后续跟踪）
                    self.bugIds.append(bug_id)

                    # 标准化日期格式（处理多种输入格式）
                    created_date = date_time_to_date(bug.get('created', ''))
                    resolved_date = date_time_to_date(bug['resolved']) if bug.get('resolved') else None

                    # 顽固缺陷检测（特定标签处理）
                    if bug.get('custom_field_Bug等级') == '顽固（180 天）':
                        self.unrepairedBugsData[bug_id] += 1

                    # 上线未修复缺陷检测（生产环境）
                    self._statistics_deploy_prod_day_unrepaired_bug(
                        bug_status=bug_status,
                        bug_platform=bug_platform,
                        bug_id=bug_id,
                        severity_name=severity_name,
                        resolved_date=resolved_date
                    )

                    # 创建日未修复缺陷检测（开发阶段）
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
                # 步骤1.6：时序数据分析
                # ==================================================================

                # 更新每日缺陷趋势（创建/解决/关闭状态）
                self._daily_trend_of_bug_changes_count(bug)

            except KeyError as e:
                # 字段缺失异常处理（记录日志并跳过）
                self._print_error(f"警告：缺陷数据缺失关键字段 {str(e)}，缺陷ID: {bug_id}")
            except ValueError as e:
                # 数据格式异常处理（记录日志并跳过）
                self._print_error(f"警告：数据格式异常 {str(e)}，缺陷ID: {bug_id}")

        # ==================================================================
        # 阶段2：后处理与结果输出
        # ==================================================================

        # 计算有效缺陷总数（基于ID数量）
        self.bugTotal = len(self.bugIds)

        # 控制台输出统计摘要（严重等级分布）
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
            self._print_error(f"警告：输入数据异常：{str(e)}")
        except Exception as e:
            # 通用异常处理
            self._print_error(f"警告：评分系统错误：{str(e)}")

    def development_cycle(self) -> None:
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
            self._print_error("警告：未获取到开发者每日工时数据")

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
            self._print_error("警告：开发周期计算结果为非正数，请检查输入数据有效性")

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

        # 存储项目测试人员和测试接收人
        self._processing_tester_list()

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
            # 'tableData': {
            #     'tableWidth': work_hour_plot_data['plotData']['widthPx'],
            #     'data': self.workHours,
            #     'headers': ['开发人员', '工时'],
            # }
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

    def edit_list_config(self) -> None:
        """
        配置列表视图的必要展示字段

        该方法确保BUG列表和子任务列表包含脚本运行所需的必要字段，通过以下步骤实现：
        1. 获取当前列表配置
        2. 合并必要字段到新配置
        3. 仅当配置发生变化时执行更新
        4. 严格的异常处理和状态回滚

        处理流程:
            1. 配置初始化检查
            2. 必要字段合并处理
            3. 差异比较与条件更新
            4. 原子化配置操作
            5. 事务性错误处理

        异常策略:
            - 使用断言确保配置操作成功
            - 捕获底层异常并附加上下文信息
            - 异常时打印完整堆栈跟踪
            - 保持异常传播不丢失原始信息
        """
        try:
            # ==================================================================
            # 阶段1：配置初始化
            # ==================================================================
            # 防御性获取配置：仅在未初始化时获取原始配置
            if not all([self.oldBugListConfigStr, self.oldSubTaskListConfigStr]):
                self._get_list_config()

            # ==================================================================
            # 阶段2：配置合并处理
            # ==================================================================
            bug_fields = list(self.oldBugListConfigStr.split(';'))
            bug_fields.extend(BUG_LIST_MUST_KEYS)
            new_bug_config = ';'.join(bug_fields)

            task_fields = list(self.oldSubTaskListConfigStr.split(';'))
            task_fields.extend(SUB_TASK_LIST_MUST_KEYS)
            new_task_config = ';'.join(task_fields)

            # ==================================================================
            # 阶段3：条件更新检查
            # ==================================================================
            # 仅当配置实际变化时执行更新操作
            config_modified = False

            if new_bug_config != self.oldBugListConfigStr:
                # 原子化BUG列表配置更新
                success = edit_query_filtering_list_config(new_bug_config)
                assert success, "BUG列表配置更新失败"
                config_modified = True

            if new_task_config != self.oldSubTaskListConfigStr:
                # 原子化子任务列表配置更新
                success = edit_requirement_list_config(new_task_config)
                assert success, "子任务列表配置更新失败"
                config_modified = True

            # ==================================================================
            # 阶段4：状态标记
            # ==================================================================
            # 仅在成功修改配置后标记初始化状态
            if config_modified:
                self.isInitialListConfig = False

        except AssertionError as ae:
            # 处理业务逻辑断言失败
            error_msg = f"配置验证失败: {str(ae)}"
            traceback.print_exc()
            raise RuntimeError(error_msg) from ae
        except Exception as e:
            # 处理不可预见异常
            error_msg = f"配置更新异常: {str(e)}"
            traceback.print_exc()
            raise RuntimeError(error_msg).with_traceback(e.__traceback__) from e

    def restore_list_config(self) -> None:
        """
        还原列表视图的字段展示配置到初始状态

        本方法通过调用TAPD官方API接口，将缺陷列表和需求子任务列表的字段展示配置
        恢复到脚本运行前的原始状态。该方法通常在脚本执行结束时调用，确保系统配置
        不受脚本运行影响。

        处理流程:
            1. 判断是否需要还原配置
            2. 还原缺陷列表视图配置
            3. 还原需求子任务列表视图配置
            4. 更新配置初始化状态标记

        异常处理:
            AssertionError: 当配置还原操作失败时抛出
            Exception: 当发生未预料异常时抛出

        关联方法:
            edit_query_filtering_list_config(): 编辑缺陷列表视图配置
            edit_requirement_list_config(): 编辑需求子任务列表视图配置
        """
        try:
            # ==================================================================
            # 阶段1：判断是否需要还原配置
            # ==================================================================
            # 如果配置已经初始化，则无需还原
            if self.isInitialListConfig:
                return

            # ==================================================================
            # 阶段2：还原缺陷列表视图配置
            # ==================================================================
            # 调用API接口还原缺陷列表视图配置，使用原始配置字符串
            # 断言确保操作成功，失败时抛出AssertionError
            assert edit_query_filtering_list_config(self.oldBugListConfigStr)

            # ==================================================================
            # 阶段3：还原需求子任务列表视图配置
            # ==================================================================
            # 调用API接口还原需求子任务列表视图配置，使用原始配置字符串
            # 断言确保操作成功，失败时抛出AssertionError
            assert edit_requirement_list_config(self.oldSubTaskListConfigStr)

        except AssertionError as ae:
            # 捕获配置还原失败异常
            # 打印完整堆栈信息，保留原始异常上下文
            traceback.format_exc()
            # 重新抛出异常，确保调用方能够处理
            raise ae
        except Exception as e:
            # 捕获其他未预料异常
            # 打印完整堆栈信息，保留原始异常上下文
            traceback.format_exc()
            # 重新抛出异常，确保调用方能够处理
            raise e
        else:
            # ==================================================================
            # 阶段4：更新配置初始化状态
            # ==================================================================
            # 仅在成功还原配置后标记初始化状态为True
            # 表示当前配置已恢复到原始状态
            self.isInitialListConfig = True

    def get_reopen_bug_detail(self) -> None:
        """
        获取并统计重新打开的缺陷详细信息

        本方法通过多线程并发请求，获取每个缺陷的状态流转历史记录，并统计每个缺陷被重新打开的次数。
        该方法适用于需要分析缺陷生命周期中重新打开情况的场景，能够高效处理大量缺陷数据。

        处理流程:
            1. 初始化请求执行数据字典，用于存储每个缺陷ID对应的Future对象
            2. 创建线程池执行器，并发获取每个缺陷的状态流转历史
            3. 遍历请求结果，统计每个缺陷的重新打开次数
            4. 更新类属性reopenBugsData，记录每个缺陷的重新打开次数

        异常处理:
            - 捕获线程池执行过程中的异常，确保程序稳定性
            - 处理API请求失败或数据解析异常的情况

        关联方法:
            get_workitem_status_transfer_history(): 获取缺陷状态流转历史记录
        """
        # 初始化请求执行数据字典，用于存储每个缺陷ID对应的Future对象
        request_exec_data = {}

        # 定义实体类型为'bug'，用于后续API请求
        entity_type = 'bug'

        try:
            # 使用线程池执行器并发获取缺陷状态流转历史
            with ThreadPoolExecutor(max_workers=None) as executor:
                # 遍历缺陷ID列表，为每个缺陷提交一个任务到线程池
                for bug_id in self.bugIds:
                    # 提交任务到线程池，并将返回的Future对象存储在request_exec_data中
                    request_exec_data[bug_id] = executor.submit(
                        get_workitem_status_transfer_history, entity_type, bug_id
                    )

            # 遍历请求结果，统计每个缺陷的重新打开次数
            for bug_id, future in request_exec_data.items():
                try:
                    # 获取缺陷状态流转历史记录
                    status_history_list = future.result()

                    # 遍历状态流转历史，查找重新打开的状态记录
                    for status_history in status_history_list:
                        if status_history['current_status_origin'] == 'reopened':
                            # 更新缺陷的重新打开次数
                            self.reopenBugsData[bug_id] += 1
                except Exception as e:
                    # 捕获单个缺陷请求或数据处理中的异常，记录日志并继续处理其他缺陷
                    print(f"处理缺陷 {bug_id} 时发生异常: {str(e)}")
                    continue

        except Exception as e:
            # 捕获线程池或整体流程中的异常，记录日志并抛出
            error_msg = f"获取缺陷重新打开详情失败: {str(e)}"
            raise RuntimeError(error_msg) from e

    def _charts_to_html(self, charts: list) -> None:
        """
        将图表数据转换为标准化的HTML结构，包含图像和表格

        本方法支持处理多维数据和非多维数据的展示逻辑，主要功能包括：
        1. 解析图表元数据生成图像标签
        2. 判断生成多维表格还是简单表格
        3. 动态构建表格HTML数据
        4. 维护样式一致性

        处理流程:
            1. 入参数据校验
            2. 图像元素处理
            3. 表格数据结构校验
            4. 表格行数据排序
            5. 判断并构建多维表格或者简单表格

        参数:
            charts: 图表数据列表，包含图表路径和表格元数据
        """
        # ==================================================================
        # 阶段1：入参数据校验
        # ==================================================================
        if not isinstance(charts, list):
            raise TypeError(f'charts数据类型错误，期望是列表，实际为：{type(charts).__name__}')

        for index, chart in enumerate(charts):
            # 如果chart数据不是字典则跳过
            if not isinstance(chart, dict):
                continue
            # ==================================================================
            # 阶段2：图表处理
            # ==================================================================
            # 如果存在图表数据时则生成图像图表的HTML
            if chart.get('plotPath'):
                self.chartHtml += f'''
                <div>
                    <img src="{chart["plotPath"]}" />
                </div>'''

            # ==================================================================
            # 阶段3：表格数据校验
            # ==================================================================
            table_data: dict = chart.get('tableData', {}) if isinstance(chart, dict) else {}
            if table_data:
                if 'data' not in table_data:
                    raise ValueError(f'第{index + 1}个表格数据中缺少"data"键')

                if not isinstance(table_data['data'], dict):
                    raise TypeError(
                        f'第{index + 1}个表格数据中"data"键的数据格式不正确，期望为字典类型，实际为{type(table_data["data"]).__name__}'
                    )

                if 'tableWidth' not in table_data:
                    raise ValueError(f'第{index + 1}个表格数据中缺少"tableWidth"键')

                if not isinstance(table_data['tableWidth'], int or float):
                    raise TypeError(
                        f'第{index + 1}个表格数据中"tableWidth"键的数据格式不正确，期望为整数或者浮点数类型，实际为{type(table_data["tableWidth"]).__name__}'
                    )

                # ==================================================================
                # 阶段4：表格行数据排序
                # ==================================================================
                if table_data.get('sort') in ('asc', 'desc'):
                    table_data['data'] = dict(sorted(
                        table_data['data'].items(),
                        key=lambda x: x[0].lower() if isinstance(x[0], str) else x[0],
                        reverse=table_data['sort'] == 'desc'
                    ))

                # ==================================================================
                # 阶段5：生成表格HTML
                # ==================================================================
                # 如果多维表格标记为True，则生成多维表格的HTML， 否则生成简单表格
                if table_data.get('isMultiDimensionalTable'):
                    # 执行多维表格的HTML生成
                    self._add_multi_dimensional_table_html(table_data)
                else:
                    # 执行简单表格的HTML生成
                    self._add_simple_table_html(table_data)

            # ==================================================================
            # 阶段9：间隔处理（保持原始视觉效果）
            # ==================================================================
            interval = 5 if index != len(charts) - 1 else 2
            self.chartHtml += '<div><br /></div>' * interval

    def _get_list_config(self) -> None:
        """
        获取并存储当前列表视图的字段展示配置信息

        本方法通过TAPD官方API接口，获取缺陷列表和需求子任务列表的当前字段配置，
        并将配置信息转换为分号分隔的字符串格式存储到类属性中，供后续配置比对使用

        流程说明:
            1. 获取缺陷列表视图的字段展示配置
            2. 获取需求子任务列表的字段展示配置
            3. 将列表格式的配置转换为标准化的字符串格式
            4. 存储配置信息到类属性供后续使用

        异常:
            KeyError: 当接口返回数据缺少关键字段时抛出
            requests.RequestException: 当API请求失败时抛出

        关联方法:
            get_query_filtering_list_config(): 获取缺陷列表视图配置
            get_requirement_list_config(): 获取需求子任务列表配置
        """
        # ==================================================================
        # 阶段1：获取缺陷列表视图配置
        # ==================================================================
        # 调用API接口获取缺陷列表展示字段配置，返回字段标识符列表
        # 示例返回数据：['id', 'title', 'status', 'platform']
        bug_list_configs = get_query_filtering_list_config()

        # ==================================================================
        # 阶段2：获取子任务列表视图配置
        # ==================================================================
        # 调用API接口获取需求子任务列表展示字段配置，返回字段标识符列表
        # 示例返回数据：['owner', 'due', 'status']
        sub_task_list_configs = get_requirement_list_config()

        # ==================================================================
        # 阶段3：数据格式转换
        # ==================================================================
        # 将列表转换为分号分隔的字符串格式，用于后续配置比对
        # 示例结果转换：['id','title'] → "id;title"
        self.oldBugListConfigStr = ';'.join(bug_list_configs)  # 缺陷列表字段配置字符串
        self.oldSubTaskListConfigStr = ';'.join(sub_task_list_configs)  # 子任务列表字段配置字符串

    def _daily_trend_of_bug_changes_count(self, data: Dict[str, Any]) -> None:
        """
        统计缺陷每日状态变化趋势，跟踪每个缺陷在整个生命周期中对每日统计指标的影响

        本方法通过解析缺陷的创建、解决和关闭时间，精确计算以下指标：
        - 每日新增缺陷数量
        - 每日修复缺陷数量
        - 每日关闭缺陷数量
        - 每日未关闭缺陷数量

        参数:
            data (Dict[str, Any]): 缺陷数据字典，必须包含以下字段：
                - created: 缺陷创建时间（必须字段）
                - resolved: 缺陷解决时间（可选字段）
                - closed: 缺陷关闭时间（可选字段）

        返回:
            None: 直接更新类属性dailyTrendOfBugChanges

        异常处理:
            KeyError: 当输入数据缺少created字段时抛出
            ValueError: 当日期格式转换失败时抛出

        实现策略:
            1. 基础数据校验与清洗
            2. 初始化用于在每个日期的统计数据
            3. 日期格式标准化处理
            4. 创建事件记录处理
            5. 解决事件记录处理
            6. 关闭事件记录处理
            7. 未关闭状态持续跟踪
        """
        # ==================================================================
        # 阶段1：基础数据校验
        # ==================================================================
        # 检查必要字段存在性，缺失created字段立即抛出异常
        if 'created' not in data:
            raise KeyError("缺陷数据必须包含created字段")

        # ==================================================================
        # 阶段2：初始化数据
        # ==================================================================
        # 初始化每个日期的计数器, 保证所有日期下面都存在完整的键值对
        base_count_data: dict = {
            '创建缺陷总数': 0,
            '修复缺陷总数': 0,
            '关闭缺陷总数': 0,
            '未关闭缺陷总数': 0,
        }

        # ==================================================================
        # 阶段3：日期标准化处理
        # ==================================================================
        # 转换创建时间为标准日期格式（YYYY-MM-DD）
        create_date = date_time_to_date(data['created'])

        # 处理解决时间（允许空值）
        resolve_date = date_time_to_date(data['resolved']) if data.get('resolved') else None

        # 处理关闭时间（允许空值）
        close_date = date_time_to_date(data['closed']) if data.get('closed') else None

        # ==================================================================
        # 阶段4：创建事件处理
        # ==================================================================
        # 忽略上线日期后创建的缺陷
        if create_date > self.lastTaskDate:
            return

        # 初始化或更新当日创建计数
        if create_date not in self.dailyTrendOfBugChanges:
            self.dailyTrendOfBugChanges[create_date] = base_count_data.copy()
        self.dailyTrendOfBugChanges[create_date]['创建缺陷总数'] += 1

        # ==================================================================
        # 阶段5：解决事件处理
        # ==================================================================
        # 仅处理有效且在项目周期内的解决日期
        if resolve_date and resolve_date <= self.lastTaskDate:
            if resolve_date not in self.dailyTrendOfBugChanges:
                self.dailyTrendOfBugChanges[resolve_date] = base_count_data.copy()
            self.dailyTrendOfBugChanges[resolve_date]['修复缺陷总数'] += 1

        # ==================================================================
        # 阶段6：关闭事件处理
        # ==================================================================
        # 当存在有效关闭日期时的处理逻辑
        if close_date and close_date <= self.lastTaskDate:
            # 更新关闭计数
            if close_date not in self.dailyTrendOfBugChanges:
                self.dailyTrendOfBugChanges[close_date] = base_count_data.copy()
            self.dailyTrendOfBugChanges[close_date]['关闭缺陷总数'] += 1

            # 计算未关闭持续时间段（创建日到关闭日前一天）
            unclosed_dates: list = get_days(create_date, close_date)[:-1]
            for date in unclosed_dates:
                if date not in self.dailyTrendOfBugChanges:
                    self.dailyTrendOfBugChanges[date] = base_count_data.copy()
                self.dailyTrendOfBugChanges[date]['未关闭缺陷总数'] += 1
        else:
            # ==================================================================
            # 阶段7：未关闭状态处理
            # ==================================================================
            # 计算从创建日到项目结束日的未关闭时间段
            unclosed_dates: list = get_days(create_date, self.lastTaskDate)
            for date in unclosed_dates:
                if date not in self.dailyTrendOfBugChanges:
                    self.dailyTrendOfBugChanges[date] = base_count_data.copy()
                self.dailyTrendOfBugChanges[date]['未关闭缺陷总数'] += 1

    def _print_error(self, error_text: str) -> None:
        """
        执行必要的清理操作后打印错误信息并退出程序

        本方法用于在发生严重错误时，在必要时恢复系统配置状态，
        最后强制终止程序运行，并输出错误信息。该方法确保在异常情况下能够优雅地退出，同时保留必要的错误上下文。

        参数:
            error_text (str): 需要显示的错误信息文本内容

        返回:
            None: 本方法执行后直接终止程序运行

        异常:
            无显式异常抛出，但会调用sys.exit(error_text)强制终止程序

        处理流程:
            1. 检查并恢复系统配置状态
            2. 强制终止程序运行，并输出错误信息

        关联方法:
            restore_list_config(): 用于恢复系统配置状态
        """
        # 检查是否需要恢复列表配置状态
        if not self.isInitialListConfig:
            # 调用配置恢复方法，确保系统状态一致性
            self.restore_list_config()

        # 强制终止程序运行，返回状态码1表示异常退出
        sys.exit(error_text)

    def _save_task_hours(self, data) -> None:
        """
        保存每个开发者每天的任务工时。

        该方法根据任务数据更新每个开发者每天的工时。如果任务开始和结束日期相同，则将完成的努力添加到该日期。
        如果开始和结束日期不同，则根据每个日期的剩余工时分配努力，直到完成的努力分配完毕。

        参数:
            data (dict): 包含任务信息的字典，结构示例：
                {
                    'developerName': '开发者名称',
                    'effort_completed': 实际完成工时,
                    'begin': 任务开始日期,
                    'due': 任务结束日期
                }

        返回:
            None: 直接更新类属性dailyWorkingHoursOfEachDeveloper

        异常处理:
            KeyError: 当输入数据缺少必要字段时抛出
            ValueError: 当日期格式转换失败时抛出

        实现流程:
            1. 提取开发者名称和实际完成工时
            2. 判断任务开始和结束日期是否相同
            3. 如果日期相同，直接累加工时
            4. 如果日期不同，按天分配工时
            5. 确保每日工时不超过8小时
        """
        # ==================================================================
        # 阶段1：提取开发者名称和实际完成工时
        # ==================================================================
        # 从输入数据中获取开发者名称
        developer_name = data['developerName']
        # 从输入数据中获取实际完成工时，并转换为浮点数
        effort_completed = float(data.get('effort_completed', 0))

        # ==================================================================
        # 阶段2：判断任务开始和结束日期是否相同
        # ==================================================================
        # 如果任务开始和结束日期相同，则直接将实际完成工时累加到该日期
        if data['begin'] == data['due']:
            self.dailyWorkingHoursOfEachDeveloper[developer_name][data['begin']] += effort_completed

        # ==================================================================
        # 阶段3：按天分配工时（开始和结束日期不同）
        # ==================================================================
        # 如果任务开始和结束日期不同，则按天分配实际完成工时
        elif data['begin'] < data['due']:
            # 获取开始和结束日期之间的所有日期
            for day in get_days(data['begin'], data['due']):
                # 获取该日期已保存的工时
                saved_task_hours = self.dailyWorkingHoursOfEachDeveloper[developer_name].get(day, 0)
                # 计算该日期的剩余工时（每日最多8小时）
                remaining_effort = 8 - saved_task_hours

                # ==================================================================
                # 阶段4：分配剩余工时
                # ==================================================================
                # 如果剩余工时大于0且实际完成工时大于剩余工时
                if effort_completed - remaining_effort > 0:
                    # 将该日期的工时加上剩余工时
                    self.dailyWorkingHoursOfEachDeveloper[developer_name][day] += remaining_effort
                    # 从实际完成工时中减去已分配的工时
                    effort_completed -= remaining_effort
                else:
                    # 如果剩余工时小于等于0，则将该日期的工时加上实际完成工时
                    self.dailyWorkingHoursOfEachDeveloper[developer_name][day] += effort_completed
                    # 结束循环，工时分配完毕
                    break

    def _processing_tester_list(self) -> None:
        """
        处理测试人员名单，分别把项目测试人员和测试接收人进行分别存储
        从测试报告接收人列表中移除当前用户，并确保测试负责人存在

        本方法通过以下步骤维护测试收件人列表的完整性：
        1. 格式化测试人员显示字符串
        2. 识别并移除当前认证用户
        3. 确保测试负责人在收件人列表中

        流程细节：
        - 统一处理部门前缀，生成易读的测试人员字符串
        - 动态获取当前登录用户信息进行精确匹配
        - 智能维护负责人配置，避免重复添加

        异常处理：
            KeyError: 当用户详情数据缺失关键字段时抛出
            AttributeError: 当用户详情结构异常时抛出

        关联方法：
            get_user_detail(): 获取当前用户详细信息
        """
        # ==================================================================
        # 阶段1：测试人员字符串格式化
        # ==================================================================
        # 当测试收件人列表存在时，构建去除部门前缀的测试人员显示字符串
        if self.testRecipient:
            # 使用生成器表达式遍历收件人列表，去除部门前缀并用顿号连接，用于展示在测试报告概要中的测试人员
            self.testersStr += '、'.join(
                tester.replace(DEPARTMENT, '')  # 移除部门前缀
                for tester in self.testRecipient  # 遍历原始收件人列表
            )

        # ==================================================================
        # 阶段2：当前用户处理
        # ==================================================================
        # 从用户详情中提取昵称字段（需包含中文名和部门信息）
        current_user_name = get_user_detail()['user_nick']  # 调用用户信息接口获取完整昵称

        # 安全移除当前用户（如果存在于收件人列表）
        if current_user_name in self.testRecipient:
            # 使用列表的remove方法进行精确匹配删除
            self.testRecipient.remove(current_user_name)

            # ==================================================================
        # 阶段3：测试负责人校验
        # ==================================================================
        # 检查测试负责人配置必要性
        if current_user_name != TESTER_LEADER:  # 当前用户非负责人时的处理
            if TESTER_LEADER not in self.testRecipient:  # 负责人不在列表时追加
                # 将带部门前缀的负责人标识加入列表末尾
                self.testRecipient.append(TESTER_LEADER)

    def _process_developer_task(
            self,
            developer: str,
            effort: float,
            begin: datetime.date,
            due: datetime.date,
            child_data: dict
    ) -> None:
        """
        处理开发者任务的核心业务逻辑

        主要功能：
        - 工时统计：累计开发者总工时
        - 时间范围跟踪：维护任务时间跨度信息
        - 任务关联：建立子任务与开发者的关联关系
        - 工时分布记录：生成每日工时分布数据

        参数:
            developer (str): 开发者姓名标识，用于工时统计和任务关联
            effort (float): 当前任务消耗的工时数，精度保留两位小数
            begin (datetime.date): 任务起始日期，用于时间范围计算
            due (datetime.date): 任务截止日期，用于时间有效性校验
            child_data (dict): 子任务原始数据字典，用于后续分析和持久化

        返回:
            None: 方法通过成员变量修改对象状态，无显式返回值

        异常:
            ValueError: 当传入无效日期参数时可能抛出
            KeyError: 当传入非字典类型的child_data时可能抛出
        """
        # ==================================================================
        # 阶段1：工时累计
        # ==================================================================

        # 累加当前任务工时到开发者总工时
        self.workHours[developer] += effort

        # ==================================================================
        # 阶段2：时间范围更新
        # ==================================================================
        # 仅在有效起始日期时更新时间范围
        # 调用内部方法更新任务时间跨度记录
        if begin is not None:
            self._update_date_range(begin=begin)

        # ==================================================================
        # 阶段3：子任务数据关联
        # ==================================================================
        # 创建数据副本避免修改原始数据
        # 深拷贝保证数据隔离性（假设child_data为简单字典结构）
        processed_data = child_data.copy()

        # 添加开发者姓名到处理后的数据
        processed_data['developerName'] = developer

        # ==================================================================
        # 阶段4：工时分布记录
        # ==================================================================
        # 有效性校验：起始日期早于等于截止日期
        if begin and due and begin <= due:
            # 调用内部方法持久化工时分布数据
            self._save_task_hours(processed_data)

        else:
            self._print_error(f"存在{developer}任务的预计开始时间和预计结束时间错误，begin={begin}，due={due}")

    def _process_tester_task(self, due_date: datetime.date, begin_date: datetime.date, owner: str) -> None:
        """
        处理测试任务的核心业务逻辑

        该方法实现测试任务数据的处理流程，主要功能包括：
        1. 测试任务存在性标记
        2. 项目关键时间节点管理
        3. 测试报告接收人列表维护

        参数:
            due_date (datetime.date):
                测试任务截止日期，用于更新项目时间跨度记录
                当值不为None时触发时间范围更新
            begin_date (datetime.date):
                测试任务起始日期，用于智能推算实际上线日期
                满足条件时将更新onlineDate属性
            owner (str):
                测试任务负责人标识，用于维护测试报告接收人列表
                自动进行去重处理

        返回:
            None: 通过修改实例属性实现状态更新

        异常:
            TypeError: 当日期参数类型不符合datetime.date时可能抛出
            ValueError: 当日期比较出现逻辑矛盾时可能抛出

        实现逻辑:
            1. 时间范围更新阶段：
               - 当due_date有效时，调用_update_date_range更新项目最晚任务日期
            2. 上线日期推算阶段：
               - 当begin_date有效且未手动输入上线日期时
               - 遵循"最后开始原则"：取最大的begin_date作为实际上线日期
            3. 收件人维护阶段：
               - 采用存在性检查确保负责人唯一性
               - 安全追加新负责人到testRecipient列表
        """
        # ==================================================================
        # 阶段1：时间范围更新
        # ==================================================================
        if due_date is not None:
            self._update_date_range(due=due_date)

        # ==================================================================
        # 阶段2：上线日期计算
        # ==================================================================
        if begin_date is not None and not self.isInputOnlineDate:
            if (self.onlineDate is None) or (begin_date > self.onlineDate):
                self.onlineDate = begin_date

        # ==================================================================
        # 阶段3：收件人列表维护
        # ==================================================================
        if owner not in self.testRecipient:
            self.testRecipient.append(owner)


    def _update_date_range(self, begin: datetime.date = None, due: datetime.date = None):
        """
        维护项目时间范围边界值

        核心功能：
        1. 动态更新项目生命周期的时间范围
        2. 维护最早任务开始日期记录
        3. 维护最晚任务结束日期记录
        4. 空值安全处理机制

        参数:
            begin (datetime.date, optional): 候选的最早任务日期，当该日期早于当前记录时更新
            due (datetime.date, optional): 候选的最晚任务日期，当该日期晚于当前记录时更新

        实现逻辑:
            1. 候选日期有效性检查
            2. 当前记录存在性验证
            3. 日期比较与边界值更新
            4. 空值安全处理机制保障数据完整性

        更新策略:
            - 最早日期采用最小值策略（取更早的日期）
            - 最晚日期采用最大值策略（取更晚的日期）
        """
        # ==================================================================
        # 阶段1：最早任务日期更新处理
        # ==================================================================
        if begin:
            # 检查当前记录是否存在或新日期是否更早
            # 条件1：尚未设置最早日期时直接赋值
            # 条件2：已存在记录时比较日期先后
            if not self.earliestTaskDate or begin < self.earliestTaskDate:
                # 更新实例属性记录项目最早开始时间点
                self.earliestTaskDate = begin  # type: datetime.date

        # ==================================================================
        # 阶段2：最晚任务日期更新处理
        # ==================================================================
        if due:
            # 检查当前记录是否存在或新日期是否更晚
            # 条件1：尚未设置最晚日期时直接赋值
            # 条件2：已存在记录时比较日期先后
            if not self.lastTaskDate or due > self.lastTaskDate:
                # 更新实例属性记录项目最晚结束时间点
                self.lastTaskDate = due  # type: datetime.date

    def _statistics_deploy_prod_day_unrepaired_bug(
            self,
            bug_status: str,
            bug_platform: str,
            bug_id: str,
            severity_name: str,
            resolved_date: str = None
    ) -> None:
        """
        统计上线生产环境当天仍未修复的缺陷，并按严重等级分类存储

        核心功能：
        1. 缺陷状态与解决时间双重校验
        2. 上线当天未修复状态判定
        3. 严重等级分类存储

        参数详解:
            bug_status (str):
                缺陷当前状态，取值范围参考TAPD状态机
                示例值：'closed'（已关闭）、'resolved'（已解决）
            bug_platform (str):
                缺陷所属平台标识，用于多平台上线日期匹配
                示例值：'IOS'、'Android'
            bug_id (str):
                缺陷唯一标识符，用于跟踪具体缺陷实例
            severity_name (str):
                缺陷严重等级名称，必须与BUG_LEVELS列表定义一致
                示例值：'致命'、'严重'、'一般'
            resolved_date (str, optional):
                缺陷解决日期，格式应为'YYYY-MM-DD'，当缺陷未解决时可为空

        异常处理:
            - 当severity_name不在预定义BUG_LEVELS列表时，会跳过分类逻辑
            - 日期格式异常会在调用栈上层处理
        """
        # ==================================================================
        # 阶段1：初始化状态标识
        # ==================================================================
        # 默认标记为上线当天未修复缺陷（后续校验可能修改此状态）
        is_deploy_prod_day_unrepaired_bug = True  # type: bool

        # ==================================================================
        # 阶段2：缺陷解决状态与时间校验
        # ==================================================================
        # 当缺陷已关闭且存在解决日期时，执行时间校验逻辑
        if bug_status == 'closed' and resolved_date:
            # 处理多平台上线日期场景
            if self.isInputOnlineDate:
                # 对比解决日期与对应平台上线日期
                if resolved_date < self.onlineDateDict[bug_platform]:
                    is_deploy_prod_day_unrepaired_bug = False
            # 处理单平台上线日期场景
            else:
                # 对比解决日期与全局上线日期
                if resolved_date < self.onlineDate:
                    is_deploy_prod_day_unrepaired_bug = False  # type: bool

        # ==================================================================
        # 阶段3：严重等级分类存储
        # ==================================================================
        # 处理致命(P0)和严重(P1)级别缺陷
        if is_deploy_prod_day_unrepaired_bug and severity_name in BUG_LEVELS[0:2]:
            # 将缺陷ID添加到P0P1分类列表
            # 数据结构维护：list[str] 类型追加操作
            self.unrepairedBugs['deployProdDayUnrepaired']['P0P1'].append(bug_id)

        # 处理一般(P2)及以下级别缺陷
        elif is_deploy_prod_day_unrepaired_bug and severity_name not in BUG_LEVELS[0:2]:
            # 将缺陷ID添加到P2分类列表
            # 数据结构维护：list[str] 类型追加操作
            self.unrepairedBugs['deployProdDayUnrepaired']['P2'].append(bug_id)


    def _statistics_on_that_day_unrepaired_bug(
            self,
            bug_status: str,
            bug_id: str,
            severity_name: str,
            created_date: str,
            resolved_date: str = None
    ) -> None:
        """
        统计缺陷创建当天未修复的缺陷，并按严重等级分类存储

        核心功能：
        1. 识别当天未及时修复的缺陷
        2. 根据缺陷严重等级进行三级分类（P0/P1/P2）
        3. 维护缺陷分类存储结构

        参数详解:
            bug_status (str): 缺陷当前状态，取值范围参考TAPD状态机
                              示例值：'closed'（已关闭）、'active'（激活中）
            bug_id (str): 缺陷唯一标识符，用于跟踪具体缺陷实例
            severity_name (str): 缺陷严重等级名称，必须与BUG_LEVELS列表定义一致
                                 示例值：'致命'、'严重'、'一般'
            created_date (str): 缺陷创建日期，格式应为'YYYY-MM-DD'
            resolved_date (str, optional): 缺陷解决日期，格式应为'YYYY-MM-DD'
                                           当缺陷未解决时可为空

        实现逻辑:
            1. 缺陷状态与解决时间双重校验
            2. 当天未修复状态判定
            3. 三级严重等级分类存储
        """
        # 初始化默认状态为当天未修复缺陷
        is_on_that_day_unrepaired_bug = True  # type: bool

        # ==================================================================
        # 阶段1：校验缺陷解决状态与时间
        # ==================================================================
        # 当缺陷已关闭且存在解决日期时，检查是否在创建当天已解决
        if bug_status == 'closed' and resolved_date:
            # 创建日期与解决日期相同则标记为已修复缺陷
            if created_date == resolved_date:
                is_on_that_day_unrepaired_bug = False  # type: bool

        # ==================================================================
        # 阶段2：按严重等级分类存储缺陷ID
        # ==================================================================
        # 处理致命(P0)级别缺陷
        if is_on_that_day_unrepaired_bug and severity_name == BUG_LEVELS[0]:
            # 将缺陷ID添加到P0分类列表
            self.unrepairedBugs['onThatDayUnrepaired']['P0'].append(bug_id)  # list[str] 类型维护

        # 处理严重(P1)级别缺陷
        elif is_on_that_day_unrepaired_bug and severity_name == BUG_LEVELS[1]:
            # 将缺陷ID添加到P1分类列表
            self.unrepairedBugs['onThatDayUnrepaired']['P1'].append(bug_id)  # list[str] 类型维护

        # 处理一般(P2)及以下级别缺陷
        elif is_on_that_day_unrepaired_bug and severity_name not in BUG_LEVELS[0:2]:
            # 将缺陷ID添加到P2分类列表
            self.unrepairedBugs['onThatDayUnrepaired']['P2'].append(bug_id)  # list[str] 类型维护

    def _check_bug_client(self, online_clients: List[str]) -> List[str]:
        """
        验证缺陷关联的客户端平台是否在已上线客户端列表中

        该方法实现以下核心功能：
        1. 遍历缺陷关联的所有客户端平台
        2. 校验各平台是否存在于已上线客户端清单
        3. 收集未上线或无效的客户端平台

        参数:
            online_clients (List[str]):
                已上线客户端标识列表，元素应为标准客户端标识符
                示例: ['IOS', 'Android', 'H5']

        返回:
            List[str]:
                包含所有未上线客户端平台的列表，按首次出现顺序排列
                示例: ['Flutter', 'Windows'] 表示存在缺陷关联了未上线的客户端

        异常处理:
            TypeError: 当输入参数不是列表类型时抛出
            ValueError: 当输入列表包含非字符串元素时抛出
        """
        # ==================================================================
        # 阶段1：输入参数校验
        # ==================================================================
        # 校验输入类型为列表（防御性编程）
        if not isinstance(online_clients, list):
            raise TypeError("online_clients参数必须为列表类型")

        # 校验列表元素类型（确保数据质量）
        for client in online_clients:
            if not isinstance(client, str):
                raise ValueError("online_clients列表元素必须为字符串类型")

        # ==================================================================
        # 阶段2：无效客户端平台检测
        # ==================================================================
        # 初始化无效客户端收集列表
        error_clients = []

        # 遍历缺陷关联的所有客户端平台
        for bug_platform in self.bugExistPlatforms:
            # 检查平台是否未上线且未被记录
            if (bug_platform not in online_clients
                and bug_platform not in error_clients):
                # 记录无效客户端平台（保留首次出现顺序）
                error_clients.append(bug_platform)

        # ==================================================================
        # 阶段3：返回检测结果
        # ==================================================================
        return error_clients


    def _add_multi_dimensional_table_html(self, table_data: dict) -> None:
        """
        生成多维数据表格的HTML结构，支持动态列头和行统计功能

        该方法通过解析多维字典数据，自动构建包含列头、数据行和总计行的复杂HTML表格。
        特别适用于展示多维度交叉统计结果，支持自动计算行总计和列总计。

        参数:
            table_data (dict): 包含表格配置和数据的字典，结构示例：
                {
                    'tableWidth': 1000,       # 表格总宽度(像素)
                    'data': {                 # 核心数据字典
                        '平台A': {'类型1': 5, '类型2': 3},
                        '平台B': {'类型1': 2, '类型2': 7}
                    },
                    'firstColumnHeader': '软件平台',  # 首列标题文本
                    'isRowTotal': True        # 是否显示行总计列
                }

        返回:
            None: 直接更新实例的chartHtml属性

        实现流程:
            1. 提取数据列头信息
            2. 定义表格样式体系
            3. 构建表格数据行HTML
            4. 计算并生成总计行数据
            5. 组合完整表格HTML结构
        """
        # ==================================================================
        # 阶段1：数据列头提取
        # ==================================================================
        # 从首行数据值中提取列头信息（动态适应数据结构）
        data_headers = []
        for value_data in table_data['data'].values():
            data_headers = list(value_data.keys())  # 提取内部字典的键作为列头
            break  # 仅需获取第一个元素的键集合

        # ==================================================================
        # 阶段2：表格样式体系定义
        # ==================================================================
        # 通用单元格样式配置（基础边框和间距设置）
        common_style = {
            'padding': '0 10px',
            'vertical-align': 'middle',
            'border-right': 'none',
            'border-left': 'none',
            'border-top': 'none',
            'border-bottom': '1px solid rgb(230, 230, 230)',
            'background-color': 'rgb(255, 255, 255)',
        }

        # 表头行特定样式（增加顶部边框和文字颜色）
        header_row_style = style_convert({
            **common_style,
            'height': '50px',
            'font-size': '12px',
            'color': '#8c95a8',
            'border-top': '1px solid rgb(230, 230, 230)',
        })

        # 数据行通用样式（标准行高和字体）
        row_style = style_convert({
            **common_style,
            'height': '38px',
            'font-size': '12px',
        })

        # 总计行强调样式（加粗字体和深色文字）
        total_row_style = style_convert({
            **common_style,
            'height': '38px',
            'font-size': '12px',
            'color': 'black',
            'font-weight': 'bold',
        })

        # ==================================================================
        # 阶段3：数据行HTML生成
        # ==================================================================
        data_row_html = ''  # 初始化数据行HTML容器
        total_row_values = [0] * (len(data_headers) + 1)  # 初始化总计行数值容器[行小计, 列1, 列2...]

        # 遍历每个主分类的数据条目（如不同平台的数据）
        for table_key, table_data_dict in table_data['data'].items():
            # 构建单行数据单元格
            row_cells = []
            current_row_total = 0  # 当前行小计

            # 遍历每个子分类的数据值（如不同缺陷类型）
            for header in data_headers:
                cell_value = table_data_dict.get(header, 0)
                row_cells.append(f'<td align="left" style="{row_style}">{cell_value}</td>')
                current_row_total += cell_value

            # 添加行小计单元格（根据配置决定是否显示）
            if table_data.get('isRowTotal'):
                row_cells.insert(0, f'<td align="left" style="{row_style}">{current_row_total}</td>')

            # 累积到总计行数值
            total_row_values[0] += current_row_total  # 行小计累计
            for idx, val in enumerate(table_data_dict.values()):
                total_row_values[idx + 1] += val  # 各列数值累计

            # 组装完整数据行HTML
            data_row_html += f'''
            <tr>
                <td align="left" style="{row_style}">{table_key}</td>
                {''.join(row_cells)}
            </tr>'''

        # ==================================================================
        # 阶段4：表头与总计行构建
        # ==================================================================
        # 生成动态列头HTML
        header_cells = []
        if table_data.get('isRowTotal'):
            header_cells.append(f'<th align="left" style="{header_row_style}">小计</th>')
        header_cells.extend(
            f'<th align="left" style="{header_row_style}">{header}</th>'
            for header in data_headers
        )

        # 生成总计行HTML
        total_cells = []
        if table_data.get('isRowTotal'):
            total_cells.append(f'<td align="left" style="{total_row_style}">{total_row_values[0]}</td>')
        total_cells.extend(
            f'<td align="left" style="{total_row_style}">{val}</td>'
            for val in total_row_values[1:]
        )

        # ==================================================================
        # 阶段5：完整表格组装
        # ==================================================================
        self.chartHtml += f'''
        {'<div><br /></div>' * 2}
        <div>
            <table cellpadding="0" cellspacing="0" class="report-chart__table" 
                   style="width:{table_data['tableWidth']}px;border:none;margin:0;">
                <tbody>
                    <tr>
                        <th align="left" style="{header_row_style}">
                            {table_data['firstColumnHeader']}
                        </th>
                        {''.join(header_cells)}
                    </tr>
                    {data_row_html}
                    <tr>
                        <td align="left" style="{total_row_style}">总计</td>
                        {''.join(total_cells)}
                    </tr>
                </tbody>
            </table>
        </div>'''

    def _add_simple_table_html(self, table_data: dict):  # 暂不进行优化
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

    def _calculate_positive_integrity_score(self) -> None:
        """
        计算配合积极性与文档完整性综合评分

        通过交互式输入获取综合评分，评分标准合并文档质量和配合态度表现。
        用户需根据实际项目情况，直接参照以下标准给出评分：

        评分标准：
        20分 - 项目期间积极配合测试主动跟进问题并解决。提测文档清晰完善（技术、接口）等。
                会给测试提供测试范围、注意事项、脚本、或其他有意义的建议。对测试执行起到重要帮助
        15分 - 项目期间积极配合测试主动跟进问题并解决。提测文档清晰完善（技术、接口）等
        10分 - 项目期间能够基本配合测试进行相关项目推进，能够跟进问题并按期解决，文档部分缺失、未及时更新
        5分  - 项目期间态度懈怠、散漫、不配合测试解决问题。但文档全面、及时更新
        1分  - 项目期间态度懈怠、散漫、不配合测试解决问题、文档缺失、不更新、有错误等。

        参数: 无，通过标准输入流获取数据
        返回: None，直接更新score['positiveIntegrityScore']
        """
        try:
            # ==================================================================
            # 阶段1：构建简洁评分说明
            # ==================================================================
            # 打印标题，用于清晰地标识出这部分评分的开始
            print('配合积极性/文档完成性'.center(LINE_LENGTH, '-'))

            # 定义评分标准文本，详细解释了每个分数段代表的项目团队行为和文档完成情况
            score_text = ("20分：项目期间积极配合测试主动跟进问题并解决。提测文档清晰完善（技术、接口）等。会给测试提供测试范围、注意事项、脚本、或其他有意义的建议。对测试执行起到重要帮助\n"
                          "15分：项目期间积极配合测试主动跟进问题并解决。提测文档清晰完善（技术、接口）等\n"
                          "10分：项目期间能够基本配合测试进行相关项目推进，能够跟进问题并按期解决，文档部分缺失、未及时更新\n"
                          "5分：项目期间态度懈怠、散漫、不配合测试解决问题。但文档全面、及时更新\n"
                          "1分：项目期间态度懈怠、散漫、不配合测试解决问题、文档缺失、不更新、有错误等。\n")

            # ==================================================================
            # 阶段2：获取综合评分输入
            # ==================================================================
            final_score = _input(
                text=score_text + '请输入分数：',
                **SCORE_INPUT_DATA
            )

            # ==================================================================
            # 阶段3：存储结果并生成报告
            # ==================================================================
            self.score['positiveIntegrityScore'] = final_score
            self.scoreContents.append({
                'title': '配合积极性/文档完成性',
                'scoreRule': score_text,
                'score': self.score['positiveIntegrityScore']
            })

        except ValueError as ve:
            raise ValueError(f"评分输入异常: {str(ve)}") from ve
        except Exception as e:
            raise RuntimeError("综合评分计算失败") from e

    def _calculate_smoke_testing_score(self) -> None:
        """
        计算研发冒烟测试综合评分

        通过交互式输入获取综合评分，评分标准冒烟测试。
        用户需根据实际项目情况，直接参照以下标准给出评分：

        评分标准：
        20分 - 考核期内所有版本有冒烟自测并一次通过
        15分 - 考核期版本有冒烟自测但部分用例不通过
        10分 - 考核期内提测版本没有进行冒烟自测，主流程通过
        5分  - 考核期内有进行冒烟自测，主流程不通过
        1分  - 考核期内提测版本没有进行冒烟自测，主流程不通过

        参数: 无，通过标准输入流获取数据
        返回: None，直接更新score['smokeTestingScore']
        """
        try:
            # ==================================================================
            # 阶段1：构建简洁评分说明
            # ==================================================================
            # 打印标题，用于清晰地标识出这部分评分的开始
            print('冒烟测试'.center(LINE_LENGTH, '-'))

            # 定义评分标准文本，详细解释了每个分数段代表的项目团队行为和文档完成情况
            score_text = ("20分：考核期内所有版本有冒烟自测并一次通过\n"
                          "15分：考核期版本有冒烟自测但部分用例不通过\n"
                          "10分：考核期内提测版本没有进行冒烟自测，主流程通过\n"
                          "5分：考核期内有进行冒烟自测，主流程不通过\n"
                          "1分：考核期内提测版本没有进行冒烟自测，主流程不通过\n")

            # ==================================================================
            # 阶段2：获取综合评分输入
            # ==================================================================
            final_score = _input(
                text=score_text + '请输入分数：',
                **SCORE_INPUT_DATA
            )

            # ==================================================================
            # 阶段3：存储结果并生成报告
            # ==================================================================
            self.score['smokeTestingScore'] = final_score
            self.scoreContents.append({
                'title': '冒烟测试',
                'scoreRule': score_text,
                'score': self.score['smokeTestingScore']
            })

        except ValueError as ve:
            raise ValueError(f"评分输入异常: {str(ve)}") from ve
        except Exception as e:
            raise RuntimeError("综合评分计算失败") from e

    def _calculate_bug_count_score(self) -> None:
        """
        计算软件质量评分中的BUG数量评分项

        本方法实现完整的BUG数量评分流程，包含以下关键步骤：
        1. 获取BUG总数和开发周期数据（优先使用实例数据，支持用户输入）
        2. 计算开发团队的平均人时工作量
        3. 根据BUG密度计算基准评分
        4. 根据缺陷严重级别调整最终评分
        5. 构建评分结果数据结构并记录日志

        流程细节：
        - 采用交互式输入机制保障数据完整性
        - 集成业务规则：致命/严重缺陷对评分的限制作用
        - 自动生成详细的评分依据说明

        返回:
            None: 结果直接存储在实例的score字典和scoreContents列表中

        异常处理:
            - 除零错误防御：在计算UU值时自动处理零值情况
            - 类型转换异常：通过_input函数的内置校验机制处理
        """
        # ==================================================================
        # 阶段1：初始化与数据准备
        # ==================================================================

        # 打印章节标题并进行格式化分隔
        # 使用中心对齐方式显示"BUG数"标题，两侧填充横线字符至指定长度
        print('BUG数'.center(LINE_LENGTH, '-'))

        # ==================================================================
        # 阶段2：输入数据获取与校验
        # ==================================================================

        # BUG总数获取逻辑：
        # 优先使用实例中已存在的bugTotal值，若为空则通过_input函数交互获取
        # self.bugTotal可能来源于API获取或先前计算的结果
        bug_total = self.bugTotal
        if bug_total:
            # 使用绿色字体突出显示已存在的BUG总数
            print(f"获取的BUG总数为：{_print_text_font(bug_total, color='green')}")
        else:
            # 通过_input函数获取用户输入，强制转换为整数类型
            # 输入值将同时更新实例的bugInputTotal属性
            bug_total = _input("请输入BUG总数为：", int)
            self.bugInputTotal = bug_total

        # 开发周期获取逻辑：
        # 优先使用实例中的developmentCycle值，若为空则通过_input获取
        # 开发周期单位为自然日，保留一位小数精度
        if self.developmentCycle:
            # 显示已存在的开发周期值，进行四舍五入处理
            print(f"获取的开发周期总天数为：{_print_text_font(round(self.developmentCycle, 1), color='green')}")
        else:
            # 通过_input函数获取浮点数类型的开发周期
            self.developmentCycle = _input("请输入开发周期总天数：", float)

        # ==================================================================
        # 阶段3：核心指标计算
        # ==================================================================

        # 计算平均人时指标：
        # devTotalHours表示开发总工时，developerCount为开发人数
        # 公式：人均工时 = 总工时 / 人数
        avg_person_hours = self.devTotalHours / self.developerCount

        # 计算日均工时：
        # 将人均工时按开发周期平均分配，得到每日工作量
        daily_avg_hours = avg_person_hours / self.developmentCycle

        # 计算UU指标（Unit of Work）：
        # 反映团队每日总工作量，用于BUG密度计算
        # 公式：UU = 开发人数 × 日均工时
        uu_result = self.developerCount * daily_avg_hours

        # 计算BUG密度：
        # 防御除零错误，当UU值为零时返回无穷大
        # 结果保留一位小数，用于后续评分计算
        avg_bug_count = round(
            bug_total / uu_result if uu_result != 0 else float('inf'),
            1
        )

        # ==================================================================
        # 阶段4：评分计算与业务规则应用
        # ==================================================================

        # 输出计算过程关键指标
        print(
            f"获取的开发人员总数为：{_print_text_font(self.developerCount, color='green')}\n"
            f"开发人员总数乘以平均工时为 {_print_text_font(f'{uu_result:.2f}', color='green')}\n"
            f"该项目平均一天工作量的Bug数为 {_print_text_font(avg_bug_count, color='green')}"
        )

        # 调用评分函数获取基准分数
        # calculate_bug_count_rating实现BUG密度到评分的映射规则
        self.score['bugCountScore'] = calculate_bug_count_rating(avg_bug_count)

        # 应用严重缺陷调整规则：
        # 当存在致命缺陷时，评分上限为10分
        # 当存在严重缺陷时，评分上限为15分
        if self.bugLevelsCount:
            if self.bugLevelsCount['致命'] > 0:
                self.score['bugCountScore'] = min(self.score['bugCountScore'], 10)
            elif self.bugLevelsCount['严重'] > 0:
                self.score['bugCountScore'] = min(self.score['bugCountScore'], 15)

        # ==================================================================
        # 阶段5：结果输出与持久化
        # ==================================================================

        # 打印最终得分并更新实例数据
        print('-' * LINE_LENGTH)
        bug_count_score = f'{self.score["bugCountScore"]} 分'
        print(
            f'当平均一天工作量的Bug数={_print_text_font(avg_bug_count, color="green")}时，'
            f'当前该项目软件质量评分中“BUG数”一项得分为：{_print_text_font(bug_count_score)}'
        )

        # 构建评分依据说明文档
        self.bugCountScoreMsg = (
            f'BUG总数为：{bug_total}\n'
            f'开发周期总天数为：{self.developmentCycle}\n'
            f'开发人员总数乘以平均工时为 {uu_result:.2f}\n'
            f'该项目平均一天工作量的Bug数为 {avg_bug_count}\n'
        )

        # 将评分详情存入scoreContents列表
        # 包含评分规则说明和实际得分
        self.scoreContents.append({
            'title': 'BUG数',  # 评分项名称
            'scoreRule': self.bugCountScoreMsg + (  # 评分规则说明
                "20分：0<=平均一天工作的Bug数<=1且无严重、致命BUG\n"
                "15分：1<平均一天工作量的Bug数<=1.5且无致命Bug\n"
                "10分：1.5<平均一天工作量的Bug数<=2.0\n"
                "5分：2.0<平均一天工作量的Bug数<=3.0\n"
                "1分：3.0<平均一天工作量的Bug数\n"
            ),
            'score': self.score['bugCountScore']  # 实际得分
        })

    def _calculate_bug_repair_score(self) -> None:
        """
        计算缺陷修复质量评分并构建评分报告

        该方法通过分析不同严重级别缺陷的修复情况，结合预定义的评分规则，
        生成可视化质量评分报告。核心功能包含：
        1. 初始化评分规则模板
        2. 缺陷存在性校验与状态分类
        3. 多维度缺陷数据可视化展示
        4. 交互式评分输入与自动计算
        5. 结构化评分结果存储

        参数: 无
        返回: 无

        异常处理:
            - 当输入评分值非法时触发_input函数的验证机制
            - 缺陷数据为空时自动分配满分
        """

        # ==================================================================
        # 阶段1：评分规则模板初始化
        # ==================================================================
        # 构建评分标准说明文本，包含各级缺陷定义和评分规则
        score_text = (
            r"P0=致命缺陷, P1=严重缺陷, P2=一般缺陷、提示、建议" "\n"
            r"20分：名下BUG当天修复，当天通过回归验证且无重开" "\n"
            r"15分：名下BUG（P0\P1）当天修复，P2\其他隔天修复，所以BUG均不能重开" "\n"
            r"10分：名下BUG（P0）当天修复，（P1\P2）当天未修复，隔天修复" "\n"
            r"5分：名下BUG（P2）上线当天存在未修复" "\n"
            r"1分：名下BUG（P0\P1）上线当天存在未修复" "\n"
        )

        # ==================================================================
        # 阶段2：缺陷修复报告标题输出
        # ==================================================================
        # 生成居中显示的标题分隔线，增强可视化结构
        print('BUG修复'.center(LINE_LENGTH, '-'))

        # ==================================================================
        # 阶段3：缺陷存在性校验与处理分支
        # ==================================================================
        # 当总缺陷数为零时的处理逻辑
        if not self.bugTotal:
            # 子分支3.1：存在输入缺陷但已全部解决
            if self.bugInputTotal > 0:
                # 展示评分标准并获取用户输入，应用输入验证规则
                self.score['bugRepairScore'] = _input(
                    score_text + '请输入分数：',
                    **SCORE_INPUT_DATA
                )
            # 子分支3.2：无任何缺陷记录
            else:
                # 直接赋予最高评分并输出结果
                print(f'BUG修复评分为：{_print_text_font(20)}')
                self.score['bugRepairScore'] = 20
        # 存在缺陷时的处理流程
        else:
            # ==================================================================
            # 阶段4：多维缺陷数据可视化构建
            # ==================================================================
            # 组装各严重级别未修复缺陷的统计信息
            self.bugRepairScoreMsg += (
                'P0=致命缺陷, P1=严重缺陷, P2=一般缺陷、提示、建议\n'
                # 上线日未修复的高危缺陷统计
                f'在项目上线当天存在P0或者P1未修复BUG数为：{_print_text_font(len(self.unrepairedBugs["deployProdDayUnrepaired"]["P0P1"]), color="green")}\n'
                # 上线日未修复的中等缺陷统计
                f'在项目上线当天存在P2未修复BUG数为：{_print_text_font(len(self.unrepairedBugs["deployProdDayUnrepaired"]["P2"]), color="green")}\n'
                # 创建日未修复的致命缺陷统计
                f'P0当天未修复的BUG数为：{_print_text_font(len(self.unrepairedBugs["onThatDayUnrepaired"]["P0"]), color="green")}\n'
                # 创建日未修复的严重缺陷统计
                f'P1当天未修复的BUG数为：{_print_text_font(len(self.unrepairedBugs["onThatDayUnrepaired"]["P1"]), color="green")}\n'
                # 创建日未修复的一般缺陷统计
                f'P2当天未修复的BUG数为：{_print_text_font(len(self.unrepairedBugs["onThatDayUnrepaired"]["P2"]), color="green")}'
            )

            # ==================================================================
            # 阶段5：交互界面渲染与数据展示
            # ==================================================================
            # 输出格式化后的统计信息
            print(self.bugRepairScoreMsg)
            # 添加视觉分隔线
            print('-' * LINE_LENGTH)

            # ==================================================================
            # 阶段6：自动评分计算逻辑
            # ==================================================================
            # 合并统计数据和评分标准用于后续展示
            score_text = self.bugRepairScoreMsg + '\n' + score_text
            # 调用评分算法计算最终得分
            self.score['bugRepairScore'] = calculate_bug_repair_rating(self.unrepairedBugs)

            # ==================================================================
            # 阶段7：评分结果可视化输出
            # ==================================================================
            # 当评分有效时的处理流程
            if self.score['bugRepairScore'] is not None:
                # 构建带颜色标记的得分展示文本
                bug_repair_score = f'{self.score["bugRepairScore"]} 分'
                # 输出格式化评分结果
                print(
                    f'根据以上BUG修复情况，当前该项目软件质量评分中“BUG修复”一项得分为： {_print_text_font(bug_repair_score)}')

        # ==================================================================
        # 阶段8：结构化数据存储
        # ==================================================================
        # 将评分结果按标准格式存入报告数据结构
        self.scoreContents.append({
            'title': 'BUG修复',  # 评分项名称
            'scoreRule': score_text,  # 使用的评分规则文本
            'score': self.score['bugRepairScore']  # 最终得分值
        })

    def _calculate_bug_reopen_score(self):
        """
        计算缺陷重新打开次数的质量评分并记录评分结果

        本方法实现完整的缺陷重启评分流程，包含以下关键步骤：
        1. 初始化评分规则说明文本
        2. 处理无缺陷数据的特殊情况
        3. 获取缺陷重启详细数据
        4. 计算重启和未修复缺陷数量
        5. 生成可视化评分结果
        6. 存储评分结果到数据结构

        参数:
            无显式参数，通过实例属性访问相关数据：
            - self.bugTotal: 当前版本缺陷总数
            - self.bugInputTotal: 用户输入的缺陷总数
            - self.reopenBugsData: 缺陷重启统计数据字典
            - self.unrepairedBugsData: 未修复缺陷统计数据字典

        返回:
            None: 结果直接存储在实例属性self.score和self.scoreContents中

        异常处理:
            - 当输入分数不符合规范时由_input函数处理
            - 当缺陷统计数据异常时由calculate_bug_reopen_rating函数处理
        """
        # ==================================================================
        # 阶段1：初始化评分规则文本
        # ==================================================================
        # 定义评分规则的多行说明文本，包含各分数段对应的条件
        score_text = (
            '20分：当前版本名下所有BUG一次性回归验证通过无重启\n'
            '15分：名下BUG重启数=1\n'
            '10分：名下BUG重启数=2\n'
            '5分：名下BUG重启数=3\n'
            '1分：名下BUG重启数>=4\n'
        )

        # 打印带装饰线的标题，居中显示"BUG重启"文本
        print('BUG重启'.center(LINE_LENGTH, '-'))

        # ==================================================================
        # 阶段2：处理无缺陷数据情况
        # ==================================================================
        if not self.bugTotal:
            # 当实际缺陷数为0但用户输入缺陷数存在时，要求手动输入分数
            if self.bugInputTotal > 0:
                self.score['bugReopenScore'] = _input(
                    score_text + '请输入分数：',  # 拼接规则说明和输入提示
                    **SCORE_INPUT_DATA  # 传入预定义的输入验证参数
                )
            else:
                # 完全无缺陷时自动赋予最高分
                print(f'BUG重启评分为：{_print_text_font(20)}')
                self.score['bugReopenScore'] = 20

        # ==================================================================
        # 阶段3：处理存在缺陷数据情况
        # ==================================================================
        else:
            # 获取缺陷重启的详细数据，填充self.reopenBugsData
            self.get_reopen_bug_detail()

            # 计算总重启缺陷数（字典值求和）
            reopen_bug_count = sum(self.reopenBugsData.values())

            # 计算总未修复缺陷数（字典值求和）
            unrepaired_bug_count = sum(self.unrepairedBugsData.values())

            # ==================================================================
            # 阶段4：构建可视化结果信息
            # ==================================================================
            # 使用带颜色的文本格式化统计结果
            self.bugReopenScoreMsg += (
                f'BUG重启数为：{_print_text_font(reopen_bug_count, color="green")}\n'
                f'BUG未修复数为：{_print_text_font(unrepaired_bug_count, color="green")}'
            )

            # 输出统计信息到控制台
            print(self.bugReopenScoreMsg)

            # ==================================================================
            # 阶段5：计算最终评分
            # ==================================================================
            # 调用评分计算函数，传入总异常缺陷数（重启+未修复）
            self.score["bugReopenScore"] = calculate_bug_reopen_rating(
                reopen_bug_count + unrepaired_bug_count
            )

            # 打印分隔线
            print('-' * LINE_LENGTH)

            # 格式化评分结果文本
            bug_reopen_score = f"{self.score['bugReopenScore']} 分"

            # 生成带颜色标注的最终评分说明
            print(
                f'当名下BUG重启数和未修复数总计={_print_text_font(reopen_bug_count + unrepaired_bug_count, color="green")}时，'
                f'当前该项目软件质量评分中“BUG重启”一项得分为： {_print_text_font(bug_reopen_score)}'
            )

            # 合并统计信息和评分规则
            score_text = self.bugReopenScoreMsg + '\n' + score_text

        # ==================================================================
        # 阶段6：存储评分结果
        # ==================================================================
        # 将评分细节存入结果列表，包含：
        # - 评分项标题
        # - 评分规则说明
        # - 实际得分
        self.scoreContents.append({
            'title': 'BUG重启',
            'scoreRule': score_text,
            'score': self.score['bugReopenScore']
        })

    def _ai_generate_summary(self) -> None:
        """
        生成测试质量报告的综合分析摘要

        本方法实现测试质量报告的智能生成流程，包含以下核心功能：
        1. 多维度数据集成：聚合需求基础信息、缺陷分布、评分数据等关键指标
        2. 结构化提示工程：构建符合大语言模型处理的提示模板
        3. AI内容生成：调用深度学习模型生成专业分析报告
        4. 交互式优化机制：支持人工复核与内容再生

        参数:
            无显式参数，通过实例属性获取分析数据：
            - self.requirementName: 需求名称
            - self.developmentCycle: 开发周期（天）
            - self.developerCount: 开发人员数量
            - self.bugTotal: 实际发现的BUG总数
            - self.bugInputTotal: 输入的BUG总数
            - self.bugLevelsCount: BUG等级分布数据
            - self.scoreContents: 评分项详细信息列表
            - self.workHours: 工时统计数据
            - self.fixers: 缺陷修复人员数据
            - self.bugLevelsMultiClientCount: 多客户端缺陷等级分布
            - self.bugSourceMultiClientCount: 多客户端缺陷来源分布
            - self.score: 评分字典

        返回:
            None: 结果直接写入self.reportSummary属性

        异常:
            APIError: 当AI服务调用失败时抛出
            ValueError: 输入数据格式异常时抛出

        实现流程:
            1. 基础信息整合与校验
            2. 缺陷数据动态装配
            3. 评分规则与结果解析
            4. 多维数据关联分析
            5. 提示模板工程构建
            6. AI服务交互控制
            7. 输出内容质量保障
        """
        # ==================================================================
        # 阶段1：基础信息装配
        # ==================================================================

        # 初始化提示文本框架，包含指令头和基础需求信息
        text_parts = [
            '请仔细的阅读我说的话, 尤其是重点和注意\n',
            f"需求名称:{self.requirementName};",
            f"开发周期总天数为:{round(self.developmentCycle, 1)};",
            f"开发人员数量为:{self.developerCount};"
        ]

        # ==================================================================
        # 阶段2：缺陷数据动态处理
        # ==================================================================

        # 处理BUG总数展示逻辑（区分实际统计与输入数据）
        if self.bugTotal is not None:
            bug_count_info = f"BUG总数为: {self.bugTotal};"
        else:
            status_suffix = '(未发现BUG)' if self.bugInputTotal == 0 else ''
            bug_count_info = f"BUG总数为: {self.bugInputTotal}{status_suffix};"
        text_parts.append(bug_count_info)

        # 装配BUG等级分布数据（当存在有效数据时）
        if self.bugLevelsCount:
            text_parts.append(f"BUG等级分布情况为:{self.bugLevelsCount};")

        # ==================================================================
        # 阶段3：评分数据分析
        # ==================================================================

        if self.scoreContents:
            # 构建评分分析章节框架
            score_section = [
                '\n项目研发评分情况:',
                *[f"\n{item['title']}评分:\n{item['scoreRule']}\n得分为:{item['score']}"
                  for item in self.scoreContents],
                '\n注意:\n'
                'BUG修复评分(10-20分)表示不存在上线当天未修复BUG，但存在创建当天未修复BUG;\n'
                'BUG修复评分(1-5分)表示存在上线当天未修复BUG;\n'
                '(P0当天未修复BUG数、P1当天未修复BUG数、P2当天未修复BUG数)归属"创建当天未修复BUG数"\n'
                '(上线当天P0/P1未修复数、上线当天P2未修复数)归属"上线当天未修复BUG数"\n'
                '示例说明:\n'
                '上线当天P0/P1未修复数：0\n'
                '上线当天P2未修复数：1\n'
                '创建当天P0未修复数：0\n'
                '创建当天P1未修复数：6\n'
                '创建当天P2未修复数：20\n'
                '表示：上线当天无P0/P1BUG未修复，存在1个P2BUG上线当天未修复BUG；创建创建当天未修复BUG有6个P1BUG和20个P2BUG\n'
            ]
            text_parts.extend(score_section)

        # ==================================================================
        # 阶段4：多维数据关联
        # ==================================================================

        # 当存在工时、修复数据等多维指标时进行深度关联
        if all([
            self.workHours,
            self.fixers,
            self.bugLevelsMultiClientCount,
            self.bugSourceMultiClientCount
        ]):
            multidimensional_data = (
                f"开发人员工时(小时): {self.workHours},"
                f"开发人员修复情况(BUG数): {self.fixers},"
                f"各端缺陷等级分布: {self.bugLevelsMultiClientCount},"
                f"各端缺陷来源分布: {self.bugSourceMultiClientCount},"
                f"总分:{sum(self.score.values())};"
            )
            text_parts.append(multidimensional_data)

        # ==================================================================
        # 阶段5：提示工程构建
        # ==================================================================

        # 定义报告生成规范与格式要求
        formatting_rules = [
            '重点:作为测试经理需要生成提测质量分析报告，要求：',
            '- 详细总结开发测试情况',
            '- 指出不足与改进建议',
            '- 格式美观、表述清晰',
            '- 关键指标突出显示（如BUG总数、重启占比）',
            '- 使用<red>标签标注重点内容'
        ]
        text_parts.extend(formatting_rules)

        # 装配报告结构要求（当有预定义结构时）
        if TEST_REPORT_SUMMARY_COMPOSITION:
            structure_info = '组成部分: ' + '、'.join(TEST_REPORT_SUMMARY_COMPOSITION)
            text_parts.append(structure_info)

        # 添加输出模板参考
        template_reference = f'\n输出模板参考(不要画表格):{ai_output_template()}'
        text_parts.append(template_reference)

        # ==================================================================
        # 阶段6：AI服务交互控制
        # ==================================================================

        # 构建完整提示文本
        full_prompt = ''.join(text_parts)

        # 内容生成主循环
        while True:
            try:
                # 调用AI服务生成报告内容
                self.reportSummary = deepseek_chat(full_prompt)

                # 当启用重试机制时进行交互确认
                if IS_SUPPORT_RETRY_CREATE_AI_SUMMARY:
                    print('\n' * 2)  # 输出视觉分隔

                    # 用户确认循环
                    while (confirm := input('是否重新生成AI总结?(y/n): ').lower()) not in {'y', 'n'}:
                        print('输入错误, 请使用 y/n 确认: ')

                    if confirm == 'y':
                        continue  # 重新生成
                    else:
                        break  # 退出循环
                else:
                    break  # 无重试需求直接退出

            except (APIError, ConnectionError) as e:
                # 处理服务不可用类异常
                error_msg = f"AI服务调用失败: {str(e)}"
                raise RuntimeError(error_msg) from e

    def run(self):
        """
        执行软件质量评估主流程控制方法

        该方法统筹协调评估流程的各个关键环节，通过模块化调用实现完整的质量评估工作流。
        包含配置管理、数据采集、计算分析、结果输出等阶段，确保各环节数据衔接与异常处理。

        实现流程:
            1. 需求元数据获取与校验
            2. 系统配置管理与数据采集
            3. 用户交互式参数收集
            4. 开发资源与周期分析
            5. 缺陷数据采集与统计
            6. 系统配置还原与清理
            7. 质量指标计算与评分
            8. 数据可视化生成
            9. 测试报告生成与提交

        异常处理:
            - 关键数据缺失时抛出ValueError并中断流程
            - 网络请求失败时进行重试并抛出可追溯异常
            - 最终确保系统配置状态还原

        关联方法:
            - edit_list_config(): 列表视图配置管理
            - get_requirement_detail(): 需求详情获取
            - requirement_task_statistics(): 工时数据分析
            - bug_list_detail(): 缺陷数据统计
            - score_result(): 质量评分计算
            - create_chart(): 可视化图表生成
            - add_test_report(): 测试报告生成
        """
        try:
            # ==================================================================
            # 阶段1：需求元数据获取与校验
            # ==================================================================
            # 通过TAPD API获取需求基础信息，包含：
            # - 需求名称
            # - 关联开发团队
            # 执行数据有效性检查，缺失关键信息时中断流程
            self.get_requirement_detail()

            # ==================================================================
            # 阶段2：系统配置管理与数据采集
            # ==================================================================
            # 配置系统视图字段用于完整数据采集：
            # 1. 临时修改需求列表字段配置
            # 2. 调整缺陷列表展示字段
            # 3. 获取完整数据后还原配置
            # 4. 校验数据有效性
            self.get_all_list_data()

            # ==================================================================
            # 阶段3：用户交互式参数收集
            # ==================================================================
            # 执行用户提问阶段收集必要参数：
            # 1. 确认需求基本信息
            # 2. 收集测试范围与平台信息
            # 3. 获取质量评估标准参数
            self.question_stage()

            # ==================================================================
            # 阶段4：开发资源与周期分析
            # ==================================================================
            # 统计需求关联的所有子任务数据：
            # 1. 递归获取多级子任务结构
            # 2. 按开发者聚合总工时数据
            # 3. 计算开发周期与人力投入
            self.requirement_task_statistics()

            # ==================================================================
            # 阶段5：开发周期精细化计算（条件执行）
            # ==================================================================
            # 当存在每日工时数据时执行：
            # 1. 解析开发者每日投入工时
            # 2. 计算有效工作日及部分工作日折算
            # 3. 生成开发周期日报表
            if self.dailyWorkingHoursOfEachDeveloper:
                self.development_cycle()

            # ==================================================================
            # 阶段6：开发资源可视化输出
            # ==================================================================
            # 生成工时汇总报告：
            # 1. 计算开发者总工时及人均工时
            # 2. 格式化输出至控制台
            # 3. 生成工时分布直方图
            self.print_development_hours()

            # ==================================================================
            # 阶段7：缺陷数据采集与分析
            # ==================================================================
            # 通过TAPD缺陷接口获取全量缺陷数据：
            # 1. 分页获取缺陷列表
            # 2. 按严重等级/状态/根源分类统计
            # 3. 识别未修复及重开缺陷
            # 4. 生成缺陷分布矩阵
            self.bug_list_detail()

            # ==================================================================
            # 阶段8：系统视图配置还原
            # ==================================================================
            # 恢复列表视图的原始配置：
            # 1. 缺陷列表字段还原
            # 2. 需求列表字段还原
            # 3. 配置变更审计日志记录
            self.restore_list_config()

            # ==================================================================
            # 阶段9：质量指标体系计算
            # ==================================================================
            # 执行多维度质量评分计算：
            # 1. BUG密度评分
            # 2. 缺陷修复及时性评分
            # 3. 缺陷重开率评分
            # 4. 文档完备性评分
            # 5. 生成综合质量评分卡
            self.score_result()

            # ==================================================================
            # 阶段10：数据可视化生成
            # ==================================================================
            # 创建评估结果可视化图表：
            # 1. 工时分布柱状图
            # 2. 缺陷分类环形图
            # 3. 质量评分雷达图
            # 4. 生成图表HTML嵌入代码
            self.create_chart()

            # ==================================================================
            # 阶段11：测试报告生成与提交
            # ==================================================================
            # 构造并提交标准化测试报告：
            # 1. 组装报告基础信息（标题/接收人/抄送）
            # 2. 插入可视化图表及数据摘要
            # 3. 调用TAPD报告提交接口
            # 4. 触发AI总结生成（如配置启用）
            self.add_test_report()

        except ValueError as ve:
            # 数据校验异常处理
            traceback.print_exc()
            raise RuntimeError(f"流程执行失败: {str(ve)}") from ve
        except KeyboardInterrupt:
            # 用户中断处理
            self._print_error("\n警告：用户主动终止评分流程")
        finally:
            try:
                # ==================================================================
                # 最终阶段：防御性系统配置还原
                # ==================================================================
                # 确保在任何执行路径下均还原系统配置：
                # 1. 缺陷列表字段配置回滚
                # 2. 需求列表字段配置回滚
                # 3. 事务性操作保障
                self.restore_list_config()
            except Exception as final_error:
                traceback.print_exc()
                raise RuntimeError(f"配置还原失败: {str(final_error)}") from final_error



if __name__ == "__main__":
    SoftwareQualityRating().run()
