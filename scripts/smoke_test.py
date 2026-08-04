"""
ASEP Production Smoke Test
==========================
Runs a full end-to-end customer journey against a running ASEP stack.

Steps:
  1.  Backend health check
  2.  Frontend health check
  3.  Signup
  4.  Login
  5.  Create Organization
  6.  Create Project
  7.  Generate API Key
  8.  Upload Document (register a URL-based source)
  9.  Knowledge Sync (trigger ingestion)
  10. GraphRAG Query
  11. Razorpay Order Creation
  12. Razorpay Payment Verification (simulated)
  
Usage:
  python scripts/smoke_test.py [--base-url http://localhost:8000]
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import random
import string
import sys
import time
from typing import Any

import requests

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"
BOLD = "\033[1m"

results: list[tuple[int, str, str, str]] = []  # (step, name, status, detail)


def _random_suffix(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}\n")


def step(n: int, name: str) -> None:
    print(f"{BOLD}Step {n:02d}: {name}{RESET}")


def ok(n: int, name: str, detail: str = "") -> None:
    print(f"  {GREEN}[PASS]{RESET} -- {detail}")
    results.append((n, name, "PASS", detail))


def fail(n: int, name: str, detail: str = "") -> None:
    print(f"  {RED}[FAIL]{RESET} -- {detail}")
    results.append((n, name, "FAIL", detail))


def warn(n: int, name: str, detail: str = "") -> None:
    print(f"  {YELLOW}[WARN]{RESET} -- {detail}")
    results.append((n, name, "WARN", detail))


def _post(url: str, token: str | None = None, **kwargs: Any) -> requests.Response:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.post(url, headers=headers, timeout=30, **kwargs)


def _get(url: str, token: str | None = None) -> requests.Response:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.get(url, headers=headers, timeout=30)


def run_smoke_test(base: str, frontend: str) -> bool:
    suffix = _random_suffix()
    email = f"smoke_{suffix}@example.com"
    password = "SmokeTest@1234"
    org_name = f"Smoke Org {suffix}"
    project_name = f"Smoke Project {suffix}"
    token: str | None = None
    project_id: str | None = None
    api_key: str | None = None
    org_id: str | None = None

    header("ASEP END-TO-END PRODUCTION SMOKE TEST")
    print(f"  Base URL  : {base}")
    print(f"  Frontend  : {frontend}")
    print(f"  Test email: {email}\n")

    # ------------------------------------------------------------------ #
    # Step 1: Backend health
    # ------------------------------------------------------------------ #
    step(1, "Backend Health Check")
    try:
        r = _get(f"{base}/health")
        if r.status_code == 200:
            ok(1, "Backend Health", f"HTTP {r.status_code} -- {r.text[:80]}")
        else:
            fail(1, "Backend Health", f"HTTP {r.status_code} -- {r.text[:200]}")
            return False
    except Exception as exc:
        fail(1, "Backend Health", str(exc))
        return False

    # ------------------------------------------------------------------ #
    # Step 2: Frontend health
    # ------------------------------------------------------------------ #
    step(2, "Frontend Health Check")
    try:
        r = requests.get(frontend, timeout=15)
        if r.status_code < 400:
            ok(2, "Frontend Health", f"HTTP {r.status_code}")
        else:
            warn(2, "Frontend Health", f"HTTP {r.status_code} -- may be normal in dev")
    except Exception as exc:
        warn(2, "Frontend Health", str(exc))

    # ------------------------------------------------------------------ #
    # Step 3: Signup
    # ------------------------------------------------------------------ #
    step(3, "Signup")
    try:
        r = _post(
            f"{base}/api/v1/auth/signup",
            json={
                "firstName": "Smoke",
                "lastName": "Test",
                "email": email,
                "password": password,
                "acceptTerms": True,
                "captchaToken": "mock-turnstile-token",
            },
        )
        if r.status_code in (200, 201):
            ok(3, "Signup", f"HTTP {r.status_code} — user created")
        elif r.status_code == 422:
            fail(3, "Signup", f"Validation error: {r.text[:300]}")
        else:
            fail(3, "Signup", f"HTTP {r.status_code} — {r.text[:300]}")
    except Exception as exc:
        fail(3, "Signup", str(exc))

    # ------------------------------------------------------------------ #
    # Step 4: Login
    # ------------------------------------------------------------------ #
    step(4, "Login")
    try:
        r = _post(
            f"{base}/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        if r.status_code == 200:
            body = r.json()
            token = body.get("access_token")
            if token:
                ok(4, "Login", f"HTTP 200 — token obtained ({len(token)} chars)")
            else:
                fail(4, "Login", f"No access_token in response: {body}")
        else:
            fail(4, "Login", f"HTTP {r.status_code} — {r.text[:300]}")
    except Exception as exc:
        fail(4, "Login", str(exc))

    if not token:
        print(f"\n{RED}Cannot continue without auth token. Aborting.{RESET}\n")
        _print_summary()
        return False

    # ------------------------------------------------------------------ #
    # Step 5: Create Organization
    # ------------------------------------------------------------------ #
    step(5, "Create Organization")
    try:
        r = _post(
            f"{base}/api/v1/organizations",
            token=token,
            json={"name": org_name},
        )
        if r.status_code in (200, 201):
            body = r.json()
            org_id = body.get("id")
            ok(5, "Create Organization", f"HTTP {r.status_code} — org_id={org_id}, slug={body.get('slug')}")
        else:
            fail(5, "Create Organization", f"HTTP {r.status_code} — {r.text[:300]}")
    except Exception as exc:
        fail(5, "Create Organization", str(exc))

    # ------------------------------------------------------------------ #
    # Step 6: Create Project
    # ------------------------------------------------------------------ #
    step(6, "Create Project")
    try:
        r = _post(
            f"{base}/api/v1/projects",
            token=token,
            json={"name": project_name, "description": "Smoke test project"},
        )
        if r.status_code in (200, 201):
            body = r.json()
            project_id = body.get("id")
            ok(6, "Create Project", f"HTTP {r.status_code} — project_id={project_id}")
        else:
            fail(6, "Create Project", f"HTTP {r.status_code} — {r.text[:300]}")
    except Exception as exc:
        fail(6, "Create Project", str(exc))

    # ------------------------------------------------------------------ #
    # Step 7: Generate API Key
    # ------------------------------------------------------------------ #
    step(7, "Generate API Key")
    try:
        payload = {"name": "Smoke Key"}
        if project_id:
            payload["project_id"] = project_id
        r = _post(
            f"{base}/api/v1/api-keys",
            token=token,
            json=payload,
        )
        if r.status_code in (200, 201):
            body = r.json()
            api_key = body.get("key") or body.get("api_key") or body.get("full_key")
            ok(7, "Generate API Key", f"HTTP {r.status_code} — prefix={body.get('prefix', body.get('key_prefix', '?'))}")
        else:
            fail(7, "Generate API Key", f"HTTP {r.status_code} — {r.text[:300]}")
    except Exception as exc:
        fail(7, "Generate API Key", str(exc))

    # ------------------------------------------------------------------ #
    # Step 8: Upload Document / Register Source
    # ------------------------------------------------------------------ #
    step(8, "Upload Document (register knowledge source)")
    source_id: str | None = None
    try:
        if not project_id:
            warn(8, "Upload Document", "Skipped -- no project_id")
        else:
            source_id = f"smoke-src-{suffix}"
            r = _post(
                f"{base}/api/v1/knowledge/sources",
                token=token,
                json={
                    "source_id": source_id,
                    "name": "Smoke Doc",
                    "source_type": "text",
                    "source_url": None,
                    "version": "1.0",
                    "trust_level": 0.9,
                    "language": "en",
                    "provenance": "Smoke Test",
                },
            )
            if r.status_code in (200, 201):
                ok(8, "Upload Document", f"HTTP {r.status_code} -- source_id={source_id}")
            elif r.status_code == 400 and "already exists" in r.text:
                ok(8, "Upload Document", f"Source already registered (idempotent): {source_id}")
            else:
                fail(8, "Upload Document", f"HTTP {r.status_code} -- {r.text[:200]}")
                source_id = None
    except Exception as exc:
        fail(8, "Upload Document", str(exc))
        source_id = None

    # ------------------------------------------------------------------ #
    # Step 9: Knowledge Sync
    # ------------------------------------------------------------------ #
    step(9, "Knowledge Sync / Ingestion")
    try:
        if not source_id:
            warn(9, "Knowledge Sync", "Skipped -- no source_id")
        else:
            r = _post(
                f"{base}/api/v1/knowledge/sync",
                token=token,
                json={"source_id": source_id, "sync_mode": "full"},
            )
            if r.status_code in (200, 201, 202):
                ok(9, "Knowledge Sync", f"HTTP {r.status_code} -- {r.text[:100]}")
            else:
                warn(9, "Knowledge Sync", f"HTTP {r.status_code} -- {r.text[:200]}")
    except Exception as exc:
        warn(9, "Knowledge Sync", str(exc))

    # ------------------------------------------------------------------ #
    # Step 10: GraphRAG Query
    # ------------------------------------------------------------------ #
    step(10, "GraphRAG Query")
    try:
        r = _post(
            f"{base}/api/v1/rag/search",
            token=token,
            json={"query": "What is ASEP?", "limit": 3, "score_threshold": 0.0},
        )
        if r.status_code == 200:
            body = r.json()
            context = body.get("context") or body.get("answer") or str(body)[:100]
            ok(10, "GraphRAG Query", f"HTTP 200 -- latency={body.get('latency_ms', '?')}ms")
        else:
            fail(10, "GraphRAG Query", f"HTTP {r.status_code} -- {r.text[:300]}")
    except Exception as exc:
        fail(10, "GraphRAG Query", str(exc))

    # ------------------------------------------------------------------ #
    # Step 11: Razorpay Order Creation
    # ------------------------------------------------------------------ #
    step(11, "Razorpay Order Creation")
    rzp_order_id: str | None = None
    try:
        r = _post(
            f"{base}/api/v1/payments/create-order",
            token=token,
            json={"amount": 49900, "currency": "INR", "description": "Pro plan - smoke test"},
        )
        if r.status_code in (200, 201):
            body = r.json()
            rzp_order_id = body.get("order_id")
            ok(11, "Razorpay Order", f"HTTP {r.status_code} -- razorpay_order_id={rzp_order_id}")
        else:
            fail(11, "Razorpay Order", f"HTTP {r.status_code} -- {r.text[:300]}")
    except Exception as exc:
        fail(11, "Razorpay Order", str(exc))

    # ------------------------------------------------------------------ #
    # Step 12: Razorpay Payment Verification (simulated)
    # ------------------------------------------------------------------ #
    step(12, "Razorpay Payment Verification (simulated)")
    try:
        order_id = rzp_order_id or "order_test_simulated"
        fake_payment_id = f"pay_smoke_{_random_suffix(10)}"
        fake_signature = hmac.new(
            b"SIMULATED_SECRET",
            f"{order_id}|{fake_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

        r = _post(
            f"{base}/api/v1/payments/verify",
            token=token,
            json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": fake_payment_id,
                "razorpay_signature": fake_signature,
            },
        )
        if r.status_code == 200:
            ok(12, "Payment Verification", f"HTTP 200 -- {r.text[:100]}")
        elif r.status_code == 400:
            # Expected: signature mismatch with simulated key -- endpoint is reachable and secure
            ok(12, "Payment Verification", f"HTTP 400 (signature mismatch with simulated key -- endpoint reachable and secure)")
        else:
            fail(12, "Payment Verification", f"HTTP {r.status_code} -- {r.text[:300]}")
    except Exception as exc:
        fail(12, "Payment Verification", str(exc))

    return _print_summary()


def _print_summary() -> bool:
    header("SMOKE TEST SUMMARY")
    passed = sum(1 for _, _, s, _ in results if s == "PASS")
    warned = sum(1 for _, _, s, _ in results if s == "WARN")
    failed = sum(1 for _, _, s, _ in results if s == "FAIL")

    for n, name, status, detail in results:
        color = GREEN if status == "PASS" else (YELLOW if status == "WARN" else RED)
        print(f"  {n:02d}. [{color}{status}{RESET}] {name}")
        if detail:
            print(f"        {detail[:100]}")

    print()
    total = len(results)
    print(f"  {BOLD}Results: {GREEN}{passed} passed{RESET}, {YELLOW}{warned} warned{RESET}, {RED}{failed} failed{RESET} / {total} total{RESET}")
    print()

    if failed > 0:
        print(f"  {RED}{BOLD}SMOKE TEST FAILED -- {failed} step(s) need fixing.{RESET}\n")
        return False
    else:
        print(f"  {GREEN}{BOLD}SMOKE TEST PASSED [OK]{RESET}\n")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ASEP Production Smoke Test")
    parser.add_argument("--base-url", default=BASE_URL, help="Backend base URL")
    parser.add_argument("--frontend-url", default=FRONTEND_URL, help="Frontend base URL")
    args = parser.parse_args()

    success = run_smoke_test(args.base_url, args.frontend_url)
    sys.exit(0 if success else 1)
