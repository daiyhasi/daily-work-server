from typing import List, Optional


def build_generation_messages(user_prompt: str, hidden_instructions: List[str], response_schema: str):
    instructions = "\n".join(f"- {item}" for item in hidden_instructions)

    system_prompt = f"""你是一个谨慎的中文健身和饮食计划生成助手。

必须输出严格 JSON 对象，不能输出 Markdown、解释、代码块或额外文本。
必须生成完整的 daily-training-plan/v1 文档：
- schemaVersion 固定为 "daily-training-plan/v1"
- source 固定为 "ai"
- durationWeeks 固定为 4
- weeks 必须有 4 周，每周 days 必须有 7 天，weekday 从 1 到 7，周一为 1
- type 只能是 cardio、strength、recovery、rest
- 每天 trainingTasks 必须非空，且 points 合计必须等于 100
- 同一天 trainingTasks 的 id 必须唯一、稳定、短小，例如 w1d1-warmup
- 文案使用中文，强度保守，避免极端节食、脱水或危险动作

隐藏约束：
{instructions}

响应结构参考：
{response_schema}
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_repair_messages(
    user_prompt: str,
    hidden_instructions: List[str],
    response_schema: str,
    invalid_output: str,
    validation_error: str,
):
    base_messages = build_generation_messages(user_prompt, hidden_instructions, response_schema)
    repair_prompt = f"""上一次输出没有通过服务端校验。请只返回修复后的完整 JSON 对象。

校验错误：
{validation_error}

上一次输出：
{invalid_output}
"""

    return [
        base_messages[0],
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": invalid_output[:20000]},
        {"role": "user", "content": repair_prompt},
    ]


def build_metadata_messages(user_prompt: str, hidden_instructions: List[str]):
    instructions = "\n".join(f"- {item}" for item in hidden_instructions)
    system_prompt = f"""你是一个谨慎的中文健身和饮食计划生成助手。

必须只返回严格 JSON 对象，不要 Markdown、解释或代码块。
这一步只生成计划元信息，不生成每天训练详情。

输出结构固定为：
{{
  "profile": {{
    "heightCm": 174,
    "weightJin": 156,
    "bodyNotes": ["肚子大", "手臂细"],
    "abilityNotes": ["力量小", "耐力小"],
    "goal": "健身锻炼身体",
    "currentDiet": "每天两顿沙县鸡腿饭"
  }},
  "globalRules": ["每日通用规则"],
  "dailyHabits": ["日常小习惯"]
}}

隐藏约束：
{instructions}
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_week_messages(
    user_prompt: str,
    hidden_instructions: List[str],
    response_schema: str,
    week_number: int,
    metadata_json: str,
):
    instructions = "\n".join(f"- {item}" for item in hidden_instructions)
    system_prompt = f"""你是一个谨慎的中文健身和饮食计划生成助手。

必须只返回严格 JSON 对象，不要 Markdown、解释或代码块。
这一步只生成第 {week_number} 周，输出必须是单个 GeneratedPlanWeek 对象，不要包含 schemaVersion/source/durationWeeks/profile/globalRules/dailyHabits。

硬性规则：
- week 固定为 {week_number}
- days 必须正好 7 天
- weekday 必须是 1 到 7，周一为 1
- 每个 day.week 必须等于 {week_number}
- type 只能是 cardio、strength、recovery、rest
- 每天 trainingTasks 必须非空，且 points 合计必须等于 100
- 同一天 trainingTasks 的 id 必须唯一、稳定、短小，例如 w{week_number}d1-warmup
- 文案使用中文，强度保守，避免极端节食、脱水或危险动作

隐藏约束：
{instructions}

全局计划元信息：
{metadata_json}

完整响应结构参考：
{response_schema}
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_object_repair_messages(invalid_output: str, validation_error: str):
    return [
        {
            "role": "system",
            "content": "你是 JSON 修复助手。必须只返回修复后的完整 JSON 对象，不要 Markdown、解释或代码块。",
        },
        {
            "role": "user",
            "content": f"""下面 JSON 没有通过校验，请修复字段和值，保持原业务含义。

校验错误：
{validation_error}

待修复内容：
{invalid_output}
""",
        },
    ]


def compact_messages_for_log(messages) -> Optional[str]:
    if not messages:
        return None
    last = messages[-1].get("content", "")
    return last[:120].replace("\n", " ")
