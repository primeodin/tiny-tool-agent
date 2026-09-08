"""CLI entry — question in, ReAct transcript + Final Answer out."""

from __future__ import annotations

import argparse
import json
import sys

from tiny_tool_agent.agent import run_agent


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tiny-tool-agent",
        description="Tiny ReAct tool-calling agent (mock-first).",
    )
    p.add_argument("question", nargs="+", help="Question to answer")
    p.add_argument(
        "--mock",
        action="store_true",
        help="Use the scripted mock brain (no API key). Default if no key needed for tests.",
    )
    p.add_argument(
        "--live",
        action="store_true",
        help="Call an OpenAI-compatible chat API (needs OPENAI_API_KEY).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print machine-readable answer + transcript + tool_calls",
    )
    p.add_argument(
        "--max-steps",
        type=int,
        default=6,
        help="Max Thought/Action turns before stopping (default 6)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    question = " ".join(args.question)
    mock = not args.live
    if args.mock:
        mock = True
    if args.live and args.mock:
        print("pick one of --mock or --live, not both", file=sys.stderr)
        return 2

    try:
        result = run_agent(question, mock=mock, max_steps=args.max_steps)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.as_json:
        payload = {
            "answer": result.answer,
            "mock": result.mock,
            "steps": result.steps,
            "tool_calls": result.tool_calls,
            "transcript": result.transcript,
        }
        print(json.dumps(payload, indent=2))
        return 0

    # Print the working transcript without the trailing Final Answer line,
    # then emit one clear Final Answer (mock-tagged when scripted).
    lines = []
    for line in result.transcript.splitlines():
        if line.startswith("Final Answer:"):
            continue
        lines.append(line)
    print("\n".join(lines).rstrip())
    print()
    prefix = "[mock] " if result.mock else ""
    print(f"{prefix}Final Answer: {result.answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
