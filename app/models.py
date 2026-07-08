from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


PlanType = Literal["cardio", "strength", "recovery", "rest"]


class PlanGenerationRequest(BaseModel):
    userPrompt: str = Field(min_length=1, max_length=6000)
    hiddenInstructions: List[str] = Field(default_factory=list, max_length=50)
    responseSchema: str = Field(default="", max_length=12000)

    @field_validator("userPrompt")
    @classmethod
    def prompt_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("userPrompt must not be empty")
        return stripped


class TrainingTask(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=200)
    points: int = Field(ge=1, le=100)


class DayPlan(BaseModel):
    week: int = Field(ge=1, le=4)
    weekday: int = Field(ge=1, le=7)
    title: str = Field(min_length=1, max_length=80)
    type: PlanType
    training: List[str] = Field(min_length=1, max_length=20)
    trainingTasks: List[TrainingTask] = Field(min_length=1, max_length=20)
    meals: List[str] = Field(min_length=1, max_length=20)
    notes: Optional[List[str]] = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def validate_tasks(self):
        point_total = sum(task.points for task in self.trainingTasks)
        if point_total != 100:
            raise ValueError("trainingTasks points must sum to exactly 100")

        task_ids = [task.id for task in self.trainingTasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("trainingTasks ids must be unique within the day")

        return self


class GeneratedPlanProfile(BaseModel):
    heightCm: int = Field(ge=100, le=250)
    weightJin: int = Field(ge=60, le=500)
    bodyNotes: List[str] = Field(default_factory=list, max_length=20)
    abilityNotes: List[str] = Field(default_factory=list, max_length=20)
    goal: str = Field(min_length=1, max_length=500)
    currentDiet: str = Field(min_length=1, max_length=500)


class GeneratedPlanMetadata(BaseModel):
    profile: GeneratedPlanProfile
    globalRules: List[str] = Field(min_length=1, max_length=30)
    dailyHabits: List[str] = Field(min_length=1, max_length=30)


class GeneratedPlanWeek(BaseModel):
    week: int = Field(ge=1, le=4)
    theme: str = Field(min_length=1, max_length=80)
    modifier: Optional[str] = Field(default=None, max_length=500)
    days: List[DayPlan] = Field(min_length=7, max_length=7)

    @model_validator(mode="after")
    def validate_days(self):
        weekdays = [day.weekday for day in self.days]
        if sorted(weekdays) != [1, 2, 3, 4, 5, 6, 7]:
            raise ValueError("week must contain weekdays 1 through 7")

        for day in self.days:
            if day.week != self.week:
                raise ValueError("day week must match parent week")

        return self


class GeneratedPlanDocument(BaseModel):
    schemaVersion: Literal["daily-training-plan/v1"]
    source: Literal["ai"]
    durationWeeks: Literal[4]
    profile: GeneratedPlanProfile
    globalRules: List[str] = Field(min_length=1, max_length=30)
    dailyHabits: List[str] = Field(min_length=1, max_length=30)
    weeks: List[GeneratedPlanWeek] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_weeks(self):
        week_numbers = [week.week for week in self.weeks]
        if sorted(week_numbers) != [1, 2, 3, 4]:
            raise ValueError("weeks must contain week 1 through 4")
        if len(self.weeks) != self.durationWeeks:
            raise ValueError("weeks length must equal durationWeeks")
        return self


class ErrorResponse(BaseModel):
    code: str
    message: str
