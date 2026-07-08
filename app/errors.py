from fastapi import status


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, detail: str = ""):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(message)


def invalid_request(message: str = "请求参数不正确。") -> AppError:
    return AppError(status.HTTP_400_BAD_REQUEST, "INVALID_REQUEST", message)


def rate_limited() -> AppError:
    return AppError(status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMITED", "请求过于频繁，请稍后再试。")


def ai_failed(detail: str = "") -> AppError:
    return AppError(status.HTTP_500_INTERNAL_SERVER_ERROR, "PLAN_GENERATION_FAILED", "计划生成失败，请稍后重试。", detail)


def invalid_ai_output(detail: str = "") -> AppError:
    return AppError(status.HTTP_502_BAD_GATEWAY, "PLAN_GENERATION_FAILED", "计划生成失败，请稍后重试。", detail)

