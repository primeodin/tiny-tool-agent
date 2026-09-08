# Contributing to tiny-tool-agent

Welcome. This repo is a **day-4 teaching ReAct agent** — Thought → Action → Observation → Final Answer. Keep that bar in mind.

## Map (fork → PR)

1. **Fork** this repo on GitHub, then clone your fork:
   ```bash
   git clone https://github.com/<you>/tiny-tool-agent.git
   cd tiny-tool-agent
   ```
2. **Install** in editable mode with test deps:
   ```bash
   pip install -e ".[dev]"
   ```
3. **Prove the wiring** before you change anything:
   ```bash
   pytest
   python -m tiny_tool_agent --mock "What is 17 * 24?"
   ```
   You want `13 passed` and a transcript that shows `Action: calc: 17 * 24`, `Observation: 408`, then `[mock] Final Answer: 408`. No API key needed.
4. **Branch** for one small change:
   ```bash
   git checkout -b my-first-pr
   ```
5. **Ship** a focused PR back to `primeodin/tiny-tool-agent`:
   - one idea per PR
   - include or update a test when behavior changes
   - say what you ran (`pytest`, the mock question)

## Add a tool

1. Implement the function in `src/tiny_tool_agent/tools.py` and register it in `default_tools`.
2. Extend `MockBrain` in `src/tiny_tool_agent/brain.py` with a scripted path for one question that needs that tool.
3. Add a test under `tests/` that fails without your tool and passes with it.
4. Add one row to the README tools table.

Keep the string convention: `Action: name: input`. The loop parses that — do not invent a second protocol.

## Good first issues

Scoped tickets (file named in the issue body):

- [#1 — `unit_convert` tool (C↔F) + mock path](https://github.com/primeodin/tiny-tool-agent/issues/1)
- [#2 — `--trace` flag numbering each Thought/Action/Observation](https://github.com/primeodin/tiny-tool-agent/issues/2)

Claim one with a comment, ask questions in the thread, then open the PR. Docs count.

## Shop rules

- **Keep it small.** No LangChain / AutoGPT pile-ons, no extra services "while we're here."
- **Mock stays sacred.** Offline tests and `--mock` must keep working without secrets.
- **Observation is truth.** If the tool lies, later Thoughts inherit the lie — fix the tool, don't yell at the model.
- **Teach by running.** Prefer a mock path + a test over a theory dump.
- **Match the voice.** Short, concrete, honest — shop notes, not pitch decks.

## What to skip

Please don't open PRs that:

- add a heavy agent/framework stack
- require paid APIs in the default path
- rewrite the README for marketing tone
- bundle unrelated refactors with a feature

Questions? Comment on the issue you're claiming — that thread is the right place.
