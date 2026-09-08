"""Decide the next Thought/Action/Final Answer — mock script or live LLM."""

from __future__ import annotations

import json
import os
import re
from typing import Protocol

import httpx

from tiny_tool_agent.tools import Tool

SYSTEM = """You are a tiny ReAct agent. Reply with EXACTLY one of these shapes:

Thought: <one short sentence>
Action: <tool_name>: <tool_input>

OR when you have enough observations:

Thought: <one short sentence>
Final Answer: <plain answer>

Tools you may call:
{tool_list}

Rules:
- Never invent Observation lines — the runtime writes those.
- Prefer one tool call per turn.
- Stop with Final Answer as soon as you can answer the question.
"""


class Brain(Protocol):
    def next_turn(self, question: str, transcript: str) -> str: ...


class MockBrain:
    """Deterministic scripted turns keyed off the question text.

    Kept dumb on purpose: readers should see the ReAct loop, not a model.
    """

    MOCK_NOW = "2026-09-08T14:00:00Z"

    def next_turn(self, question: str, transcript: str) -> str:
        q = question.lower()
        steps_done = transcript.count("Observation:")

        if "17" in q and ("24" in q or "twenty" in q or "*" in q or "×" in q):
            if steps_done == 0:
                return (
                    "Thought: I need exact arithmetic, so I will use calc.\n"
                    "Action: calc: 17 * 24"
                )
            return (
                "Thought: The tool returned 408.\n"
                "Final Answer: 408"
            )

        # Multi-tool path before the clock path — "times" must not match "time".
        if "then" in q and ("+" in q or "plus" in q) and ("*" in q or "times" in q):
            if steps_done == 0:
                return (
                    "Thought: First compute the sum inside.\n"
                    "Action: calc: 3 + 5"
                )
            if steps_done == 1:
                return (
                    "Thought: Now multiply that result by 7.\n"
                    "Action: calc: 8 * 7"
                )
            return (
                "Thought: 3+5=8, then 8*7=56.\n"
                "Final Answer: 56"
            )

        if re.search(r"\b(time|clock|utc|date)\b", q) or "day is it" in q:
            if steps_done == 0:
                return (
                    "Thought: I should ask the clock tool.\n"
                    "Action: now: -"
                )
            return (
                f"Thought: The clock says {self.MOCK_NOW}.\n"
                f"Final Answer: {self.MOCK_NOW}"
            )

        if any(w in q for w in ("react", "tool-calling", "tool calling", "observation")):
            topic = "react"
            if "observation" in q:
                topic = "observation"
            elif re.search(r"\btools?\b", q) and "react" not in q:
                topic = "tool"
            if steps_done == 0:
                return (
                    f"Thought: I will look up a short note on {topic}.\n"
                    f"Action: lookup: {topic}"
                )
            # Pull the observation body from the transcript for a grounded final.
            obs = ""
            for line in transcript.splitlines():
                if line.startswith("Observation:"):
                    obs = line[len("Observation:") :].strip()
            return (
                "Thought: I have the teaching note.\n"
                f"Final Answer: {obs}"
            )

        # Default: one lookup on react, then answer honestly that we are in mock.
        if steps_done == 0:
            return (
                "Thought: Default mock path — look up ReAct.\n"
                "Action: lookup: react"
            )
        return (
            "Thought: Mock mode has no better match for this question.\n"
            "Final Answer: [mock] I looked up ReAct. Rephrase with math, time, or "
            "a react/tool/observation question for a tighter script."
        )


class LiveBrain:
    """Thin OpenAI-compatible chat wrapper. Needs OPENAI_API_KEY."""

    def __init__(
        self,
        tools: dict[str, Tool],
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = (
            base_url
            or os.environ.get("OPENAI_BASE_URL")
            or "https://api.openai.com/v1"
        ).rstrip("/")
        self.model = model
        tool_list = "\n".join(
            f"- {t.name}: {t.description}" for t in tools.values()
        )
        self.system = SYSTEM.format(tool_list=tool_list)

    def next_turn(self, question: str, transcript: str) -> str:
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required unless you pass --mock "
                "(or set OPENAI_BASE_URL for a local OpenAI-compatible server)."
            )
        user = f"Question: {question}\n\nTranscript so far:\n{transcript or '(empty)'}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                content=json.dumps(payload),
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
