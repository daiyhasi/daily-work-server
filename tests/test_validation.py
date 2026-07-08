import pytest
from pydantic import ValidationError

from app.models import GeneratedPlanDocument


def make_valid_plan():
    def day(week, weekday):
        return {
            "week": week,
            "weekday": weekday,
            "title": "训练日",
            "type": "cardio",
            "training": ["热身 5 分钟，爬坡 15 分钟，放松 5 分钟"],
            "trainingTasks": [
                {"id": f"w{week}d{weekday}-warmup", "label": "热身 5 分钟", "points": 20},
                {"id": f"w{week}d{weekday}-main", "label": "主训练", "points": 60},
                {"id": f"w{week}d{weekday}-cooldown", "label": "放松 5 分钟", "points": 20},
            ],
            "meals": ["鸡腿饭，米饭一拳，两份青菜"],
            "notes": ["量力而行"],
        }

    return {
        "schemaVersion": "daily-training-plan/v1",
        "source": "ai",
        "durationWeeks": 4,
        "profile": {
            "heightCm": 174,
            "weightJin": 156,
            "bodyNotes": ["肚子大"],
            "abilityNotes": ["耐力弱"],
            "goal": "健身锻炼身体",
            "currentDiet": "每天两顿沙县鸡腿饭",
        },
        "globalRules": ["每日饮水 2400ml"],
        "dailyHabits": ["训练后记录完成情况"],
        "weeks": [
            {
                "week": week,
                "theme": f"第 {week} 周",
                "modifier": "保守进阶",
                "days": [day(week, weekday) for weekday in range(1, 8)],
            }
            for week in range(1, 5)
        ],
    }


def test_valid_plan_passes():
    plan = GeneratedPlanDocument.model_validate(make_valid_plan())
    assert plan.schemaVersion == "daily-training-plan/v1"
    assert len(plan.weeks) == 4


def test_points_must_sum_to_100():
    data = make_valid_plan()
    data["weeks"][0]["days"][0]["trainingTasks"][0]["points"] = 10

    with pytest.raises(ValidationError):
        GeneratedPlanDocument.model_validate(data)


def test_each_week_must_have_7_days():
    data = make_valid_plan()
    data["weeks"][0]["days"].pop()

    with pytest.raises(ValidationError):
        GeneratedPlanDocument.model_validate(data)

