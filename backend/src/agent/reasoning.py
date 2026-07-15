"""
ASEP — Reasoning Engine

Lightweight goal enrichment and planner prompt assembly.
Contains ZERO LLM calls — pure deterministic string transformation.
"""

from src.agent.context_builder import ContextSnapshot


class ReasoningEngine:
    """Transforms a raw user goal + context snapshot into a richer Planner input.

    Design constraints:
      - No LLM calls.
      - No self-improvement or reflection loops.
      - Deterministic: same inputs always produce the same output.
    """

    def enrich_goal(self, raw_goal: str, context: ContextSnapshot) -> str:
        """Append relevant context facts to the raw goal to give the Planner richer input."""
        sections: list[str] = [f"Goal: {raw_goal}"]

        if context.relevant_concepts:
            facts = [
                c.get("content") or c.get("text") or str(c)
                for c in context.relevant_concepts[:3]
            ]
            sections.append("Relevant knowledge:\n" + "\n".join(f"- {f}" for f in facts if f))

        if context.relevant_procedures:
            procs = [
                p.get("name") or p.get("title") or str(p)
                for p in context.relevant_procedures[:2]
            ]
            sections.append("Applicable procedures:\n" + "\n".join(f"- {p}" for p in procs if p))

        if context.available_tools:
            tools = [t["name"] for t in context.available_tools[:5]]
            sections.append("Available tools: " + ", ".join(tools))

        return "\n\n".join(sections)

    def build_planner_prompt(self, enriched_goal: str, context: ContextSnapshot) -> str:
        """Assemble the full structured prompt string consumed by the Planner provider."""
        recent = ""
        if context.recent_episodes:
            ep = context.recent_episodes[0]
            summary = ep.get("summary") or ep.get("content") or ""
            if summary:
                recent = f"\nMost recent prior activity: {summary}"

        return (
            f"{enriched_goal}"
            f"{recent}\n\n"
            "Decompose this goal into a structured execution plan."
        )
