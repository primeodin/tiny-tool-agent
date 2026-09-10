# Why a bad Observation poisons every later Thought

Short shop note. The README already draws the ReAct loop — this page answers the *debugging* question: when the Final Answer is wrong, do you rewrite the prompt, or fix the tool?

## The inheritance rule

Every Thought after the first reads the **whole transcript**. That includes every `Observation:` your runtime appended. The model does not re-run the tool; it trusts the string you gave it.

So:

- A wrong Observation is not a one-step glitch
- It becomes ground truth for every later Thought
- Polite prompting ("think carefully") cannot undo a lie already on the tape

Shop rule from the README, restated: **fix the tool, don't yell at the model.**

## Hand-worked poison: `17 * 24`

Healthy path (what `--mock` does today):

| Step | Line on the tape | Truth |
| --- | --- | --- |
| 1 | `Thought: I need exact arithmetic, so I will use calc.` | Plan is fine |
| 2 | `Action: calc: 17 * 24` | Tool choice is fine |
| 3 | `Observation: 408` | Tool told the truth |
| 4 | `Thought: The tool returned 408.` | Inherits 408 |
| 5 | `Final Answer: 408` | Correct |

Now break only the tool — pretend `calc` returns `407` (off-by-one, bad AST edge, or a stub you forgot to wire):

| Step | Line on the tape | Truth |
| --- | --- | --- |
| 1 | `Thought: I need exact arithmetic, so I will use calc.` | Still fine |
| 2 | `Action: calc: 17 * 24` | Still fine |
| 3 | `Observation: 407` | **Lie enters here** |
| 4 | `Thought: The tool returned 407.` | Model is "correct" relative to the tape |
| 5 | `Final Answer: 407` | Wrong answer, honest agent |

Same Thoughts. Same Action. One bad Observation. The loop did its job — it just amplified a tool bug.

## What to check (in order)

1. **Print the Observation** — before you touch the system prompt. If the number is already wrong, the brain is not the patient.
2. **Unit-test the tool alone** — `calc("17 * 24") == "408"` with no agent in the room.
3. **Only then** look at Action parsing / MockBrain scripts — wrong tool name or a scripted path that never calls `calc` is a different failure mode.

Yelling "be more careful" at step 4 is cargo-cult. The model already carefully used the poisoned tape.

## Shop tip (with judgment)

**When the Final Answer smells wrong, diff the Observations first.** If Observation matches the tool's real output and that output is wrong, fix `tools.py` (or the external API). If Observation is right but the next Thought ignores it, *then* you have a prompt / brain problem.

Safe hack for teaching: deliberately break `calc` in a throwaway branch, re-run the mock question, and watch Final Answer track the lie. That drill sticks harder than another diagram.

Unsafe on a live agent: silently catch tool exceptions and append `Observation: OK` (or an empty string). You just taught the model that failure looks like success — every later Thought will plan on fiction. Surface the error text in the Observation, or stop the loop. Lying "OK" is how shops ship broken gear with a green sticker.
