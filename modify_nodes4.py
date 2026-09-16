import re
import uuid
import secrets

with open('backend/src/runtime/nodes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. orchestrator_node local secrets
local_secrets_addition = '''
    # Auto-generate local secrets if missing
    local_secrets = state.get("local_secrets", {})
    if not local_secrets:
        import secrets
        local_secrets = {
            "JWT_SECRET": secrets.token_urlsafe(32),
            "SESSION_SECRET": secrets.token_urlsafe(32),
            "DB_PASSWORD": secrets.token_urlsafe(16),
        }
'''
# inject inside orchestrator_node right after goal = state.get("goal", "")
# Wait, let's just replace goal = state.get("goal", "") with the local_secrets block.
content = content.replace('    goal = state.get("goal", "")\n    logger.info("Orchestrator Agent routing goal: %s", goal)', '    goal = state.get("goal", "")\n    logger.info("Orchestrator Agent routing goal: %s", goal)\n' + local_secrets_addition)


# Also we need to inject deploy_clarification_gate right before deploy in all phase_maps.
def inject_deploy_clarification(match):
    full_match = match.group(0)
    if '"deploy_clarification_gate"' not in full_match:
        return full_match.replace(', "deploy"', ', "deploy_clarification_gate", "deploy"')
    return full_match

content = re.sub(r'phase_map = \[.*?\]', inject_deploy_clarification, content)


# 2. Update clarification_gate_node
old_clarification = '''async def clarification_gate_node(state: AgentState) -> dict[str, Any]:
    goal = state.get("goal", "").lower()
    
    # Identify dependencies
    dependencies = []
    if "google login" in goal or "oauth" in goal:
        dependencies.append("Google OAuth Client ID and Secret")
    if "stripe" in goal or "payment" in goal:
        dependencies.append("Stripe Secret Key")
    if "email" in goal or "smtp" in goal:
        dependencies.append("SMTP Credentials or Email API Key")

    if not dependencies:
        return {
            "status": "verified",
            "current_phase": "clarification_gate",
            "messages": [{"role": "system", "content": "Clarification Gate: No external dependencies detected."}]
        }

    clarifications_gathered = {}
    blocked_items = []
    
    for dep in dependencies:
        attempts = 0
        prompt_msg = f"[Clarification Required] To integrate this feature, I need: {dep}. Please provide valid credentials, or type 'mock' to use a local mock that you can swap later."
        
        while attempts < 3:
            decision = interrupt({
                "action": "clarification_required",
                "reason": f"External dependency detected: {dep}",
                "prompt": prompt_msg
            })
            
            human_input = str(decision)
            if "mock" in human_input.lower():
                clarifications_gathered[dep] = "mock"
                break
                
            # Basic validation: minimum length
            if len(human_input.strip()) > 8:
                clarifications_gathered[dep] = human_input
                break
                
            attempts += 1
            if attempts >= 3:
                blocked_items.append(dep)
                break
                
            prompt_msg = f"[Clarification Required] The credentials provided for {dep} were invalid or too short. Attempt {attempts}/3. Please provide valid credentials or type 'mock'."

    msg = f"Clarification Gate Complete. Resolved: {len(clarifications_gathered)}, Blocked: {len(blocked_items)}."
    return {
        "status": "verified",
        "current_phase": "clarification_gate",
        "messages": [{"role": "system", "content": msg}]
    }'''

new_clarification = '''async def clarification_gate_node(state: AgentState) -> dict[str, Any]:
    goal = state.get("goal", "").lower()
    env_mode = state.get("environment_mode", "local")
    credentials_status = state.get("credentials_status", {})
    local_secrets = state.get("local_secrets", {})
    
    # Identify dependencies
    dependencies = []
    if "google login" in goal or "oauth" in goal:
        dependencies.append("Google OAuth Client ID and Secret")
    if "stripe" in goal or "payment" in goal:
        dependencies.append("Stripe Secret Key")
    if "email" in goal or "smtp" in goal:
        dependencies.append("SMTP Credentials or Email API Key")

    if not dependencies:
        return {
            "status": "verified",
            "current_phase": "clarification_gate",
            "local_secrets": local_secrets,
            "messages": [{"role": "system", "content": "Clarification Gate: No external dependencies detected."}]
        }

    clarifications_gathered = credentials_status
    blocked_items = []
    
    # Environment-Aware Credential Policy
    if env_mode == "local":
        # System auto-generates mocks, NEVER asks user for API keys in local mode
        for dep in dependencies:
            clarifications_gathered[dep] = "mock"
        
        msg = f"Clarification Gate Complete [LOCAL MODE]. Auto-mocked {len(dependencies)} external services."
        return {
            "status": "verified",
            "current_phase": "clarification_gate",
            "credentials_status": clarifications_gathered,
            "local_secrets": local_secrets,
            "messages": [{"role": "system", "content": msg}]
        }

    # Deploy Mode (Initial or Switched)
    for dep in dependencies:
        if dep in clarifications_gathered and clarifications_gathered[dep] != "mock":
            continue # already have a real key
            
        attempts = 0
        prompt_msg = f"[Clarification Required] DEPLOY MODE: To integrate this feature in production, I need: {dep}. Please provide valid LIVE credentials, or type 'mock' to deliberately deploy with test services."
        
        while attempts < 3:
            decision = interrupt({
                "action": "clarification_required",
                "reason": f"External production dependency detected: {dep}",
                "prompt": prompt_msg
            })
            
            human_input = str(decision)
            if "mock" in human_input.lower():
                clarifications_gathered[dep] = "mock"
                break
                
            # Basic validation: minimum length
            if len(human_input.strip()) > 8:
                clarifications_gathered[dep] = human_input
                break
                
            attempts += 1
            if attempts >= 3:
                blocked_items.append(dep)
                break
                
            prompt_msg = f"[Clarification Required] The credentials provided for {dep} were invalid or too short. Attempt {attempts}/3. Please provide valid LIVE credentials or type 'mock'."

    msg = f"Clarification Gate Complete. Resolved: {len(clarifications_gathered)}, Blocked: {len(blocked_items)}."
    return {
        "status": "verified",
        "current_phase": "clarification_gate",
        "credentials_status": clarifications_gathered,
        "local_secrets": local_secrets,
        "messages": [{"role": "system", "content": msg}]
    }

async def deploy_clarification_gate_node(state: AgentState) -> dict[str, Any]:
    env_mode = state.get("environment_mode", "local")
    credentials_status = state.get("credentials_status", {})
    
    if env_mode == "local":
        return {
            "status": "verified",
            "current_phase": "deploy_clarification_gate",
            "messages": [{"role": "system", "content": "Deploy Clarification Gate skipped in LOCAL mode."}]
        }

    # Deploy Mode Checklist
    missing_live_keys = [dep for dep, val in credentials_status.items() if val == "mock"]
    if not missing_live_keys:
        return {
            "status": "verified",
            "current_phase": "deploy_clarification_gate",
            "messages": [{"role": "system", "content": "Deploy Clarification Gate: All production keys are present."}]
        }
        
    blocked_items = []
    
    for dep in missing_live_keys:
        attempts = 0
        # Exact prompt requested by user
        prompt_msg = f"[Clarification Required] To deploy with {dep.split()[0].lower()}, I need your {dep.split()[0]} LIVE key ID and secret. Get them from the dashboard ? Settings ? API Keys."
        
        while attempts < 3:
            decision = interrupt({
                "action": "clarification_required",
                "reason": f"Missing production key for: {dep}",
                "prompt": prompt_msg
            })
            
            human_input = str(decision)
            if len(human_input.strip()) > 8 and "mock" not in human_input.lower():
                credentials_status[dep] = human_input
                break
                
            attempts += 1
            if attempts >= 3:
                blocked_items.append(dep)
                break
                
            prompt_msg = f"[Clarification Required] Invalid key for {dep}. Attempt {attempts}/3. Please provide a valid LIVE key."

    if blocked_items:
        # Deploy proceeds only when credential checklist = 100% complete
        return {
            "status": "blocked",
            "current_phase": "deploy_clarification_gate",
            "credentials_status": credentials_status,
            "messages": [{"role": "system", "content": f"DEPLOY BLOCKED. Missing keys: {', '.join(blocked_items)}"}]
        }
        
    return {
        "status": "verified",
        "current_phase": "deploy_clarification_gate",
        "credentials_status": credentials_status,
        "messages": [{"role": "system", "content": "Deploy Clarification Gate: 100% Production keys secured. Swapping .env to production values."}]
    }'''

content = content.replace(old_clarification, new_clarification)

with open('backend/src/runtime/nodes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated nodes.py")
