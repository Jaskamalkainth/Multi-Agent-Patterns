# Autonomy Lab: make it autonomous, then make it safe

A hands-on lab for the **AgenticAI Summit 2026** session *Agent Flow & Multi-Agent Systems*.

Agents usually start when a person types a prompt or submits a form. In this lab they start **on their own**, when something changes in the world. Then we break them, and fix them with two guardrails written in code.

This lab follows Rahul Verma's CrewAI + n8n demos, which cover agent roles, typed handoffs and a human approval gate. This lab covers what happens **before** a human is involved: agents that start by themselves, fight over ownership, and loop.

| Step | File | What happens |
|---|---|---|
| 1 | `steps/step1_trigger.py` | **Self-starting.** A price drop in a store feed starts the agents. Nobody types anything. |
| 2 | `steps/step2_broken.py` | **Break it.** Two agents both think the purchase is theirs. They argue, add 2 items to the cart, and only the framework's recursion limit stops them. |
| 3 | `steps/step3_owner.py` | **Fix 1: one owner per task.** First claim wins. Code rejects any other claim. |
| 4 | `steps/step4_budget.py` | **Fix 2: budget and stop.** Hard limits on turns and tokens. When hit, stop and hand over to a human. |

Built with [LangGraph](https://github.com/langchain-ai/langgraph). All orders are simulated. Nothing is bought.

---

## Setup (2 minutes)

Requires Python 3.10 or newer.

```bash
git clone <repo-url> autonomy-lab
cd autonomy-lab
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

No API key needed. By default the lab runs in **offline mode** with scripted agent replies, so every run gives the same result.

## Run it

```bash
python run.py 1 --auto-drop 3     # 1. agents start by themselves after a price drop
python run.py 2                   # 2. two agents, no rules: watch it go wrong
python run.py 3                   # 3. fix 1: one owner per task
python run.py 3 --chaos           #    ...but a looping owner still runs until the framework kills it
python run.py 4 --chaos           # 4. fix 2: the budget stops the loop
```

Options:

| Flag | Meaning |
|---|---|
| `--auto-drop N` | The price drops by itself after N seconds. Good for a single screen. |
| `--watch` | Steps 2–4: wait for a real price change instead of firing at once. |
| `--chaos` | The owner agent keeps re-checking prices forever. Shows why step 4 is needed. |

Environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `LAB_DELAY` | `0.7` | Seconds between lines, so a room can read along. Use `0` when testing. |
| `LAB_LLM` | `offline` | `offline`, `openai` or `anthropic` |
| `LAB_MODEL` | — | Model name, required for real-model mode |

### Trigger step 1 by hand

Run `python run.py 1` in one terminal. It waits. In a second terminal:

```bash
python tools/drop_price.py                 # Sparx shoe → ₹849
python tools/drop_price.py CMPS-BLK-41 899 # any item, any price
python tools/drop_price.py --reset         # all prices back above budget
```

Or open `data/price_feed.json` and change a price below 1000 by hand.

---

## What changes between steps

Each step is a full, runnable file. The new lines are marked `# NEW`. To see exactly what each fix adds:

```bash
diff steps/step2_broken.py steps/step3_owner.py    # ownership rule
diff steps/step3_owner.py  steps/step4_budget.py   # budget + escalate
```

The two fixes in short:

```python
# Fix 1: one owner per task (step 3)
def claim(state, name):
    owner = state.get("owner")
    return name if owner in (None, name) else None

# Fix 2: budget and stop (step 4)
def within_budget(state):
    return state.get("turn", 0) < MAX_TURNS and state.get("tokens", 0) < MAX_TOKENS
```

The models never enforce these rules. **Code does.** A model can still say "I'll buy it". The code decides whether it can.

To see each graph as a diagram: `python tools/draw_graphs.py` writes `docs/graphs.md` (Mermaid; renders on GitHub).

---

## Use a real model

Real models are not deterministic, so each run may differ. The guardrails still hold, because they are in code.

**Any OpenAI-compatible server** (OpenAI, vLLM, Ollama, LM Studio):

```bash
pip install openai
export LAB_LLM=openai
export LAB_MODEL=<model-name>
export OPENAI_API_KEY=<key>                       # any value for local servers
export OPENAI_BASE_URL=http://localhost:8000/v1   # leave unset for OpenAI
python run.py 2
```

**Anthropic:**

```bash
pip install anthropic
export LAB_LLM=anthropic LAB_MODEL=<model-name> ANTHROPIC_API_KEY=<key>
python run.py 2
```

---

## Try this yourself

1. In step 4, change `MAX_TURNS` to 3. What happens to a normal (non-chaos) run?
2. In step 3, change who gets the event first (`g.add_edge("watcher", "deal")`). Who owns the task now?
3. In step 4, pause for human approval before checkout with LangGraph's `interrupt()` (the same idea as Rahul's n8n approval gate, in code). Hint: compile with a checkpointer.
4. Add a third agent, "Reviews", that must agree before `buy` is allowed.

---

## Project layout

```
run.py                 runs a step and prints the summary
lab/feed.py            the fake store feed and the watcher
lab/llm.py             one ask() function: offline script or a real model
lab/core.py            graph state, watcher node, terminal output
steps/step1..4_*.py    the four steps
tools/drop_price.py    change a price from a second terminal
tools/draw_graphs.py   export each graph as Mermaid
data/price_feed.json   the "world"
PRESENTER.md           stage runbook
```
