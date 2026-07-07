from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from pathlib import Path

def is_rate_limit_error(exception: Exception) -> bool: 
    err_msg = str(exception).lower()
    return any(keyword in err_msg for keyword in ["429", "quota", "rate limit", "too many requests", "rate", "overloaded", "resource_exhausted"])

gemini_retry_decorator = retry(
    reraise=True, 
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2,min=2, max=10), 
    retry=retry_if_exception(is_rate_limit_error), 
    before_sleep=lambda retry_state: print(
        f"\n⚠️ Bị giới hạn API Gemini! Đang ngủ chờ thử lại "
        f"(Lần thử {retry_state.attempt_number}/4)..."
    )
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent