# ASEP — Cloud Cost Model & Unit Economics (COGS)
=================================================

## 1. Operating Cost Breakdown by User Scale

| Scale Tier | Monthly Active Users (MAU) | Database (Neon) | Redis (Upstash) | Vector / Graph DB | Frontend Hosting | Backend Compute | Total Infra Cost / mo | Revenue @ $29/mo (10% conv) | Gross Profit Margin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stage 1 (Bootstrapped)** | 1 – 100 | **$0** (Free) | **$0** (Free) | **$0** (Free) | **$0** (Cloudflare) | **$0** (Render Free) | **$0.00 / mo** | $290 / mo | **97.6%** |
| **Stage 2 (Growth)** | 500 | $19.00 | $10.00 | $25.00 | $0 (Cloudflare) | $25.00 (Render Pro) | **$79.00 / mo** | $1,450 / mo | **94.5%** |
| **Stage 3 (Scale)** | 2,500 | $75.00 | $40.00 | $90.00 | $20 (Cloudflare Pro) | $120.00 (AWS/Fly.io) | **$345.00 / mo** | $7,250 / mo | **95.2%** |
| **Stage 4 (Enterprise)** | 10,000 | $280.00 | $150.00 | $350.00 | $50.00 | $450.00 (K8s Cluster) | **$1,280.00 / mo** | $29,000 / mo | **95.5%** |

---

## 2. LLM Token Economics (Per Active Agent Cycle)

* **Average Autonomous Coding Loop**: 15–20 agent steps.
* **Token Consumption**: ~30k input tokens + ~2.5k output tokens per complex subtask.
* **Cost Per Model**:
  - *Gemini 1.5 Flash / DeepSeek-V3*: **~$0.015 – $0.035** per completed task.
  - *Claude 3.5 Sonnet / GPT-4o*: **~$0.35 – $0.65** per completed task.
  - *Self-Hosted Ollama (Qwen 2.5 Coder / Llama 3.2)*: **$0.00 token cost** (fixed server compute).

---

## 3. Payment Gateway Economics (Razorpay India)
* **Domestic UPI / RuPay**: 0.0% MDR (Zero transaction fee).
* **Domestic Cards / Netbanking**: 2.0% + 18% GST = **2.36% per sale**.
* **International Cards**: 3.0% + 18% GST = **3.54% per sale**.
