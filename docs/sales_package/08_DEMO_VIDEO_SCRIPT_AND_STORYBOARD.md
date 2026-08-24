# ASEP — 3-Minute Demo Video Script & Storyboard
=================================================
Use this script with any screen recording tool (Loom, OBS Studio, ScreenStudio) to produce the investor / buyer walkthrough video.

---

### Scene 1: Introduction & Landing Page (0:00 – 0:30)
* **Visual**: Open `http://localhost:3000`. Scroll smoothly across Hero section, Features Bento Grid, and Live Tech Stack marquee.
* **Audio / Voiceover**:
  > *"Welcome to ASEP — the Autonomous Software Engineering Platform. ASEP is a sovereign, production-grade developer control plane that allows teams to orchestrate autonomous AI agents with full human-in-the-loop governance and isolated execution sandboxes."*

---

### Scene 2: Secure Authentication & Dashboard (0:30 – 1:00)
* **Visual**: Click "Get Started" -> Sign Up / Sign In -> Show Dashboard Overview.
* **Audio / Voiceover**:
  > *"ASEP includes complete enterprise SaaS plumbing out of the box: Argon2id password hashing, RFC 6238 TOTP Multi-Factor Authentication, sliding-window rate limiting, and dynamic quota management. Here in the overview, developers have a unified view of active agent runs, memory indexes, and pending human approvals."*

---

### Scene 3: Live Agent Execution & Interactive PTY Terminal (1:00 – 2:00)
* **Visual**: Navigate to `/sessions` -> Launch an agent task (e.g. "Analyze dependencies and create a health endpoint"). Switch to the live interactive xterm.js terminal.
* **Audio / Voiceover**:
  > *"Unlike simple chat wrappers, ASEP orchestrates a multi-agent DAG powered by LangGraph. Notice the live bidirectional terminal stream — this is a true OS pseudo-terminal session streamed over WebSockets. The agent plans the task, executes shell commands, inspects outputs, and iterates autonomously with Open Policy Agent guardrails."*

---

### Scene 4: Human-in-the-Loop & Monaco Diff Review (2:00 – 2:30)
* **Visual**: Show the `/approvals` screen -> Open the side-by-side Monaco diff viewer showing the agent's code change -> Click "Approve".
* **Audio / Voiceover**:
  > *"Security and control are core to ASEP. When an agent proposes code modifications, the Human-in-the-Loop approval gate pauses execution. Developers can inspect side-by-side git diffs directly in the Monaco editor and approve or reject with one click."*

---

### Scene 5: Monetization & Architecture Close (2:30 – 3:00)
* **Visual**: Navigate to `/billing` -> Show Razorpay plan tiers -> Show terminal showing 199 passing tests.
* **Audio / Voiceover**:
  > *"ASEP is fully monetized with Razorpay payment processing, Qdrant vector memory, Neo4j knowledge graphs, and over 52,000 lines of production code with 199 passing tests and zero copyleft licensing. It is 100% turnkey and ready for immediate deployment."*
