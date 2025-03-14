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
    if sub_key:
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
    # 阶段5：数据聚合（防御性计数）
    # ==================================================================
    try:
        # 原子操作更新计数器
        result[processed_key][processed_sub_key] += 1
    except KeyError as e:
        # 异常处理策略（根据需求可选）：
        # 方案1：忽略未定义维度（当前实现）
        # 方案2：动态扩展维度（需评估业务需求）
        print(f"未定义子维度 {e}，该数据未被统计")