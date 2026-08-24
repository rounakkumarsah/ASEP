import logging

import httpx

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

async def verify_turnstile_token(token: str | None, remote_ip: str | None = None) -> bool:
    """Verify Cloudflare Turnstile token with Cloudflare API."""
    settings = get_settings()

    # Feature flag check
    if not settings.ENABLE_TURNSTILE:
        logger.info("Turnstile verification skipped: ENABLE_TURNSTILE is False")
        return True

    if not token:
        logger.warning("Turnstile verification failed: Missing token.")
        return False

    is_localhost = remote_ip in ("127.0.0.1", "localhost", "::1")

    # Non-production or local bypass
    if (settings.APP_ENV != "production" or is_localhost) and token in (
        "",
        "mock-turnstile-token",
        "dummy-turnstile-token",
        "mock-cloudflare-turnstile-token",
    ):
        logger.debug("Turnstile bypassed (dev mode, mock token)")
        return True

    # Use backend environment secret key, or Cloudflare's always-pass test secret key (1x00...)
    secret_key = settings.turnstile_secret or "1x0000000000000000000000000000000AA"

    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {
        "secret": secret_key,
        "response": token,
    }
    if remote_ip and remote_ip != "unknown":
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
                logger.warning(
                    f"Turnstile verification failed: error-codes={res_data.get('error-codes')}, "
                    f"hostname={res_data.get('hostname')}"
                )
            return bool(success)
    except Exception as e:
        logger.exception(f"Exception during Turnstile validation: {e}")
        return False
