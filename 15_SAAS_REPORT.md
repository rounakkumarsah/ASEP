# 15 — SaaS Readiness & Monetization Forensic Report: ASEP

**Audit Date**: August 2026  
**Methodology**: Inspection of `backend/src/api/routers/payments.py`, `backend/src/db/models/subscription.py`, `backend/src/db/models/organization.py`, and `frontend/src/app/pricing/page.tsx`.

---

## 1. Monetization Subsystem (Razorpay Gateway)

Implemented in `backend/src/api/routers/payments.py`.

- **Order Creation**: `POST /api/v1/payments/create-order` generating Razorpay order IDs with amount in paise.
- **Server-Side Verification**: `POST /api/v1/payments/verify` with HMAC-SHA256 signature verification (`razorpay_order_id|razorpay_payment_id`).
- **Webhook Processing**: `POST /api/v1/payments/webhook` handling subscription updates and payment captures with signature checking.
- **Live/Test Switching**: Environment-controlled keys (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`) requiring zero source code edits to switch between sandbox and production.

---

## 2. Subscription Tiers & Multi-Tenancy

- **Tiers Supported**: Developer ($0), Team ($49/mo), Enterprise (Custom).
- **Organization Scoping**: Multi-tenant organizations with slug URLs (`backend/src/api/routers/organizations.py`).
- **Developer Quotas**: Scoped API key management with granular permissions.
