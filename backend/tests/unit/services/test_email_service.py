import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.email_service import EmailService
from src.db.models.audit_log import ActorType, AuditOutcome

@pytest.mark.asyncio
async def test_email_service_mock_sending():
    audit_service = MagicMock()
    audit_service.log_event = AsyncMock()
    
    email_service = EmailService(audit_service)
    # Set api_key to mock
    email_service.api_key = "mock"
    
    # Test sending verification email
    res = await email_service.send_verification_email("user@example.com", "username123", "token123")
    assert res is True
    audit_service.log_event.assert_called_once()
    assert audit_service.log_event.call_args[1]["action"] == "email.verify_sent_mock"

@pytest.mark.asyncio
async def test_email_service_welcome():
    audit_service = MagicMock()
    audit_service.log_event = AsyncMock()
    
    email_service = EmailService(audit_service)
    email_service.api_key = "mock"
    
    res = await email_service.send_welcome_email("user@example.com", "John Doe")
    assert res is True
    audit_service.log_event.assert_called_once()
    assert audit_service.log_event.call_args[1]["action"] == "email.welcome_sent_mock"

@pytest.mark.asyncio
async def test_email_service_reset_password():
    audit_service = MagicMock()
    audit_service.log_event = AsyncMock()
    
    email_service = EmailService(audit_service)
    email_service.api_key = "mock"
    
    res = await email_service.send_reset_password_email("user@example.com", "mock-token-123")
    assert res is True
    audit_service.log_event.assert_called_once()
    assert audit_service.log_event.call_args[1]["action"] == "email.forgot_password_sent_mock"
