import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.ai_client import AIClient
from app.config import get_settings
from app.errors import AppError, invalid_request
from app.models import ErrorResponse, GeneratedPlanDocument, PlanGenerationRequest
from app.rate_limit import InMemoryRateLimiter
from app.service import generate_plan

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
ai_client = AIClient(settings)
rate_limiter = InMemoryRateLimiter(settings.rate_limit_per_minute)

app = FastAPI(title="Daily Work Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    started = time.perf_counter()
    response = None
    error_code = "-"

    try:
        response = await call_next(request)
        error_code = getattr(request.state, "error_code", "-")
        return response
    finally:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        status_code = getattr(response, "status_code", 500)
        logger.info(
            "request_id=%s method=%s path=%s status=%s latency_ms=%s model=%s error_code=%s",
            request_id,
            request.method,
            request.url.path,
            status_code,
            latency_ms,
            settings.openai_model,
            error_code,
        )
        if response is not None:
            response.headers["X-Request-ID"] = request_id


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    request.state.error_code = exc.code
    if exc.detail:
        logger.warning("request_id=%s code=%s detail=%s", request.state.request_id, exc.code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(code=exc.code, message=exc.message).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    error = invalid_request()
    request.state.error_code = error.code
    logger.info("request_id=%s validation_error=%s", request.state.request_id, exc.errors())
    return JSONResponse(
        status_code=error.status_code,
        content=ErrorResponse(code=error.code, message=error.message).model_dump(),
    )


@app.get("/health")
async def health():
    return {"ok": True}


@app.post(
    "/plans/generate",
    response_model=GeneratedPlanDocument,
    responses={
        400: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
async def plans_generate(request: Request, body: PlanGenerationRequest):
    client_host = request.client.host if request.client else "unknown"
    rate_limiter.check(client_host)
    plan = await generate_plan(body, ai_client)
    logger.info("request_id=%s validation_result=ok weeks=%s", request.state.request_id, len(plan.weeks))
    return plan

