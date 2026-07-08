import asyncio
import json
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.ai_client import AIClient
from app.errors import invalid_ai_output
from app.json_utils import parse_json_object
from app.models import GeneratedPlanDocument, GeneratedPlanMetadata, GeneratedPlanWeek, PlanGenerationRequest
from app.prompts import (
    build_generation_messages,
    build_metadata_messages,
    build_object_repair_messages,
    build_repair_messages,
    build_week_messages,
)


T = TypeVar("T", bound=BaseModel)


async def generate_plan(request: PlanGenerationRequest, ai_client: AIClient) -> GeneratedPlanDocument:
    return await generate_plan_by_weeks(request, ai_client)


async def generate_plan_whole_document(request: PlanGenerationRequest, ai_client: AIClient) -> GeneratedPlanDocument:
    messages = build_generation_messages(request.userPrompt, request.hiddenInstructions, request.responseSchema)
    raw_output = await ai_client.complete_json(messages)

    try:
        return validate_raw_output(raw_output)
    except (ValueError, ValidationError) as first_error:
        repair_messages = build_repair_messages(
            request.userPrompt,
            request.hiddenInstructions,
            request.responseSchema,
            raw_output,
            str(first_error),
        )
        repaired_output = await ai_client.complete_json(repair_messages)

        try:
            return validate_raw_output(repaired_output)
        except (ValueError, ValidationError) as second_error:
            raise invalid_ai_output(str(second_error))


async def generate_plan_by_weeks(request: PlanGenerationRequest, ai_client: AIClient) -> GeneratedPlanDocument:
    metadata_messages = build_metadata_messages(request.userPrompt, request.hiddenInstructions)
    metadata = await complete_and_validate(ai_client, metadata_messages, GeneratedPlanMetadata)
    metadata_json = json.dumps(metadata.model_dump(), ensure_ascii=False)

    async def generate_week(week_number: int) -> GeneratedPlanWeek:
        week_messages = build_week_messages(
            request.userPrompt,
            request.hiddenInstructions,
            request.responseSchema,
            week_number,
            metadata_json,
        )
        return await complete_and_validate(ai_client, week_messages, GeneratedPlanWeek)

    weeks = await asyncio.gather(*(generate_week(week_number) for week_number in range(1, 5)))

    document = {
        "schemaVersion": "daily-training-plan/v1",
        "source": "ai",
        "durationWeeks": 4,
        "profile": metadata.profile.model_dump(),
        "globalRules": metadata.globalRules,
        "dailyHabits": metadata.dailyHabits,
        "weeks": [week.model_dump() for week in weeks],
    }
    return GeneratedPlanDocument.model_validate(document)


async def complete_and_validate(ai_client: AIClient, messages, model: Type[T]) -> T:
    raw_output = await ai_client.complete_json(messages)
    try:
        return model.model_validate(parse_json_object(raw_output))
    except (ValueError, ValidationError) as first_error:
        repair_messages = build_object_repair_messages(raw_output, str(first_error))
        repaired_output = await ai_client.complete_json(repair_messages)
        try:
            return model.model_validate(parse_json_object(repaired_output))
        except (ValueError, ValidationError) as second_error:
            raise invalid_ai_output(str(second_error))


def validate_raw_output(raw_output: str) -> GeneratedPlanDocument:
    parsed = parse_json_object(raw_output)
    return GeneratedPlanDocument.model_validate(parsed)
