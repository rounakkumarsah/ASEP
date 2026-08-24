# ASEP — Tool Permission Matrix & MCP Security Specification
**Document ID:** ASEP-SEC-028  
**Classification:** Enterprise Security & Governance  
**Author:** Rounak Kumar Sah  
**Status:** Approved & Enforced  

---

## 1. Tool Permission Hierarchy

ASEP implements strict least-privilege role-based access control (RBAC) across all agent tools. No tool is granted blanket host execution privileges.

| Tool Name | Tool Category | Required Permission | Dangerous / Destructive? | Sandboxed? | Human Approval Required? |
|---|---|---|---|---|---|
| `filesystem` | `FILESYSTEM` | `ToolPermission.FILESYSTEM` | **Yes (Write/Delete)** | Path Jailed (`WORKSPACE_ROOT`) | Optional on Read; Enforced on Write |
| `terminal` | `SYSTEM` | `ToolPermission.EXECUTE` | **Yes (Command Exec)** | Docker Non-Root (`1000:1000`) | **Mandatory for all shell commands** |
| `web_search` | `NETWORK` | `ToolPermission.NETWORK` | No (Read-Only) | Outbound HTTPS Jailed | No |
| `git_clone` | `VERSION_CONTROL`| `ToolPermission.NETWORK` | No (Read-Only) | Outbound HTTPS | No |
| `git_commit`| `VERSION_CONTROL`| `ToolPermission.EXECUTE` | Yes (State Mutating) | Container Jailed | **Mandatory** |
| `mcp_tool` | `INTEGRATION` | `ToolPermission.INTEGRATION` | Dynamic Schema | Validated by Registry | Based on Tool Metadata Flag |

---

## 2. Model Context Protocol (MCP) Safety Invariants

1. **Schema Validation:** Every tool definition exposed via MCP is validated against JSON Schema specifications before invocation.
2. **Permission Boundary:** An agent cannot self-grant permissions. Tool invocations outside the assigned session role permissions are rejected by `ToolRouter`.
3. **Execution Sandbox:** Command execution tools route through Docker containers with `cap_drop=["ALL"]` and `read_only=True` root filesystems.
