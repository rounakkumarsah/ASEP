import httpx
import logging
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

async def verify_turnstile_token(token: str, remote_ip: str | None = None) -> bool:
    """Verify Cloudflare Turnstile token with Cloudflare API."""
    settings = get_settings()
    
    is_localhost = remote_ip in ("127.0.0.1", "localhost", "::1")
    
    if settings.APP_ENV != "production":
        # Allow mock tokens to bypass API verification in non-production entirely
        if token in ("", "mock-turnstile-token", "dummy-turnstile-token", "mock-cloudflare-turnstile-token"):
            logger.debug("Turnstile bypassed (dev mode, mock token)")
            return True
        secret_key = "1x0000000000000000000000000000000AA"
    elif is_localhost:
        # Allow localhost in any env with mock tokens
        if token in ("", "mock-turnstile-token", "dummy-turnstile-token", "mock-cloudflare-turnstile-token"):
            return True
        secret_key = settings.TURNSTILE_SECRET_KEY or "1x0000000000000000000000000000000AA"
    else:
        if not token:
            logger.warning("Turnstile verification failed: Missing token.")
            return False

        secret_key = settings.turnstile_secret or "1x0000000000000000000000000000000AA"
        
        # In production, reject any dummy/mock token values
        if token in ("mock-turnstile-token", "dummy-turnstile-token", "mock-cloudflare-turnstile-token"):
            logger.warning("Mock Turnstile token rejected in production environment.")
            return False

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
            
            if settings.APP_ENV != "production":
                logger.info(
                    f"Turnstile verification result: "
                    f"success={success}, "
                    f"hostname={res_data.get('hostname')}, "
                    f"action={res_data.get('action')}, "
                    f"challenge_ts={res_data.get('challenge_ts')}, "
                    f"error-codes={res_data.get('error-codes')}"
                )
            
            if not success:
                logger.warning(f"Turnstile verification failed: {res_data.get('error-codes')}")
            return success
    except Exception as e:
        logger.exception(f"Exception during Turnstile validation: {e}")
        return False
