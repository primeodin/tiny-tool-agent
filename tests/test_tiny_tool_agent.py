import json
import os

from tiny_tool_agent.agent import run_agent
from tiny_tool_agent.brain import LiveBrain, MockBrain
from tiny_tool_agent.cli import main
from tiny_tool_agent.tools import calc, default_tools, lookup, parse_action, parse_final


def test_calc_integer():
    assert calc("17 * 24") == "408"


def test_calc_rejects_names():
    out = calc("__import__('os').system('echo hi')")
    assert out.startswith("error:")


def test_lookup_react():
    body = lookup("react")
    assert "Reason" in body or "ReAct" in body


def test_lookup_unknown():
    out = lookup("quantum-foam")
    assert out.startswith("error:")
    assert "react" in out


def test_parse_action_and_final():
    turn = "Thought: do math.\nAction: calc: 2 + 2"
    assert parse_action(turn) == ("calc", "2 + 2")
    done = "Thought: done.\nFinal Answer: 4"
    assert parse_final(done) == "4"
    assert parse_action(done) is None


def test_mock_math_run():
    result = run_agent("What is 17 * 24?", mock=True)
    assert result.mock is True
    assert result.answer == "408"
    assert result.tool_calls
    assert result.tool_calls[0]["tool"] == "calc"
    assert "Observation: 408" in result.transcript


def test_mock_time_run():
    result = run_agent("What time is it in UTC?", mock=True)
    assert result.answer == MockBrain.MOCK_NOW
    assert result.tool_calls[0]["tool"] == "now"


def test_mock_lookup_run():
    result = run_agent("What is ReAct tool-calling?", mock=True)
    assert "Reason" in result.answer or "Act" in result.answer
    assert result.tool_calls[0]["tool"] == "lookup"


def test_mock_multi_step():
    result = run_agent("Compute 3 + 5 then times 7", mock=True)
    assert result.answer == "56"
    assert len(result.tool_calls) == 2


def test_cli_mock_math(capsys):
    code = main(["--mock", "What is 17 * 24?"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Action: calc: 17 * 24" in out
    assert "Observation: 408" in out
    assert "[mock] Final Answer: 408" in out


def test_cli_json(capsys):
    code = main(["--mock", "--json", "What is 17 * 24?"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert code == 0
    assert data["answer"] == "408"
    assert data["mock"] is True
    assert data["tool_calls"][0]["tool"] == "calc"


def test_live_brain_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    tools = default_tools()
    brain = LiveBrain(tools, api_key=None)
    try:
        brain.next_turn("hi", "")
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "OPENAI_API_KEY" in str(exc)


def test_run_agent_live_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        run_agent("hi", mock=False)
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "OPENAI_API_KEY" in str(exc)
