import re

with open('backend/src/runtime/nodes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# First, modify orchestrator_node to inject "clarification_gate" after "research" in all phase maps
def inject_clarification(match):
    full_match = match.group(0)
    if '"clarification_gate"' not in full_match:
        return full_match.replace('"research",', '"research", "clarification_gate",')
    return full_match

content = re.sub(r'phase_map = \["research",.*?\]', inject_clarification, content)

clarification_code = '''
async def clarification_gate_node(state: AgentState) -> dict[str, Any]:
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
    }
'''

content = content.replace('async def blueprint_phase_node(state: AgentState) -> dict[str, Any]:', clarification_code + '\n\nasync def blueprint_phase_node(state: AgentState) -> dict[str, Any]:')

with open('backend/src/runtime/nodes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated nodes.py")
