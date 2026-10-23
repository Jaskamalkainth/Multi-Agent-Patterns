"""One Query, Four Patterns · CrewAI: the script twin of 05_shopping_patterns_crewai.ipynb. Run it from the repo root or notebooks/:

    python notebooks/05_shopping_patterns_crewai.py

Same cells, same code as the notebook; the Markdown cells are the comments.
"""


# %% [markdown]
# # One Query, Four Patterns · CrewAI
#
# The same shopping demo as `04_shopping_patterns_langgraph.ipynb`, built with CrewAI. Same query
# (**"Black running shoes, size 9, under ₹1,000"**), same three demo stores, same grader, same scripted
# replies offline. Only the framework changes, so you can compare LangGraph and CrewAI like for like.
#
# | Level | Pattern | CrewAI building block | File |
# |---|---|---|---|
# | L0 | Pipeline | A `Crew` with `Process.sequential`: three fixed tasks | `crews/l0_sequential.py` |
# | L1 | Planner → workers | A planner task whose plan is context for a fixed list of worker tasks | `crews/l1_planned.py` |
# | L2 | Team + critic | `async_execution=True` scouts, and the critic as a task `guardrail` | `crews/l2_guardrail.py` |
# | L3 | Event-driven | A `Flow`: `@start` waits for the price feed, `@router` decides, `@listen` runs L2 | `crews/l3_flow.py` |
#
# Every agent's model is `BridgeLLM` (`crews/llm.py`): a CrewAI `BaseLLM` that answers from the script offline,
# or asks a real model for JSON that matches the task's pydantic schema (`crews/contracts.py`).
#
# Needs CrewAI: `pip install -r requirements-crewai.txt` (Python 3.10–3.13). Nothing is ever really bought.


# %%
# Put the repo root on the path so `patterns` and `lab` import (from notebooks/, the repo root, or as a script)
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
ROOT = HERE.parent if HERE.name == "notebooks" else HERE
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):   # a script in a Windows console: print ₹ and arrows, not an error
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import warnings
from concurrent.futures import ThreadPoolExecutor

import crews
from crews import l0_sequential, l1_planned, l2_guardrail, l3_flow
from lab import llm
from patterns import common, score, world

if not crews.available():
    raise RuntimeError("CrewAI is not installed: pip install -r requirements-crewai.txt (Python 3.10-3.13)")
warnings.filterwarnings("ignore", message="function callbacks cannot be serialized")   # the demo doesn't checkpoint crews


def run_crew(level, **kw):
    # A worker thread: Jupyter already runs an event loop, and Crew.kickoff() won't start inside one
    with ThreadPoolExecutor(1) as pool:
        return pool.submit(crews.run, level, **kw).result()

common.set_pace(0)   # the talk pauses between messages so a room can read along; a notebook doesn't need to


# %% [markdown]
# ## Choose the brain
#
# `offline` (the default) uses scripted replies: same result every run, no key. To have a real model make the
# decisions, set `BRAIN = "gemini"` and put a free key from [Google AI Studio](https://aistudio.google.com/api-keys)
# in the repo's `.env` as `GEMINI_API_KEY` (or paste it below). Gemini is reached through its OpenAI-compatible
# endpoint, so this needs `pip install openai`.
#
# A real model can be slow or fail. If a call fails, the agents fall back to their scripted replies for the
# rest of the run and say so, so a run always finishes.


# %%
import os

BRAIN = "offline"   # "offline" | "gemini"

if BRAIN == "gemini":
    os.environ["OPENAI_API_KEY"] = os.getenv("GEMINI_API_KEY") or "your-gemini-api-key"
    os.environ["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
    llm.configure("openai", "gemini-3.5-flash")
else:
    llm.configure("offline")
print("brain:", llm.MODE, llm.MODEL)


# %% [markdown]
# ## The world
#
# Three demo stores, eight listings. Look for the traps before you run anything: a cheap black shoe that
# isn't a running shoe, running shoes without size 9, and a ₹699 "Sparx" from a reseller nobody has checked.


# %%
try:                        # Jupyter: render tables and diagrams. A plain script: print the Markdown.
    get_ipython()
    from IPython.display import Markdown, display
    NOTEBOOK = True
except NameError:
    Markdown, display, NOTEBOOK = str, print, False

rows = ["| id | store | listing | price | type | sizes | seller | verified |", "|---|---|---|---|---|---|---|---|"]
for x in world.LISTINGS.values():
    s = world.SELLERS[x["seller"]]
    rows.append(f"| {x['id']} | {x['store']} | {x['name']} | ₹{x['price']:,} | {x['type']} | "
                f"{', '.join(map(str, x['sizes']))} | {x['seller']} | {'✓' if s['verified'] else '✗ ' + s['note']} |")
print("Query:", world.QUERY)
print("Goal: ", world.GOAL)
display(Markdown("\n".join(rows)))


# %% [markdown]
# ## Watching a run
#
# Agents don't print. They emit events (an agent appears, a message is sent, a tool is called) and whoever
# is listening draws them: the talk's web page, `search.py` in the terminal, and here a small printer.
#
# A crew has no graph to draw, so `tasks()` lists what the developer built instead: each task, the agent that
# runs it, the schema its answer must match, whether it runs async, its guardrail, and which earlier tasks it
# gets as context.


# %%
NAMES = {"you": "You", "checkout": "Checkout", "feed": "Price feed"}


def show(ev):
    t = ev["type"]
    if t == "agent":
        NAMES[ev["id"]] = ev["label"] + (f" {ev['id'][-1]}" if ev["id"].startswith("scout-") else "")
    elif t == "step":
        print(f"\n— {ev['text']}")
    elif t == "msg":
        print(f"  {ev['kind'].upper():>5}  {NAMES.get(ev['from'], ev['from'])} → {NAMES.get(ev['to'], ev['to'])}: {ev['text']}")
    elif t == "say":
        print(f"  {NAMES.get(ev['id'], ev['id']):>11}: {ev['text']}")
    elif t == "tool":
        print(f"  {NAMES.get(ev['agent'], ev['agent']):>11} ⚙ {ev['tool']}({ev['args']}) → {ev['result']}")
    elif t == "note":
        print(f"  ! {ev['text']}")
    elif t == "notify":
        print(f"\n  📱 {ev['title']}: {ev['text']}")


def report(r):
    g = r["grade"]
    if not g:
        print("\nNothing bought.")
        return
    print(f"\n{g['name']} · ₹{g['price']:,} · score {g['score']}/{g['of']}")
    for k, ok in g["checks"].items():
        print(f"  {'✓' if ok else '✗'} {k:<19} {g['why'][k]}")


def scoreboard(results):
    rows = ["| Level | Framework | Bought | Score | Agents | LLM calls | Tokens | Human steps |",
            "|---|---|---|---|---|---|---|---|"]
    for r in results:
        g, s = r["grade"], r["stats"]
        bought, sc = (f"{g['name']} · ₹{g['price']:,}", f"{g['score']}/{g['of']}") if g else ("nothing", "—")
        fw = {"langgraph": "LangGraph", "crewai": "CrewAI"}[r["framework"]]
        rows.append(f"| {r['title']} | {fw} | {bought} | {sc} | {s['agents']} | {s['llm_calls']} | {s['tokens']:,} | {s['human_steps']} |")
    display(Markdown("\n".join(rows)))


def tasks(crew):
    print(f"  {crew.process}")
    for i, t in enumerate(crew.tasks):
        flags = (["async"] if t.async_execution else []) + ([f"guardrail={t.guardrail.__name__}"] if t.guardrail else [])
        ctx = [crew.tasks.index(x) for x in t.context] if isinstance(t.context, list) and t.context else []
        print(f"  task {i}: {t.agent.role:<22} → {t.output_pydantic.__name__:<9} {' '.join(flags):<20}"
              + (f"context: tasks {ctx}" if ctx else ""))


stop_listening = common.listen(show)
results = {}


# %% [markdown]
# ## Level 0 · Sequential crew
#
# A developer wrote three tasks, and `Process.sequential` runs them in order; each task's output is the next
# one's context. Same weakness as the LangGraph pipeline: the tasks only mention the colour and the budget,
# so "running" and "size 9" disappear. One difference: here every step is an LLM agent reading the previous
# output, not code, so even a fixed pipeline spends a model call per step.


# %%
tasks(l0_sequential.build())


# %%
results[0] = run_crew(0)
report(results[0])


# %% [markdown]
# ## Level 1 · Planner + fixed tasks
#
# A planner task turns the query into checks, and its plan is context for every worker task. The difference
# from LangGraph: there the planner chose the workers at run time. A crew's task list is fixed when the crew is
# built, so the plan can only shape what the workers do, not which workers run. Still no task about the seller.


# %%
tasks(l1_planned.build())


# %%
results[1] = run_crew(1)
report(results[1])


# %% [markdown]
# ## Level 2 · Async tasks + guardrail
#
# - **Fan out** is a task flag: `async_execution=True` on each scout task. **Fan in** is the next task's
#   `context`. No `Send()`, no reducers.
# - **The critic is a guardrail** on the evaluator task: a function that returns `(True, output)` or
#   `(False, "why")`.
# - **The rework loop is built in:** when the guardrail fails, CrewAI re-runs the same agent with the feedback,
#   up to `guardrail_max_retries`. In LangGraph you draw that loop as two conditional edges.
#
# ```python
# kit.task(..., async_execution=True)                                  # one per store
# kit.task(..., context=scout_tasks, guardrail=critic, guardrail_max_retries=2)
# ```


# %%
tasks(l2_guardrail.build())


# %%
results[2] = run_crew(2)
report(results[2])


# %% [markdown]
# ## Level 3 · Flow
#
# A `Flow` is CrewAI's event-driven layer: a method starts when the method it listens to finishes, and a
# router returns the name of the next branch. The Level 2 crew runs unchanged, and checkout asks you first.
#
# ```python
# class PriceWatch(Flow[Watch]):
#     @start()
#     def wait_for_price(self): ...          # blocks until the price feed drops a price
#
#     @router(wait_for_price)
#     def does_it_matter(self): ...          # one model call: "trigger" or "ignore"
#
#     @listen("trigger")
#     def run_team(self): ...                # the Level 2 crew, with ask_first=True
# ```


# %%
results[3] = run_crew(3, auto_drop=1)
report(results[3])


# %% [markdown]
# ## Scoreboard: CrewAI, then LangGraph
#
# The same four levels in LangGraph, run quietly, so you can compare the two frameworks side by side. Same
# answers, different building blocks. CrewAI spends more tokens: every agent reads the whole task text with the
# listings, and at Levels 0 and 1 each step is a model call where LangGraph runs code.


# %%
from patterns import run as langgraph_run

stop_listening()
both = [results[n] for n in range(4)] + [langgraph_run(n, auto_drop=0.5) for n in range(4)]
scoreboard(sorted(both, key=lambda r: (r["level"], r["framework"] != "crewai")))
stop_listening = common.listen(show)


# %% [markdown]
# ## Try this
#
# **1. Remove the guardrail.** Build the evaluator task without its critic. What does Level 2 buy now?


# %%
from crews import kit

original = kit.task
kit.task = lambda *a, guardrail=None, guardrail_max_retries=None, **kw: original(*a, **kw)   # drop the critic
try:
    report(run_crew(2))
finally:
    kit.task = original


# %% [markdown]
# **2. Your own query.** Any query with a colour, a type (`running` or `casual`), an optional size and a
# budget works on the demo stores. The grader builds its checks from your query. With the grey query every
# level scores 4/4: a pattern only earns its tokens when the data has a trap it catches. Try your own.


# %%
stop_listening()   # quiet: just the scoreboards
for q in ["Grey running shoes, size 9, under ₹800", "Black running shoes, size 8, under ₹1,000"]:
    world.use("demo", query=q)
    display(Markdown(f"**{q}**"))
    scoreboard([run_crew(n, auto_drop=0.5) for n in range(4)])
world.use("demo")  # back to the default query
stop_listening = common.listen(show)


# %% [markdown]
# **3. A guardrail written as a sentence.** CrewAI also accepts a guardrail as plain text, checked by an LLM,
# for example `guardrail="The seller must be verified in the seller register"`. Try it in
# `crews/l2_guardrail.py` with `BRAIN = "gemini"`. What does the LLM need to see to check it, and is it as
# reliable as the function?
#
# **4. Make Level 1 safer.** Add a seller task to `crews/l1_planned.py` (an agent whose script calls
# `world.seller_check`) between the price and pick tasks. Does it now match Level 2, and what does it cost
# in model calls?
