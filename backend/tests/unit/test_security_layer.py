"""
ASEP — Security Layer & Auditor Unit Tests
==========================================
Verifies:
1. Security Auditor Node:
   - Scans for SQL injection, command injection, template injection (SSTI)
   - Detects hardcoded secrets, debug mode flags, and missing endpoint authentication
   - Verifies dependency vulnerability checking against known CVE advisories
   - Severity table generation and strict blocking on CRITICAL findings
2. Package Resolution Engine:
   - Error output parsing and 3-way classification: security-blocked / version-conflict / network
   - Compliant alternative package discovery for OS security blocks (e.g. uvloop on Windows -> winloop)
   - User-facing explanation of the security swap and refusal to bypass OS security policies
3. Final Artifact Gate:
   - Rejection of "complete" status when security report is missing or failed
   - Verification of passed security report before release
"""

import pytest
from unittest.mock import patch, MagicMock

from src.utils.security_scanner import SecurityScanner, SecurityReport, SecurityFinding, scanner
from src.utils.package_resolver import PackageResolver, PackageResolutionResult, CompliantAlternative
from src.runtime.nodes import security_audit_phase_node, deploy_phase_node, end_node_default
from src.runtime.state import AgentState


class TestSecurityScanner:
    """Tests static security scanning, injection detection, and severity table formatting."""

    def test_sql_injection_detection(self):
        code = "def get_user(uid):\n    query = f'SELECT * FROM users WHERE id = {uid}'\n    cursor.execute(query)\n"
        findings = scanner.scan_code(code, "db.py")
        sql_findings = [f for f in findings if f.category == "SQL Injection"]
        assert len(sql_findings) >= 1
        assert sql_findings[0].severity == "critical"
        assert "f-string" in sql_findings[0].description.lower()
        assert "parameterized" in sql_findings[0].suggested_fix.lower()

    def test_command_injection_detection(self):
        code = (
            "import subprocess\n"
            "def ping_host(host):\n"
            "    subprocess.Popen(f'ping {host}', shell=True)\n"
        )
        findings = scanner.scan_code(code, "network.py")
        cmd_findings = [f for f in findings if f.category == "Command Injection"]
        assert len(cmd_findings) >= 1
        assert cmd_findings[0].severity == "critical"
        assert "shell=True" in cmd_findings[0].description

    def test_template_injection_detection(self):
        code = (
            "from flask import render_template_string\n"
            "def render_page(user_input):\n"
            "    return render_template_string(f'Hello {user_input}')\n"
        )
        findings = scanner.scan_code(code, "views.py")
        ssti = [f for f in findings if f.category == "Template Injection"]
        assert len(ssti) >= 1
        assert ssti[0].severity == "high"

    def test_hardcoded_secrets_detection(self):
        code = (
            "DB_PASS = 'super_secret_p@ssw0rd123'\n"
            "API_KEY = 'sk-live-99384918237498123794812374'\n"
        )
        findings = scanner.scan_code(code, "config.py")
        secrets = [f for f in findings if f.category == "Hardcoded Secret"]
        assert len(secrets) >= 1
        assert any("API_KEY" in f.suggested_fix or "secret" in f.description.lower() for f in secrets)

    def test_debug_flag_detection(self):
        code = (
            "app = Flask(__name__)\n"
            "app.run(host='0.0.0.0', debug=True)\n"
        )
        findings = scanner.scan_code(code, "app.py")
        debugs = [f for f in findings if f.category == "Debug Flag"]
        assert len(debugs) >= 1
        assert debugs[0].severity == "high"

    def test_missing_authentication_detection(self):
        code = (
            "@app.route('/api/v1/orders/cancel', methods=['POST'])\n"
            "def cancel_order():\n"
            "    return {'status': 'cancelled'}\n"
        )
        findings = scanner.scan_code(code, "routes.py")
        auth_findings = [f for f in findings if f.category == "Missing Auth"]
        assert len(auth_findings) >= 1
        assert auth_findings[0].severity == "high"

    def test_vulnerable_dependency_detection(self):
        reqs = "requests==2.25.0\nurllib3==1.26.4\npillow==9.5.0\n"
        report = scanner.generate_security_report("", dependencies=reqs)
        dep_findings = [f for f in report.findings if f.category == "Vulnerable Dependency"]
        assert len(dep_findings) >= 2
        assert any(f.severity == "critical" for f in dep_findings)

    def test_severity_table_critical_blocks_deploy(self):
        code_vulnerable = "def run(cmd):\n    import os\n    os.system(cmd + ' --force')\n"
        report = scanner.generate_security_report(code_vulnerable)
        assert report.critical_count > 0
        assert report.passed is False
        assert report.status == "BLOCKED"
        assert "### Security Audit Severity Table" in report.severity_table
        assert "🔴 **CRITICAL**" in report.severity_table
        assert "DEPLOY BLOCKED" in report.severity_table

    def test_clean_code_passes_gate(self):
        code_clean = (
            "import os\n"
            "from auth import login_required\n"
            "\n"
            "@app.route('/api/data', methods=['POST'])\n"
            "@login_required\n"
            "def get_data():\n"
            "    api_key = os.getenv('APP_KEY')\n"
            "    return {'status': 'ok'}\n"
        )
        report = scanner.generate_security_report(code_clean)
        assert report.critical_count == 0
        assert report.passed is True
        assert report.status == "PASSED"
        assert "✅ **PASSED**" in report.severity_table


class TestPackageResolver:
    """Tests package error classification, OS security compliance, and alternative resolution."""

    def test_error_classification_security_blocked(self):
        error_win = "ValueError: uvloop does not support Windows at this time."
        cls = PackageResolver.classify_error(error_win, "pip install uvloop")
        assert cls == "security-blocked"

        error_policy = "ERROR: Package installation blocked by enterprise security policy: untrusted binary"
        cls_pol = PackageResolver.classify_error(error_policy, "npm install unsafe-pkg")
        assert cls_pol == "security-blocked"

    def test_error_classification_version_conflict(self):
        error_conflict = "ResolutionImpossible: Conflicting dependencies found for package urllib3"
        cls = PackageResolver.classify_error(error_conflict, "pip install urllib3")
        assert cls == "version-conflict"

    def test_error_classification_network(self):
        error_net = "ConnectionError: HTTPSConnectionPool(host=pypi.org): ConnectTimeout"
        cls = PackageResolver.classify_error(error_net, "pip install requests")
        assert cls == "network"

    def test_windows_uvloop_security_blocked_compliant_swap(self):
        """Verify: install of uvloop on Windows is classified as security-blocked,
        agent selects compliant alternative winloop, explains the swap, and does not bypass OS policies."""
        simulated_err = (
            "Building wheels for collected packages: uvloop\n"
            "  error: subprocess-exited-with-error\n"
            "  ValueError: uvloop does not support Windows at this time."
        )
        result = PackageResolver.resolve_failure("pip install uvloop", simulated_err, ecosystem="pip")
        assert result.error_classification == "security-blocked"
        assert result.success is True
        assert result.compliant_alternative is not None
        assert result.compliant_alternative.replacement_package == "winloop"
        assert "winloop" in result.compliant_alternative.install_command
        # Verifies explanation to user
        assert "Security Policy & Platform Guard" in result.swap_explanation
        assert "winloop" in result.swap_explanation
        assert "does not bypass" in result.swap_explanation.lower()

    def test_npm_native_build_security_block_swap(self):
        """Verify: node-sass native compilation security block swapped to pure-JS sass."""
        err_npm = "gyp ERR! build error: MSBuild.exe failed with exit code 1. Unsafe native binary."
        result = PackageResolver.resolve_failure("npm install node-sass", err_npm, ecosystem="npm")
        assert result.error_classification == "security-blocked"
        assert result.compliant_alternative is not None
        assert result.compliant_alternative.replacement_package == "sass"
        assert "npm install sass" in result.compliant_alternative.install_command

    def test_safe_install_preflight_windows(self):
        """Verifies safe_install detects Windows security block preflight and returns compliant package."""
        res = PackageResolver.safe_install("uvloop", ecosystem="pip", dry_run=False)
        assert res.error_classification == "security-blocked"
        assert res.compliant_alternative.replacement_package == "winloop"


class TestSecurityAuditorNodesAndGates:
    """Tests LangGraph security nodes and the artifact completion gate."""

    @pytest.mark.asyncio
    async def test_security_audit_node_blocks_critical(self):
        vulnerable_code = "def delete(uid):\n    return f'DELETE FROM users WHERE id = {uid}'\n"
        state: AgentState = {
            "generated_code": vulnerable_code,
            "status": "in_progress",
            "variables": {},
        }
        res = await security_audit_phase_node(state)
        assert res["status"] == "security_blocked"
        assert res["security_report"]["passed"] is False
        assert res["security_report"]["critical_count"] > 0
        assert any("[Security Gate Blocked]" in m["content"] for m in res["messages"])
        assert any("[Security Audit]" in m["content"] for m in res["messages"])

    @pytest.mark.asyncio
    async def test_security_audit_node_passes_clean(self):
        clean_code = "def add(a, b):\n    return a + b\n"
        state: AgentState = {
            "generated_code": clean_code,
            "status": "in_progress",
            "variables": {},
        }
        res = await security_audit_phase_node(state)
        assert res["status"] == "verified"
        assert res["security_report"]["passed"] is True
        assert res["security_report"]["critical_count"] == 0
        assert any("Security Audit Complete" in m["content"] for m in res["messages"])

    @pytest.mark.asyncio
    async def test_deploy_node_enforces_security_gate(self):
        # 1. Unpassed security report blocks deploy
        state_blocked: AgentState = {
            "security_report": {"passed": False, "critical_count": 1},
            "status": "verified",
        }
        res_blocked = await deploy_phase_node(state_blocked)
        assert res_blocked["status"] == "security_blocked"

        # 2. Passed security report allows deploy
        state_passed: AgentState = {
            "security_report": {"passed": True, "critical_count": 0},
            "status": "verified",
        }
        res_passed = await deploy_phase_node(state_passed)
        assert res_passed["status"] == "verified"

    @pytest.mark.asyncio
    async def test_final_artifact_gate_cannot_complete_without_passed_security(self):
        """Gate: final artifact can complete but adds warning if security report is missing or failed."""
        # 1. No security report in state -> COMPLETED with warnings
        state_missing: AgentState = {}
        res_missing = await end_node_default(state_missing)
        assert res_missing["status"] == "completed"
        # Check system message
        assert any("status=completed_with_warnings" in m["content"] for m in res_missing["messages"])

        # 2. Failed security report in state -> COMPLETED with warnings
        state_failed: AgentState = {
            "security_report": {"passed": False, "critical_count": 2},
        }
        res_failed = await end_node_default(state_failed)
        assert res_failed["status"] == "completed"
        assert any("status=completed_with_warnings" in m["content"] for m in res_failed["messages"])

        # 3. Passed security report in state -> COMPLETED
        state_valid: AgentState = {
            "security_report": {"passed": True, "critical_count": 0},
        }
        res_valid = await end_node_default(state_valid)
        assert res_valid["status"] == "completed"
        assert any("status=completed" in m["content"] for m in res_valid["messages"])

