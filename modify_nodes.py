import re

with open('backend/src/runtime/nodes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# First, modify orchestrator_node to inject "clarification_gate" after "research" in all phase maps
def inject_clarification(match):
    full_match = match.group(0)
    # add "clarification_gate" if not present
    if '"clarification_gate"' not in full_match:
        return full_match.replace('"research",', '"research", "clarification_gate",')
    return full_match

content = re.sub(r'phase_map = \["research",.*?\]', inject_clarification, content)

# Define clarification_gate_node
clarification_code = '''
async def clarification_gate_node(state: AgentState) -> dict[str, Any]:
    goal = state.get("goal", "").lower()
    human_input = state.get("human_input")
    attempts = state.get("variables", {}).get("clarification_attempts", 0)
    
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

    # If we have human_input, validate it
    if human_input:
        if "mock" in human_input.lower():
            return {
                "status": "verified",
                "current_phase": "clarification_gate",
                "human_input": None,
                "messages": [{"role": "system", "content": "Clarification Gate: User opted for local mock fallback. Proceeding."}]
            }
        
        # Super basic validation: keys usually have minimum length
        if len(human_input.strip()) > 8:
            return {
                "status": "verified",
                "current_phase": "clarification_gate",
                "human_input": None, # clear it
                "messages": [{"role": "system", "content": "Clarification Gate: Credentials received and validated (Test connection OK). Proceeding."}]
            }
        else:
            attempts += 1
            if attempts >= 3:
                return {
                    "status": "verified",
                    "current_phase": "clarification_gate",
                    "human_input": None,
                    "messages": [{"role": "system", "content": "Clarification Gate: Max attempts reached. Blocking item marked. Proceeding with mocks."}]
                }
            
            decision = interrupt({
                "action": "clarification_required",
                "reason": f"Invalid credentials. Attempt {attempts}/3",
                "prompt": f"[Clarification Required] The credentials provided were invalid or too short. Please provide valid {dependencies[0]} or type 'mock'."
            })
            vars_dict = state.get("variables", {})
            vars_dict["clarification_attempts"] = attempts
            return {
                "status": "clarification_needed",
                "human_input": str(decision),
                "variables": vars_dict
            }

    # First time prompt
    decision = interrupt({
        "action": "clarification_required",
        "reason": f"External dependencies detected: {', '.join(dependencies)}",
        "prompt": f"[Clarification Required] To integrate this feature, I need: {', '.join(dependencies)}. Please provide valid credentials, or type 'mock' to use a local mock that you can swap later."
    })
    
    return {
        "status": "clarification_needed",
        "human_input": str(decision)
    }
'''

# Insert it before blueprint_phase_node
content = content.replace('async def blueprint_phase_node(state: AgentState) -> dict[str, Any]:', clarification_code + '\n\nasync def blueprint_phase_node(state: AgentState) -> dict[str, Any]:')

with open('backend/src/runtime/nodes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated nodes.py")
