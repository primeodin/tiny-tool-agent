"""Built-in tools the agent can call. Keep them tiny and inspectable."""

from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

# Safe arithmetic only — no names, no attributes, no calls.
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

NOTES = {
    "react": (
        "ReAct = Reason + Act. The model writes a Thought, picks an Action "
        "(tool + input), reads the Observation, then repeats until Final Answer."
    ),
    "tool": (
        "A tool is a function the agent may call. The model never executes code "
        "directly — it names the tool and args; your loop runs it and feeds back "
        "the observation."
    ),
    "observation": (
        "An Observation is the tool's return value pasted back into the transcript. "
        "The next Thought must use it — otherwise the loop is theater."
    ),
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    raise ValueError("only numbers and + - * / // % ** are allowed")


def calc(expression: str) -> str:
    """Evaluate a pure arithmetic expression and return the number as text."""
    expr = expression.strip()
    if not expr:
        return "error: empty expression"
    try:
        tree = ast.parse(expr, mode="eval")
        value = _eval_node(tree)
    except Exception as exc:  # noqa: BLE001 — teach the error surface
        return f"error: {exc}"
    if value == int(value):
        return str(int(value))
    return str(value)


def now(_: str = "") -> str:
    """Return current UTC time as ISO-8601. Mock mode overrides this."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lookup(topic: str) -> str:
    """Look up a short teaching note by keyword."""
    key = topic.strip().lower()
    if not key:
        return "error: empty topic"
    if key in NOTES:
        return NOTES[key]
    for name, body in NOTES.items():
        if key in name or key in body.lower():
            return body
    return f"error: no note for {topic!r}. try: {', '.join(sorted(NOTES))}"


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    fn: Callable[[str], str]


def default_tools(*, clock: Callable[[str], str] | None = None) -> dict[str, Tool]:
    """Registry the agent reads. Swap `clock` in mock mode for a frozen time."""
    tools = [
        Tool("calc", "Arithmetic only. Input: expression like 17 * 24", calc),
        Tool(
            "now",
            "Current UTC time as ISO-8601. Input: ignored (pass -)",
            clock or now,
        ),
        Tool(
            "lookup",
            "Short teaching note. Input: react | tool | observation",
            lookup,
        ),
    ]
    return {t.name: t for t in tools}


_ACTION_RE = re.compile(
    r"^Action:\s*(?P<name>[a-zA-Z_][\w-]*)\s*:\s*(?P<input>.*)$",
    re.MULTILINE,
)
_FINAL_RE = re.compile(r"^Final Answer:\s*(?P<answer>.*)$", re.MULTILINE | re.DOTALL)


def parse_action(text: str) -> tuple[str, str] | None:
    """Pull the first Action: name: input line from a model turn."""
    match = _ACTION_RE.search(text)
    if not match:
        return None
    return match.group("name").strip(), match.group("input").strip()


def parse_final(text: str) -> str | None:
    """Pull Final Answer: ... if the model is done."""
    match = _FINAL_RE.search(text)
    if not match:
        return None
    return match.group("answer").strip()
