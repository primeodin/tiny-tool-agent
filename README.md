# tiny-tool-agent

> Day-4 of PrimeOdin’s daily public builds — a tiny ReAct tool-calling agent with no framework soup.

**Thought → Action → Observation → Final Answer.** The model proposes; your loop runs the tool; the next thought has to use the observation. That is the whole trick.

## 60-second start

```bash
git clone https://github.com/primeodin/tiny-tool-agent.git
cd tiny-tool-agent
pip install -e ".[dev]"
pytest
python -m tiny_tool_agent --mock "What is 17 * 24?"
python -m tiny_tool_agent --mock --json "What time is it in UTC?"
```

**Expected stdout** (deterministic on `--mock` — yours should match):

```text
# pytest
.............                                                            [100%]
13 passed

# mock math
Thought: I need exact arithmetic, so I will use calc.
Action: calc: 17 * 24
Observation: 408
Thought: The tool returned 408.

[mock] Final Answer: 408

# mock time (JSON)
{
  "answer": "2026-09-08T14:00:00Z",
  "mock": true,
  "steps": 2,
  "tool_calls": [
    {
      "tool": "now",
      "input": "-",
      "output": "2026-09-08T14:00:00Z"
    }
  ],
  ...
}
```

If the Action line or `408` drifts, the mock script or the calc tool changed — open an issue before "fixing" the loop by eye.

## Why ReAct is the right mid-level look

Chat alone is a parrot. Tools alone are a CLI. **ReAct** is the bridge: the model writes a short Thought, names a tool, your runtime executes it, and the Observation lands back in the transcript so the next Thought is grounded.

Three mysteries go away once you run this loop yourself:

- why "agents" are mostly a while-loop with string conventions
- why tool schemas matter more than prompt poetry
- why a bad Observation poisons every later Thought

## The whole loop, in five lines

1. Ask the brain for the next turn given the question + transcript so far.
2. If it wrote `Final Answer:`, stop and print it.
3. If it wrote `Action: name: input`, look up that tool.
4. Run the tool. Append `Observation: <result>` to the transcript.
5. Repeat until the answer or you hit the step budget.

```text
Question
   |
   v
Thought ----> Action: name: input ----> Tool runs ----> Observation
   ^                                                   |
   +------------- loop (append Observation) -----------+
   |
   v
Final Answer
```

Shop rule: the Thought is cheap talk until an Observation lands. If the Observation is wrong, every later Thought inherits the lie — fix the tool, don't yell at the model.

## Built-in tools

| Tool | Input | Job |
| --- | --- | --- |
| `calc` | `17 * 24` | Safe arithmetic AST eval — no names, no imports |
| `now` | `-` | UTC ISO-8601 (frozen in `--mock`) |
| `lookup` | `react` / `tool` / `observation` | Tiny teaching notes |

## Change one thing

1. Add a tool (weather stub, unit converter) in `tools.py` and register it in `default_tools`  
2. Extend `MockBrain` with a scripted path for your new question  
3. Swap `--mock` for `--live` when you have an `OPENAI_API_KEY` (or point `OPENAI_BASE_URL` at Ollama)

## Real model (optional)

```bash
export OPENAI_API_KEY=sk-...
# optional: export OPENAI_BASE_URL=http://localhost:11434/v1
python -m tiny_tool_agent --live "What is 19 * 21?"
```

## What you just built

| Piece | Job |
| --- | --- |
| `tools.py` | `calc` / `now` / `lookup` + Action/Final parsers |
| `brain.py` | Scripted `MockBrain` or thin OpenAI-compatible `LiveBrain` |
| `agent.py` | The while-loop that stitches Thought / Action / Observation |
| `cli.py` | Question in → transcript + Final Answer out |

## Help / good first issues

See [CONTRIBUTING.md](CONTRIBUTING.md) for fork → install → mock → PR. Scoped tickets live in [Issues](https://github.com/primeodin/tiny-tool-agent/issues). Open contribution ideas:

- **#1** — Add a `unit_convert` tool (C↔F) with a mock script path  
- **#2** — `--trace` flag that numbers each Thought/Action/Observation step  

New to pull requests? Start at [first-commit-ai](https://github.com/primeodin/first-commit-ai), then come back.

## Daily builds series

Tiny, tested teaching repos — starter → mid. Ship one, read it, then climb:

| Lane | Repo | Why open it |
| --- | --- | --- |
| Starter chat | [first-commit-ai](https://github.com/primeodin/first-commit-ai) | Mock-first chat CLI + pytest |
| Starter RAG | [notes-rag](https://github.com/primeodin/notes-rag) | Retrieve, cite, answer over Markdown notes |
| Starter tokenizer | [tiny-bpe-tokenizer](https://github.com/primeodin/tiny-bpe-tokenizer) | Watch text become token IDs — train, encode, decode |
| Mid tool agent (this) | [tiny-tool-agent](https://github.com/primeodin/tiny-tool-agent) | ReAct: Thought, Action, Observation, Final Answer |
| Attention mid | [attention-warrior](https://github.com/primeodin/attention-warrior) | Transformer attention you can hold in one hand |
| Shop skills | [mister-jay](https://github.com/primeodin/mister-jay) | Interactive DIY drills — [live](https://primeodin.github.io/mister-jay/) |
| Literacy (Sinhala) | [jay-ai-sinhala](https://github.com/primeodin/jay-ai-sinhala) | Friends 70+ learning GitHub + AI — [live](https://primeodin.github.io/jay-ai-sinhala/) |
| Systems DIY | [camera-selector](https://github.com/primeodin/camera-selector) | NVR/Frigate camera planning — [live](https://primeodin.github.io/camera-selector/) |

Weekday cadence, in order: chat CLI → RAG → tokenizer → **tool agent (this)** → prompt lab → embeddings → vision → memory → shop-skill explainer.

Profile forge: [github.com/primeodin](https://github.com/primeodin)

## License

MIT
