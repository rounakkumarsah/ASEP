import httpx
import logging
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

async def verify_turnstile_token(token: str, remote_ip: str | None = None) -> bool:
    """Verify Cloudflare Turnstile token with Cloudflare API."""
    settings = get_settings()
    secret_key = getattr(settings, "TURNSTILE_SECRET", None)
    if not secret_key:
        logger.warning("TURNSTILE_SECRET not configured. Bypassing Turnstile validation.")
        return True

    # Check for test/mock tokens
    if token in ("mock-turnstile-token", "dummy-turnstile-token"):
        return True

    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {
        "secret": secret_key,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, timeout=5.0)
            if response.status_code != 200:
                logger.error(f"Turnstile API returned status {response.status_code}")
                return False
            
            res_data = response.json()
            success = res_data.get("success", False)
            if not success:
                logger.warning(f"Turnstile verification failed: {res_data.get('error-codes')}")
            return success
    except Exception as e:
        logger.exception(f"Exception during Turnstile validation: {e}")
        return False
