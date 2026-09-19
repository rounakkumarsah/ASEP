"""
ASEP — Security Scanner & Auditor Engine
========================================
Performs deep static analysis across generated source code and dependencies.
Detects:
1. Injection (SQL, Command, Template/SSTI)
2. Hardcoded Secrets & Credentials
3. Debug Mode Flags in Production
4. Missing Authentication on Resource Endpoints
5. Dependency Vulnerabilities against CVE Advisories

Generates severity tables and strictly gates deployment on CRITICAL findings.
"""

from __future__ import annotations

import ast
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    """Structured security vulnerability or policy violation."""
    id: str
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "SQL Injection", "Command Injection", "Template Injection", "Hardcoded Secret", "Debug Flag", "Missing Auth", "Vulnerable Dependency"
    file: str
    line: int
    description: str
    suggested_fix: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity.lower(),
            "category": self.category,
            "file": self.file,
            "line": self.line,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class SecurityReport:
    """Comprehensive security audit outcome for a codebase or artifact."""
    passed: bool
    status: str  # "PASSED" | "BLOCKED"
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_findings: int
    findings: list[SecurityFinding] = field(default_factory=list)
    severity_table: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "total_findings": self.total_findings,
            "findings": [f.to_dict() for f in self.findings],
            "severity_table": self.severity_table,
        }


class SecurityScanner:
    """Security scanner with injection, secret, debug, auth, and CVE dependency checks."""

    # Known vulnerable dependencies and CVE advisory thresholds
    VULNERABLE_DEPENDENCIES: dict[str, dict[str, Any]] = {
        # Python
        "requests": {
            "max_vulnerable": "2.31.0",
            "severity": "high",
            "cve": "CVE-2023-32681",
            "desc": "Unintended leak of Proxy-Authorization headers across redirects",
            "fix": "Upgrade requests to >=2.31.0",
        },
        "urllib3": {
            "max_vulnerable": "1.26.18",
            "severity": "critical",
            "cve": "CVE-2023-45803",
            "desc": "Cookie leak and request body clearing vulnerabilities",
            "fix": "Upgrade urllib3 to >=1.26.18 or >=2.0.7",
        },
        "flask": {
            "max_vulnerable": "2.2.5",
            "severity": "high",
            "cve": "CVE-2023-30861",
            "desc": "High vulnerability in cookie handling and session validation",
            "fix": "Upgrade flask to >=2.3.0",
        },
        "django": {
            "max_vulnerable": "3.2.20",
            "severity": "critical",
            "cve": "CVE-2023-36053",
            "desc": "SQL injection and potential ReDoS in EmailValidator",
            "fix": "Upgrade django to >=4.2.4",
        },
        "pillow": {
            "max_vulnerable": "10.0.1",
            "severity": "critical",
            "cve": "CVE-2023-4863",
            "desc": "Heap buffer overflow in WebP image processing (RCE risk)",
            "fix": "Upgrade pillow to >=10.0.1",
        },
        "pyyaml": {
            "max_vulnerable": "5.4.1",
            "severity": "critical",
            "cve": "CVE-2020-14343",
            "desc": "Arbitrary code execution through yaml.load() without SafeLoader",
            "fix": "Upgrade pyyaml to >=6.0.1 and use yaml.safe_load()",
        },
        "jinja2": {
            "max_vulnerable": "3.1.3",
            "severity": "high",
            "cve": "CVE-2024-22195",
            "desc": "Server-side template injection and HTML attribute injection",
            "fix": "Upgrade jinja2 to >=3.1.4",
        },
        "cryptography": {
            "max_vulnerable": "41.0.6",
            "severity": "high",
            "cve": "CVE-2023-49083",
            "desc": "Null pointer dereference when loading PKCS7 certificates",
            "fix": "Upgrade cryptography to >=42.0.0",
        },
        "aiohttp": {
            "max_vulnerable": "3.9.2",
            "severity": "critical",
            "cve": "CVE-2024-23334",
            "desc": "Directory traversal vulnerability in static file serving",
            "fix": "Upgrade aiohttp to >=3.9.3",
        },
        # Node.js
        "lodash": {
            "max_vulnerable": "4.17.21",
            "severity": "critical",
            "cve": "CVE-2021-23337",
            "desc": "Command injection via template function and prototype pollution",
            "fix": "Upgrade lodash to >=4.17.21 or migrate to native ES methods",
        },
        "axios": {
            "max_vulnerable": "0.21.2",
            "severity": "critical",
            "cve": "CVE-2020-28168",
            "desc": "SSRF and confidential header leakage during redirects",
            "fix": "Upgrade axios to >=1.6.0",
        },
        "jsonwebtoken": {
            "max_vulnerable": "9.0.0",
            "severity": "critical",
            "cve": "CVE-2022-23529",
            "desc": "Remote code execution through insecure key object parsing",
            "fix": "Upgrade jsonwebtoken to >=9.0.2",
        },
    }

    def __init__(self) -> None:
        self._counter = 1

    def _next_id(self) -> str:
        fid = f"SEC-{self._counter:03d}"
        self._counter += 1
        return fid

    def scan_code(self, code: str, filename: str = "main.py") -> list[SecurityFinding]:
        """Performs static security analysis on source code."""
        findings: list[SecurityFinding] = []
        lines = code.splitlines()

        # 1. Line-by-line regex and pattern heuristics
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()

            # --- A. SQL INJECTION (CRITICAL) ---
            # Checks for raw f-strings, % formatting, or string concat in SQL queries
            sql_keywords = r"(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|DROP\s+TABLE|ALTER\s+TABLE)"
            if re.search(rf"(?i)f['\"].*?{sql_keywords}.*?\{{.*?\}}", stripped):
                findings.append(SecurityFinding(
                    id=self._next_id(),
                    severity="critical",
                    category="SQL Injection",
                    file=filename,
                    line=line_num,
                    description="Critical SQL Injection: Unsanitized f-string formatting in SQL query.",
                    suggested_fix="Use parameterized queries (e.g. execute('... WHERE id = ?', (id,))) instead of f-strings."
                ))
            elif re.search(rf"(?i)(cursor\.execute|db\.query|session\.execute)\(.*(%|\.format\()", stripped):
                findings.append(SecurityFinding(
                    id=self._next_id(),
                    severity="critical",
                    category="SQL Injection",
                    file=filename,
                    line=line_num,
                    description="Potential SQL Injection: String concatenation or % formatting passed to SQL execute().",
                    suggested_fix="Bind parameters safely using SQL query placeholders: execute(query, (params,))."
                ))

            # --- B. COMMAND INJECTION (CRITICAL) ---
            if re.search(r"\bos\.system\s*\(", stripped) or re.search(r"(subprocess\.(Popen|call|run|check_output)).*?shell\s*=\s*True", stripped):
                findings.append(SecurityFinding(
                    id=self._next_id(),
                    severity="critical",
                    category="Command Injection",
                    file=filename,
                    line=line_num,
                    description="Critical Command Injection: Process executed with shell=True on unvalidated input.",
                    suggested_fix="Set shell=False and pass arguments as an explicit sanitized list of strings."
                ))
            elif re.search(r"\b(eval|exec)\s*\((?!['\"][^'\"]*['\"])", stripped) and not stripped.startswith("#"):
                findings.append(SecurityFinding(
                    id=self._next_id(),
                    severity="critical",
                    category="Command Injection",
                    file=filename,
                    line=line_num,
                    description="Arbitrary Code Execution: Dynamic eval() or exec() invoked on variable expression.",
                    suggested_fix="Avoid dynamic eval/exec. Use ast.literal_eval for safe literal data parsing."
                ))

            # --- C. TEMPLATE INJECTION / SSTI (HIGH) ---
            if "render_template_string(" in stripped:
                findings.append(SecurityFinding(
                    id=self._next_id(),
                    severity="high",
                    category="Template Injection",
                    file=filename,
                    line=line_num,
                    description="Server-Side Template Injection (SSTI): Dynamic template string rendered directly.",
                    suggested_fix="Use static template files via render_template() instead of dynamic string templates."
                ))

            # --- D. HARDCODED SECRETS (HIGH / CRITICAL) ---
            if re.search(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", stripped):
                findings.append(SecurityFinding(
                    id=self._next_id(),
                    severity="critical",
                    category="Hardcoded Secret",
                    file=filename,
                    line=line_num,
                    description="Critical Secret Exposure: Unencrypted private key found directly in source code.",
                    suggested_fix="Remove private key from source. Inject via secure secret manager or environment variable."
                ))
            elif re.search(r"(?i)(api[_-]?key|secret[_-]?key|password|pass|db_pass|jwt[_-]?secret|auth[_-]?token)\s*=\s*['\"][^'\"]{8,}['\"]", stripped):
                # Don't flag dummy/placeholder tokens
                val_match = re.search(r"=\s*['\"]([^'\"]+)['\"]", stripped)
                val = val_match.group(1).lower() if val_match else ""
                if not any(placeholder in val for placeholder in ("placeholder", "test", "your_", "dummy", "example")):
                    findings.append(SecurityFinding(
                        id=self._next_id(),
                        severity="high",
                        category="Hardcoded Secret",
                        file=filename,
                        line=line_num,
                        description="Hardcoded Secret: Sensitive credential, password, or API token detected in code.",
                        suggested_fix="Load credentials dynamically from environment variables (e.g. os.environ['SECRET_KEY'])."
                    ))

            # --- E. DEBUG FLAGS IN PRODUCTION (HIGH) ---
            if re.search(r"(?i)(debug\s*=\s*True|['\"]DEBUG['\"]\s*\]?\s*=\s*True|app\.run\(.*?debug\s*=\s*True)", stripped):
                findings.append(SecurityFinding(
                    id=self._next_id(),
                    severity="high",
                    category="Debug Flag",
                    file=filename,
                    line=line_num,
                    description="Debug Mode Enabled: Exposing debug stack traces and interactive consoles in production.",
                    suggested_fix="Set debug=False or toggle conditionally using os.getenv('DEBUG', 'False').lower() == 'true'."
                ))

        # --- F. MISSING AUTHENTICATION ON ENDPOINTS (HIGH / MEDIUM) ---
        route_indices = [
            i for i, line in enumerate(lines)
            if re.search(r"@(app|router|api)\.(route|post|put|delete|patch)\(", line)
        ]
        for idx in route_indices:
            route_line = lines[idx].strip()
            # Check if this route modifies state or accesses sensitive paths
            is_mutation = any(m in route_line.lower() for m in ("post", "put", "delete", "patch", "admin", "settings", "users", "delete"))
            has_auth = False
            for j in range(idx + 1, min(idx + 6, len(lines))):
                candidate = lines[j].strip()
                if candidate.startswith("def ") or candidate.startswith("async def "):
                    if "Depends(" in candidate and any(k in candidate for k in ("auth", "user", "token", "login")):
                        has_auth = True
                    break
                if any(decorator in candidate for decorator in ("@login_required", "@jwt_required", "@auth_required", "@require_auth", "@permission_required")):
                    has_auth = True
                    break

            if not has_auth and is_mutation:
                findings.append(SecurityFinding(
                    id=self._next_id(),
                    severity="high",
                    category="Missing Auth",
                    file=filename,
                    line=idx + 1,
                    description="Missing Authentication: Modifying API route endpoint lacks auth decorator or guard dependency.",
                    suggested_fix="Protect endpoint with authentication decorator (@login_required, @jwt_required) or security dependency."
                ))

        # --- G. DEPENDENCY CHECKS IN CODE / REQUIREMENTS ---
        findings.extend(self._scan_dependencies(code, filename))

        return findings

    def _scan_dependencies(self, text: str, filename: str) -> list[SecurityFinding]:
        """Scans dependency declarations or import requirements against known CVE database."""
        dep_findings: list[SecurityFinding] = []
        lines = text.splitlines()

        for i, line in enumerate(lines):
            line_num = i + 1
            # Matches: requests==2.25.0 or flask<=2.0.0 or "lodash": "^4.17.15"
            py_match = re.search(r"^([a-zA-Z0-9_\-]+)\s*(==|<=|~=|<)\s*([0-9\.]+)", line.strip())
            js_match = re.search(r"['\"]([a-zA-Z0-9_\-]+)['\"]\s*:\s*['\"][\^~]?([0-9\.]+)['\"]", line.strip())

            pkg = None
            ver = None
            if py_match:
                pkg = py_match.group(1).lower()
                ver = py_match.group(3)
            elif js_match:
                pkg = js_match.group(1).lower()
                ver = js_match.group(2)

            if pkg and ver and pkg in self.VULNERABLE_DEPENDENCIES:
                adv = self.VULNERABLE_DEPENDENCIES[pkg]
                if self._version_is_vulnerable(ver, adv["max_vulnerable"]):
                    dep_findings.append(SecurityFinding(
                        id=self._next_id(),
                        severity=adv["severity"],
                        category="Vulnerable Dependency",
                        file=filename,
                        line=line_num,
                        description=f"Vulnerable Dependency '{pkg} {ver}': {adv['cve']} - {adv['desc']}.",
                        suggested_fix=adv["fix"],
                    ))

        return dep_findings

    @staticmethod
    def _version_is_vulnerable(detected: str, max_vulnerable: str) -> bool:
        """Compares numeric version tuples."""
        try:
            d_parts = [int(p) for p in re.findall(r"\d+", detected)[:3]]
            m_parts = [int(p) for p in re.findall(r"\d+", max_vulnerable)[:3]]
            while len(d_parts) < 3:
                d_parts.append(0)
            while len(m_parts) < 3:
                m_parts.append(0)
            return tuple(d_parts) <= tuple(m_parts)
        except Exception:
            return detected == max_vulnerable

    def generate_security_report(
        self,
        code_or_files: str | dict[str, str],
        dependencies: str | list[str] | dict[str, str] | None = None,
    ) -> SecurityReport:
        """Generates complete security audit report and markdown severity table."""
        self._counter = 1
        all_findings: list[SecurityFinding] = []

        if isinstance(code_or_files, str):
            all_findings.extend(self.scan_code(code_or_files, filename="main.py"))
        elif isinstance(code_or_files, dict):
            for fname, content in code_or_files.items():
                all_findings.extend(self.scan_code(content, filename=fname))

        if dependencies:
            if isinstance(dependencies, str):
                all_findings.extend(self._scan_dependencies(dependencies, "requirements.txt"))
            elif isinstance(dependencies, list):
                all_findings.extend(self._scan_dependencies("\n".join(dependencies), "requirements.txt"))
            elif isinstance(dependencies, dict):
                dep_text = "\n".join(f"{k}=={v}" for k, v in dependencies.items())
                all_findings.extend(self._scan_dependencies(dep_text, "requirements.txt"))

        # Deduplicate findings
        seen = set()
        unique_findings = []
        for f in all_findings:
            key = (f.category, f.file, f.line, f.description)
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        crit_count = sum(1 for f in unique_findings if f.severity.lower() == "critical")
        high_count = sum(1 for f in unique_findings if f.severity.lower() == "high")
        med_count = sum(1 for f in unique_findings if f.severity.lower() == "medium")
        low_count = sum(1 for f in unique_findings if f.severity.lower() == "low")

        passed = crit_count == 0
        status = "PASSED" if passed else "BLOCKED"

        table = self._build_severity_table(unique_findings, status, crit_count)

        return SecurityReport(
            passed=passed,
            status=status,
            critical_count=crit_count,
            high_count=high_count,
            medium_count=med_count,
            low_count=low_count,
            total_findings=len(unique_findings),
            findings=unique_findings,
            severity_table=table,
        )

    def _build_severity_table(self, findings: list[SecurityFinding], status: str, crit_count: int) -> str:
        """Builds Markdown severity table for execution logs and report display."""
        lines = [
            "### Security Audit Severity Table",
            "",
            "| ID | Severity | Category | Location | Description | Remediation |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        badge_map = {
            "critical": "🔴 **CRITICAL**",
            "high": "🟠 **HIGH**",
            "medium": "🟡 **MEDIUM**",
            "low": "🔵 **LOW**",
        }

        if not findings:
            lines.append("| — | 🟢 **CLEAN** | None | Global | No security vulnerabilities detected | Ready for deployment |")
        else:
            for f in findings:
                badge = badge_map.get(f.severity.lower(), f.severity.upper())
                loc = f"`{f.file}:{f.line}`"
                # Clean description of markdown table pipes
                clean_desc = f.description.replace("|", "-")
                clean_fix = f.suggested_fix.replace("|", "-")
                lines.append(f"| {f.id} | {badge} | {f.category} | {loc} | {clean_desc} | {clean_fix} |")

        lines.append("")
        if crit_count > 0:
            lines.append(
                f"**Audit Status:** ⛔ **DEPLOY BLOCKED** — {crit_count} CRITICAL vulnerability detected. "
                "All CRITICAL security flaws must be remediated before production deployment."
            )
        else:
            lines.append(
                "**Audit Status:** ✅ **PASSED** — 0 Critical vulnerabilities detected. Code is approved for deployment."
            )

        return "\n".join(lines)


# Global singleton scanner instance
scanner = SecurityScanner()


def secure_filename(filename: str) -> str:
    """Sanitize a filename by removing unsafe characters and path traversal segments."""
    import os
    import unicodedata
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")
    for sep in [os.path.sep, os.path.altsep]:
        if sep:
            filename = filename.replace(sep, " ")
    filename = "_".join(re.findall(r"[\w.-]+", filename)).strip("._")
    return filename or "document"
