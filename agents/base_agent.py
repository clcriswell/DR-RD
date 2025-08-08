from __future__ import annotations

from typing import Optional, List, Tuple

from config.feature_flags import RAG_ENABLED, RAG_TOPK, RAG_SNIPPET_TOKENS

try:  # avoid import errors when knowledge package is absent
    from dr_rd.knowledge.retriever import Retriever
    from dr_rd.knowledge.faiss_store import build_default_retriever
except Exception:  # pragma: no cover - fallback when module missing
    Retriever = None  # type: ignore
    build_default_retriever = lambda: None  # type: ignore


class BaseAgent:
    """Base class for role-specific agents."""

    def __init__(
        self,
        name: str,
        model: str,
        system_message: str,
        user_prompt_template: str,
        retriever: Optional[Retriever] = None,
    ):
        self.name = name
        self.model = model
        self.system_message = system_message
        self.user_prompt_template = user_prompt_template
        if RAG_ENABLED and retriever is None:
            try:
                self.retriever: Optional[Retriever] = build_default_retriever()
            except Exception:  # pragma: no cover - best effort
                self.retriever = None
        else:
            self.retriever = retriever

    @staticmethod
    def _truncate_tokens(text: str, max_tokens: int) -> str:
        tokens = text.split()
        if len(tokens) <= max_tokens:
            return text
        return " ".join(tokens[:max_tokens])

    def _augment_prompt(self, prompt: str, context: str) -> str:
        """Attach retrieved snippets to the prompt when RAG is enabled."""
        if not (RAG_ENABLED and self.retriever):
            return prompt
        try:
            hits: List[Tuple[str, str]] = self.retriever.query(context, RAG_TOPK)
        except Exception:
            return prompt
        if not hits:
            return prompt
        bundle_lines = []
        for i, (text, src) in enumerate(hits, 1):
            raw = text.replace("\n", " ")
            snippet = self._truncate_tokens(raw, RAG_SNIPPET_TOKENS)
            bundle_lines.append(f"[{i}] {snippet} ({src})")
        bundle = "\n".join(bundle_lines)
        print(f"[RAG] {self.name} retrieved {len(hits)} snippet(s)")
        return prompt + "\n\nResearch Bundle:\n" + bundle

    def run(self, idea: str, task: str, design_depth: str = "Medium") -> str:
        """Construct the prompt and call the OpenAI API. Returns assistant text."""
        import openai

        # Base prompt from template
        prompt = self.user_prompt_template.format(idea=idea, task=task)

        prompt = self._augment_prompt(prompt, f"{idea}\n{task}")

        # Adjust prompt detail based on design_depth
        design_depth = design_depth.capitalize()  # normalize casing (Low/Medium/High)
        if design_depth == "High":
            prompt += (
                "\n\n**Design Depth: High** – Include all relevant component-level details. "
                "Provide exhaustive technical depth, with complete diagrams, schematics, and trade-off analyses for design decisions."
            )
        elif design_depth == "Low":
            prompt += (
                "\n\n**Design Depth: Low** – Provide a brief high-level overview with minimal technical detail. "
                "Focus on core concepts and avoid deep specifics or extensive diagrams."
            )
        else:  # Medium or default
            prompt += (
                "\n\n**Design Depth: Medium** – Provide a balanced level of detail. "
                "Include key diagrams or specifications and reasoning for major decisions without delving into excessive minutiae."
            )

        # Call OpenAI ChatCompletion with system and user messages
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
