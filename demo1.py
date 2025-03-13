from typing import Dict, List, Tuple, Union
import numpy as np
from collections import OrderedDict


def switch_numpy_data(data: Dict[str, Union[Dict[str, float], float]]) -> Tuple[List[str], np.ndarray]:
    """
    通用数据转换方法，支持多层级字典结构处理

    参数:
        data: 支持两种数据结构：
            1. 多层结构：{样本名: {特征名: 值}}
            2. 单层结构：{样本名: 数值}

    返回:
        Tuple[List[str], np.ndarray]:
            - 特征标签列表（多层结构返回特征名，单层结构返回空列表）
            - 数据矩阵（多层结构形状为(特征数, 样本数)，单层结构为(1, 样本数))

    实现策略:
        1. 智能数据结构检测
        2. 多层结构特征顺序保留
        3. 自动维度对齐
        4. 空值安全处理
    """
    # ==================================================================
    # 阶段1：数据结构分析与校验
    # ==================================================================
    if not data:
        return [], np.array([], dtype=np.float64)

    # 检测数据结构类型
    is_multilayer = isinstance(next(iter(data.values())), dict)

    # 统一格式校验
    if is_multilayer:
        for v in data.values():
            if not isinstance(v, dict):
                raise TypeError("混合数据结构：包含字典和非字典值")

    # ==================================================================
    # 阶段2：特征标签处理
    # ==================================================================
    if is_multilayer:
        # 保持第一个样本的特征顺序
        feature_labels = list(next(iter(data.values())).keys())
        # 验证所有样本特征一致性
        for sample in data.values():
            if list(sample.keys()) != feature_labels:
                missing = set(feature_labels) - set(sample.keys())
                extra = set(sample.keys()) - set(feature_labels)
                raise ValueError(f"特征不一致，缺失：{missing}, 多余：{extra}")
    else:
        feature_labels = []

    # ==================================================================
    # 阶段3：数据矩阵构建
    # ==================================================================
    sample_names = list(data.keys())
    num_samples = len(sample_names)

    if is_multilayer:
        num_features = len(feature_labels)
        matrix = np.zeros((num_features, num_samples), dtype=np.float64)

        for col_idx, sample in enumerate(data.values()):
            for row_idx, label in enumerate(feature_labels):
                matrix[row_idx, col_idx] = sample.get(label, 0.0)
    else:
        matrix = np.array([list(data.values())], dtype=np.float64)

    return feature_labels, matrix


if __name__ == '__main__':
    data = {'H5': {'实现与文档不符': 3, '需求缺陷': 0, '技术方案考虑不足': 2, '环境问题': 2, '历史遗留缺陷': 1,
                   '第三方依赖': 0, '兼容性': 9, '性能问题': 0, '安全问题': 0, 'Bugfix 引入': 0, '无效缺陷': 2},
            'API': {'实现与文档不符': 2, '需求缺陷': 0, '技术方案考虑不足': 4, '环境问题': 1, '历史遗留缺陷': 0,
                    '第三方依赖': 0, '兼容性': 0, '性能问题': 0, '安全问题': 0, 'Bugfix 引入': 0, '无效缺陷': 0},
            'PC': {'实现与文档不符': 2, '需求缺陷': 1, '技术方案考虑不足': 7, '环境问题': 2, '历史遗留缺陷': 1,
                   '第三方依赖': 1, '兼容性': 1, '性能问题': 0, '安全问题': 0, 'Bugfix 引入': 0, '无效缺陷': 0},
            'IOS': {'实现与文档不符': 0, '需求缺陷': 1, '技术方案考虑不足': 2, '环境问题': 0, '历史遗留缺陷': 0,
                    '第三方依赖': 0, '兼容性': 1, '性能问题': 0, '安全问题': 0, 'Bugfix 引入': 0, '无效缺陷': 0},
            'Flutter': {'实现与文档不符': 3, '需求缺陷': 0, '技术方案考虑不足': 2, '环境问题': 0, '历史遗留缺陷': 0,
                        '第三方依赖': 0, '兼容性': 1, '性能问题': 0, '安全问题': 0, 'Bugfix 引入': 0, '无效缺陷': 0},
            '空': {'实现与文档不符': 0, '需求缺陷': 0, '技术方案考虑不足': 1, '环境问题': 0, '历史遗留缺陷': 0,
                   '第三方依赖': 0, '兼容性': 0, '性能问题': 0, '安全问题': 0, 'Bugfix 引入': 0, '无效缺陷': 0}}
    """以上data期望返回的是: 
    (['实现与文档不符', '需求缺陷', '技术方案考虑不足', '环境问题', '历史遗留缺陷', '第三方依赖', '兼容性', '性能问题', '安全问题', 'Bugfix 引入', '无效缺陷'], array([[3, 2, 2, 0, 3, 0],
       [0, 0, 1, 1, 0, 0],
       [2, 4, 7, 2, 2, 1],
       [2, 1, 2, 0, 0, 0],
       [1, 0, 1, 0, 0, 0],
       [0, 0, 1, 0, 0, 0],
       [9, 0, 1, 1, 1, 0],
       [0, 0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0, 0],
       [0, 0, 0, 0, 0, 0],
       [2, 0, 0, 0, 0, 0]]))
    """
    data1 = {'林洵锋': 103.0, '王镇': 120.0, '龚进': 163.5, '陈育林': 90.0, '韦江': 100.5, '汪勇奇': 47.0}
    """以上data期望返回的是: 
    ([], array([[103. , 120. , 163.5,  90. , 100.5,  47. ]]))
    """
    data2 = {'T5龚进': 25, 'T5林洵锋': 4, 'T5王镇': 4, 'T5韦江': 11, 'T5汪勇奇': 5, 'T5陈育林': 3}
    """以上data期望返回的是: 
    ([], array([[25,  4,  4, 11,  5,  3]]))
    """
    print(switch_numpy_data(data2))