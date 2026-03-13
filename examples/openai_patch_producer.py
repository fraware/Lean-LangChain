"""OpenAI-backed CandidateProducer: uses OpenAI API to propose a patch from context. Requires OPENAI_API_KEY."""

from __future__ import annotations

import os

from obligation_runtime_orchestrator.producer import ProducerContext


class OpenAIPatchProducer:
    """Propose a patch by calling OpenAI with diagnostics/goals and file context."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self._model = model

    def propose_patch(self, context: ProducerContext) -> dict[str, str]:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError("OpenAI producer requires: pip install openai") from e
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {}
        client = OpenAI(api_key=api_key)
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
            resp = client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = (resp.choices[0].message.content or "").strip()
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

