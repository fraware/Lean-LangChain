"""Anthropic-backed CandidateProducer: uses Anthropic API to propose a patch from context. Requires ANTHROPIC_API_KEY."""

from __future__ import annotations

import os

from obligation_runtime_orchestrator.producer import ProducerContext


class AnthropicPatchProducer:
    """Propose a patch by calling Anthropic with diagnostics/goals and file context."""

    def __init__(self, model: str = "claude-3-5-haiku-20241022") -> None:
        self._model = model

    def propose_patch(self, context: ProducerContext) -> dict[str, str]:
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise ImportError("Anthropic producer requires: pip install anthropic") from e
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {}
        client = Anthropic(api_key=api_key)
        file_path = context.get("file_path") or "Main.lean"
        diagnostics = context.get("diagnostics") or []
        goals = context.get("goals") or []
        prompt = (
            "You are helping fix a Lean 4 file. Return only the complete file content for the path given, "
            "no explanation. Fix any errors indicated by diagnostics or goals.\n"
            f"File path: {file_path}\n"
        )
        if diagnostics:
            prompt += f"Diagnostics: {diagnostics}\n"
        if goals:
            prompt += f"Goals: {goals}\n"
        prompt += "Return the full corrected Lean file content:"
        try:
            msg = client.messages.create(
                model=self._model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text if msg.content else ""
            content = text.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)
            return {file_path: content} if content else {}
        except Exception:
            return {}
