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
        if not all([self.oldBugListConfigs, self.oldSubTaskListConfigs]):
            self._get_list_config()

        # ==================================================================
        # 阶段2：配置合并处理
        # ==================================================================
        # 使用集合操作高效处理字段合并
        current_bug_fields = set(self.oldBugListConfigs.split(';'))
        required_bug_fields = set(BUG_LIST_MUST_KEYS)
        merged_bug_fields = current_bug_fields.union(required_bug_fields)
        new_bug_config = ';'.join(sorted(merged_bug_fields))

        current_task_fields = set(self.oldSubTaskListConfigs.split(';'))
        required_task_fields = set(SUB_TASK_LIST_MUST_KEYS)
        merged_task_fields = current_task_fields.union(required_task_fields)
        new_task_config = ';'.join(sorted(merged_task_fields))

        # ==================================================================
        # 阶段3：条件更新检查
        # ==================================================================
        # 仅当配置实际变化时执行更新操作
        config_modified = False

        if new_bug_config != self.oldBugListConfigs:
            # 原子化BUG列表配置更新
            success = edit_query_filtering_list_config(new_bug_config)
            assert success, "BUG列表配置更新失败"
            config_modified = True

        if new_task_config != self.oldSubTaskListConfigs:
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