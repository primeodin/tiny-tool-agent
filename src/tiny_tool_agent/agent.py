"""The ReAct loop itself — brain proposes, tools observe, we stitch the transcript."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiny_tool_agent.brain import Brain, MockBrain
from tiny_tool_agent.tools import Tool, default_tools, parse_action, parse_final


@dataclass
class RunResult:
    answer: str
    transcript: str
    steps: int
    mock: bool
    tool_calls: list[dict[str, str]] = field(default_factory=list)


def run_agent(
    question: str,
    *,
    brain: Brain | None = None,
    tools: dict[str, Tool] | None = None,
    max_steps: int = 6,
    mock: bool = True,
) -> RunResult:
    """Run Thought → Action → Observation until Final Answer or step budget."""
    if mock:
        mock_brain = MockBrain()
        tools = tools or default_tools(clock=lambda _: MockBrain.MOCK_NOW)
        brain = brain or mock_brain
    else:
        tools = tools or default_tools()
        if brain is None:
            from tiny_tool_agent.brain import LiveBrain

            brain = LiveBrain(tools)

    transcript_parts: list[str] = []
    tool_calls: list[dict[str, str]] = []
    answer = ""
    steps = 0

    for step in range(1, max_steps + 1):
        steps = step
        transcript = "\n".join(transcript_parts)
        turn = brain.next_turn(question, transcript).strip()
        transcript_parts.append(turn)

        final = parse_final(turn)
        if final is not None:
            answer = final
            break

        action = parse_action(turn)
        if action is None:
            answer = (
                "error: model turn had neither Action nor Final Answer — "
                f"got:\n{turn}"
            )
            break

        name, tool_input = action
        tool = tools.get(name)
        if tool is None:
            observation = (
                f"error: unknown tool {name!r}. "
                f"available: {', '.join(sorted(tools))}"
            )
        else:
            observation = tool.fn(tool_input)
        tool_calls.append({"tool": name, "input": tool_input, "output": observation})
        transcript_parts.append(f"Observation: {observation}")
    else:
        answer = answer or f"error: hit max_steps={max_steps} without Final Answer"

    return RunResult(
        answer=answer,
        transcript="\n".join(transcript_parts),
        steps=steps,
        mock=mock,
        tool_calls=tool_calls,
    )
