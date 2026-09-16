import re
from typing import Any, Dict, List

class SecurityScanner:
    def __init__(self):
        # Known vulnerable dependencies (mock list for demonstration)
        self.vulnerable_deps = {
            "flask": "<=2.0.0",
            "django": "<=3.2.0",
            "requests": "<=2.25.0",
            "urllib3": "<=1.26.4"
        }
        
    def scan_code(self, code: str, filename: str = "snippet.py") -> List[Dict[str, Any]]:
        findings = []
        lines = code.split("\n")
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Simple heuristic for SQL injection in f-strings or format strings
            if re.search(r"(?i)(f['\"].*?(SELECT|INSERT|UPDATE|DELETE)\s+.*?\{.*?\}|(SELECT|INSERT|UPDATE|DELETE)\s+.*?%\s*\(.*?\)|(SELECT|INSERT|UPDATE|DELETE)\s+.*\.format\()", line):
                findings.append({
                    "severity": "critical",
                    "file": filename,
                    "line": line_num,
                    "description": "Potential SQL Injection detected. String formatting used in SQL query.",
                    "suggested_fix": "Use parameterized queries (e.g. execute('... WHERE id=?', (id,))) instead of string formatting."
                })
                
            # 2. Command Injection
            if re.search(r"(os\.system|subprocess\.(Popen|call|run|check_output)).*?shell\s*=\s*True", line):
                findings.append({
                    "severity": "critical",
                    "file": filename,
                    "line": line_num,
                    "description": "Command Injection risk. Shell execution enabled.",
                    "suggested_fix": "Set shell=False and pass arguments as a list."
                })
                
            # Template Injection
            if "render_template_string(" in line:
                findings.append({
                    "severity": "high",
                    "file": filename,
                    "line": line_num,
                    "description": "Server-Side Template Injection (SSTI) risk.",
                    "suggested_fix": "Use render_template() with static template files instead of render_template_string()."
                })
                
            # 3. Hardcoded Secrets
            if re.search(r"(?i)(api_key|password|secret|token)\s*=\s*['\"][a-zA-Z0-9_\-]{8,}['\"]", line):
                findings.append({
                    "severity": "high",
                    "file": filename,
                    "line": line_num,
                    "description": "Hardcoded secret or API key detected.",
                    "suggested_fix": "Load secrets from environment variables (e.g. os.environ.get('SECRET')).",
                })
                
            # 4. Debug Mode Left On
            if re.search(r"(?i)(debug\s*=\s*True|['\"]DEBUG['\"]\s*\]?\s*=\s*True)", line):
                findings.append({
                    "severity": "high",
                    "file": filename,
                    "line": line_num,
                    "description": "Debug mode is enabled, which can leak sensitive environment details.",
                    "suggested_fix": "Set debug=False or use environment variables to configure debug mode conditionally."
                })
                
        # 5. Missing Auth Checks (multi-line heuristic)
        # Look for @app.route without a subsequent @login_required
        route_indices = [i for i, line in enumerate(lines) if "@app.route" in line or "@route" in line]
        for idx in route_indices:
            # Check the next few lines for decorators
            has_auth = False
            for j in range(idx + 1, min(idx + 5, len(lines))):
                if "def " in lines[j]:
                    break
                if "@login_required" in lines[j] or "@jwt_required" in lines[j]:
                    has_auth = True
                    break
            if not has_auth:
                findings.append({
                    "severity": "medium",
                    "file": filename,
                    "line": idx + 1,
                    "description": "Endpoint may be missing authentication checks.",
                    "suggested_fix": "Add @login_required or similar authentication decorator to this endpoint."
                })
                
        # Unsafe dependencies
        for i, line in enumerate(lines):
            match = re.search(r"([a-zA-Z0-9_\-]+)\s*(==|<=|<)\s*([0-9\.]+)", line)
            if match:
                pkg = match.group(1).lower()
                version = match.group(3)
                if pkg in self.vulnerable_deps:
                    findings.append({
                        "severity": "high",
                        "file": filename,
                        "line": i + 1,
                        "description": f"Unsafe dependency version: {pkg} {version} is known to be vulnerable.",
                        "suggested_fix": f"Upgrade {pkg} to a secure version."
                    })

        return findings

    def extract_and_scan(self, markdown_text: str) -> List[Dict[str, Any]]:
        findings = []
        code_blocks = re.findall(r"```(python|bash|sh|txt|)?\n(.*?)```", markdown_text, re.DOTALL)
        
        for lang, code in code_blocks:
            filename = "generated_code.py" if lang == "python" or not lang else "snippet.txt"
            findings.extend(self.scan_code(code, filename))
            
        if not code_blocks:
            findings.extend(self.scan_code(markdown_text, "response.txt"))
            
        return findings

scanner = SecurityScanner()
