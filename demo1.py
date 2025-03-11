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
    model_mapping = {
        'v3': 'deepseek-chat',
        'r1': 'deepseek-reasoner',
        '百炼r1': 'deepseek-r1',
        '百炼v3': 'deepseek-v3'
    }

    # 防御性配置校验
    open_ai_model = OPEN_AI_MODEL.lower()
    if open_ai_model not in model_mapping:
        raise ValueError(f'模型配置错误，支持: {", ".join(model_mapping.keys())}')

    # ==================================================================
    # API交互核心逻辑
    # ==================================================================
    client = OpenAI(
        api_key=OPEN_AI_KEY,
        base_url=OPEN_AI_URL,
        timeout=30.0  # 统一超时设置
    )

    for attempt in range(retries):
        try:
            # 创建聊天补全请求
            completion = client.chat.completions.create(
                model=model_mapping[open_ai_model],
                messages=[{"role": "user", "content": user_input}],
                stream=OPEN_AI_IS_STREAM_RESPONSE,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
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


def _handle_stream_response(completion, result: list) -> str:
    """处理流式响应数据"""
    print(f'\n{datetime.now().strftime("%H:%M:%S")} 生成开始')

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
                    print('\n思考轨迹:', end='', flush=True)
                    is_reasoning = True
                print(f'\033[90m{reasoning_content}\033[0m', end='', flush=True)

            # 最终答案处理
            if content:
                if not is_final_answer:
                    print('\n\n最终答案:', end='', flush=True)
                    is_final_answer = True
                print(content, end='', flush=True)
                result.append(content)

        print(f'\n\n{datetime.now().strftime("%H:%M:%S")} 生成完成')
        return ai_result_switch_html(''.join(result))

    except KeyboardInterrupt:
        print('\n\n生成过程已中断')
        return ai_result_switch_html(''.join(result))


def _handle_normal_response(completion, result: list) -> str:
    """处理非流式响应数据"""
    print(f'\n{datetime.now().strftime("%H:%M:%S")} 生成开始')

    try:
        # 提取思考过程
        if reasoning_content := completion.choices[0].message.reasoning_content:
            print("\n思考轨迹:\n\033[90m{}\033[0m".format(reasoning_content))

        # 提取最终答案
        if final_answer := completion.choices[0].message.content:
            print("\n最终答案:\n{}".format(final_answer))
            result.append(final_answer)

        print(f'\n{datetime.now().strftime("%H:%M:%S")} 生成完成')
        return ai_result_switch_html(''.join(result))

    except AttributeError as e:
        raise APIError("响应结构异常") from e