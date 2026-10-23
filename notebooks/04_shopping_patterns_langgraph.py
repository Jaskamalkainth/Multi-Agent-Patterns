"""One Query, Four Patterns · LangGraph: the script twin of 04_shopping_patterns_langgraph.ipynb. Run it from the repo root or notebooks/:

    python notebooks/04_shopping_patterns_langgraph.py

Same cells, same code as the notebook; the Markdown cells are the comments.
"""


# %% [markdown]
# # One Query, Four Patterns · LangGraph
#
# The shopping demo from the talk, in a notebook. Four agent teams get the same query,
# **"Black running shoes, size 9, under ₹1,000"**, the same three demo stores, the same tools and the same grader.
# Only the coordination pattern changes, so the scoreboard at the end shows what each pattern buys you.
#
# | Level | Pattern | File |
# |---|---|---|
# | L0 | Pipeline: search → filter → pick | `patterns/l0_pipeline.py` |
# | L1 | Planner → workers (hub and spoke) | `patterns/l1_orchestrator.py` |
# | L2 | Team + critic (fan out / fan in, rework loop) | `patterns/l2_team.py` |
# | L3 | Event-driven (a price drop wakes the L2 team) | `patterns/l3_event.py` |
#
# This notebook doesn't copy the agents: it imports the repo's own LangGraph code, so what you change in
# `patterns/` shows up here. It runs offline with scripted replies by default, so you don't need a key.
# Nothing is ever really bought. The same four patterns in CrewAI are in `05_shopping_patterns_crewai.ipynb`.


# %%
# Put the repo root on the path so `patterns` and `lab` import (from notebooks/, the repo root, or as a script)
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
ROOT = HERE.parent if HERE.name == "notebooks" else HERE
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):   # a script in a Windows console: print ₹ and arrows, not an error
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from lab import llm
from patterns import common, l0_pipeline, l1_orchestrator, l2_team, l3_event, run, score, world

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


def graph(module):
    g = module.build().get_graph()
    if NOTEBOOK:   # JupyterLab 4.1+ draws Mermaid; elsewhere you see the Mermaid text (paste it into mermaid.live)
        display(Markdown("```mermaid\n" + g.draw_mermaid() + "\n```"))
    else:
        for e in g.edges:
            print(f"  {e.source} {'-->' if e.conditional else '→'} {e.target}")


stop_listening = common.listen(show)
results = {}


# %% [markdown]
# ## Level 0 · Scripted pipeline
#
# A developer decided every step at build time: search for one keyword (the colour), drop what's over
# budget, take the cheapest. The LLM only writes the confirmation. Nobody wrote a step for "running" or
# "size 9", so those requirements silently disappear.


# %%
graph(l0_pipeline)


# %%
results[0] = run(0)
report(results[0])


# %% [markdown]
# ## Level 1 · Planner → workers
#
# You give the goal, not the steps. A planner (an LLM) turns the query into checks and briefs one worker per
# check. Every result goes back through the planner (hub and spoke), and workers pass on only what their brief
# asked for. It catches the type and the size this time, but no worker's brief is about the seller.


# %%
graph(l1_orchestrator)


# %%
results[1] = run(1)
report(results[1])


# %% [markdown]
# ## Level 2 · Team + critic
#
# Three things change:
#
# - **Fan out / fan in:** `Send()` starts one scout per store at once; the evaluator waits for all of them.
# - **Critic:** a reviewer with a clean context. It sees only the pick and the seller register.
# - **Rework loop:** a rejected pick goes back to the evaluator, which picks again.
#
# ```python
# g.add_conditional_edges("lead", fan_out, ["scout"])                         # fan out
# g.add_edge("scout", "evaluator")                                            # fan in
# g.add_conditional_edges("evaluator", after_evaluator, ["critic", "checkout"])
# g.add_conditional_edges("critic", after_critic, ["evaluator", "checkout"])  # rejected? pick again
# ```


# %%
graph(l2_team)


# %%
results[2] = run(2)
report(results[2])


# %% [markdown]
# ## Level 3 · Event-driven
#
# Nobody types anything. A watcher subscribes to the price feed with your saved query. When a price drops,
# it decides whether that matters and, if it does, starts the **Level 2 team, unchanged**. This time checkout
# asks you before buying instead of ordering.
#
# `auto_drop` is how many seconds the feed waits before the price drops by itself.


# %%
results[3] = run(3, auto_drop=1)
report(results[3])


# %% [markdown]
# ## Scoreboard
#
# Each level is more autonomous and spends more tokens. Is the better answer worth it?


# %%
scoreboard(results.values())


# %% [markdown]
# ## Try this
#
# **1. Remove the critic.** Make Level 2's evaluator go straight to checkout. What does it buy now, and what
# does that tell you about where the "intelligence" in Level 2 really is?


# %%
original = l2_team.after_evaluator
l2_team.after_evaluator = lambda state: "checkout"   # build() reads this when it wires the graph
try:
    report(run(2))
finally:
    l2_team.after_evaluator = original


# %% [markdown]
# **2. Your own query.** Any query with a colour, a type (`running` or `casual`), an optional size and a
# budget works on the demo stores. The grader builds its checks from your query. With the grey query every
# level scores 4/4: a pattern only earns its tokens when the data has a trap it catches. Try your own.


# %%
stop_listening()   # quiet: just the scoreboards
for q in ["Grey running shoes, size 9, under ₹800", "Black running shoes, size 8, under ₹1,000"]:
    world.use("demo", query=q)
    display(Markdown(f"**{q}**"))
    scoreboard([run(n, auto_drop=0.5) for n in range(4)])
world.use("demo")  # back to the default query
stop_listening = common.listen(show)


# %% [markdown]
# **3. Add a trap.** Add a ₹599 black running shoe in size 9 from an unverified seller to `data/shoes.json`,
# restart the kernel (or rerun the script) and run everything again. Which levels buy it?
#
# **4. Make Level 1 safer.** Give the planner a `seller` worker in `patterns/l1_orchestrator.py` (a new
# entry in `SKILLS` and a branch in `worker()` that calls `world.seller_check`). Does it now match Level 2,
# and how do the two compare on tokens?
#
# **Next:** the same four patterns in CrewAI, in `05_shopping_patterns_crewai.ipynb`.
