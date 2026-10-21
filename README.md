# How Agents Talk: coordination patterns in LangGraph and CrewAI

A hands-on session on how AI agents coordinate. One shopping query goes all the way through, from search to a simulated
order: **"Black running shoes, size 9, under ₹1,000."** The same query runs through four coordination patterns, in
[LangGraph](https://github.com/langchain-ai/langgraph) and in [CrewAI](https://github.com/crewAIInc/crewAI), on demo stores
or on real listings from Amazon.in, Flipkart and Myntra. A grader scores every purchase, so you can see which pattern buys
the right shoe and what it costs.

Nothing is ever really bought.

The talk (`python app.py`) has four sections:

| # | Section | What's in it |
|---|---|---|
| 1 | **Patterns** | Eight animated simulations: sequential handoff, selective context, hierarchical process, parallel fan-out/fan-in, critic loop, shared state, event-driven, human in the loop. Each shows what every agent's context window holds |
| 2 | **LangGraph** | Five tabs (what it is, how a run works, strengths, weaknesses, gotchas and fixes), then a code tour of the real repo code: state and reducers, nodes, edges, conditional routing, `Send`, cycles, `interrupt()` and checkpoints, the Claude call |
| 3 | **CrewAI** | Five tabs (what it is, how a run works, where it beats LangGraph, weaknesses, which one when), then the same tour for CrewAI: Agent, Task, context, `Process.sequential`, `async_execution`, guardrails, Flow, the BaseLLM bridge, `Process.hierarchical`, and a side-by-side comparison |
| 4 | **Live demo** | The real graphs and crews running: pick the framework, the brain (scripted or Claude) and the world (demo stores, live sites, recording). A Run log shows every event and model call |

## Quick start

Python 3.10 or newer. No API key needed: by default the agents use scripted replies, so every run gives the same result.
Run everything from the repo folder (`how-agents-talk/`).

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**macOS / Linux**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

`python app.py` opens the talk at **http://127.0.0.1:8700** in your browser, with the live demo inside it.
The **Theme** button in the top bar switches Dark → Light → System (dark by default, for projectors); the live demo inside
follows it. Add `?theme=light` to the URL to open in light.
Leave the terminal running; `Ctrl+C` stops everything.

## Optional extras

| Want | Install | Notes |
|---|---|---|
| The CrewAI version of Demo 1 | `pip install -r requirements-crewai.txt` | Heavier: also installs chromadb, grpc and more |
| Real listings from Amazon.in, Flipkart and Myntra | `pip install -r requirements-live.txt` | Uses your installed Google Chrome; no browser download |
| Claude as the agents' brain, no API key | Install [Claude Code](https://claude.com/claude-code) and run `claude` once to log in | Found on PATH, or the copy bundled with the VS Code extension |
| Your own settings | `copy .env.example .env` (Windows) or `cp .env.example .env` | See [Settings](#settings-env) |

Without an extra, its button on the page is greyed out and says what to install.

## Run it

### The whole session: `app.py`

| Command | What it does |
|---|---|
| `python app.py` | The talk, with the live demo inside it. Opens your browser |
| `python app.py --no-browser` | The same, without opening a browser tab |
| `python app.py --port 8800 --live-port 8801` | Other ports, if 8700 or 8701 is taken |

It starts two local servers:

| URL | What |
|---|---|
| http://127.0.0.1:8700 | The talk (`web/talk.html`): four sections, PageDown/PageUp or a clicker to move |
| http://127.0.0.1:8701 | The live demo on its own page (section 4 of the talk) |
| http://127.0.0.1:8701/evidence | What the last live collection saw: each site's screenshot and every listing with its verdict |

On the live demo each run has four choices: **Framework** (LangGraph · CrewAI), **Brain** (scripted · Claude haiku ·
Claude sonnet), **World** (demo stores · live sites · live recording) and the **Pattern** (L0–L3, or Run all four).
With **Live sites** you also get: **Browser** Show/Hide (watch Chrome search, or hide it), **↻ Collect fresh + run all**
(search again now instead of reusing the last 15 minutes) and **Evidence ↗** (screenshots and every listing).
While a run is going: **❚❚ Pause / ▶ Resume** (or Space) holds it at its next step, and changing the **pace** (Slow · Stage · Quick ·
Instant) applies at once. Clicking a pattern only selects it (description, graph and code preview); **▶ Run** starts it.
Keys: `0`–`3` select a pattern, Enter runs it, `a` runs all four.

In the talk's Patterns section, the player bar has **Restart · Pause/Play · Step ⏭** (play to the next step, then pause),
**speed** 0.25×–3× and **Auto-play all**. Keys: Space pause · N step · R restart · ←/→ pattern · +/− speed.

To start the agents with Claude already chosen:

```powershell
$env:LAB_LLM = "claude"; $env:LAB_MODEL = "haiku"; python app.py      # PowerShell
```

```bash
LAB_LLM=claude LAB_MODEL=haiku python app.py                          # macOS / Linux
```

The pages' Brain picker overrides this per run, so you can also just switch it in the browser.

### Demo 1 in the terminal: `search.py`

| Command | What it does |
|---|---|
| `python search.py` | All four levels with LangGraph, then the scoreboard |
| `python search.py --level 2` | One level (0, 1, 2 or 3) |
| `python search.py --fast` | No pauses between messages |
| `python search.py --framework crewai` | The CrewAI version (`langgraph`, `crewai` or `both`) |
| `python search.py --framework both --fast` | Both frameworks, compared level by level |
| `python search.py --brain claude-haiku` | Claude decides (`offline`, `claude-haiku`, `claude-sonnet`) |
| `python search.py --world live` | Real listings: opens Chrome and searches the three sites first |
| `python search.py --world recording` | The last live collection, replayed |
| `python search.py --auto-drop 5` | Level 3: seconds until the price drops (or the re-check runs) by itself |

Options combine, for example `python search.py --framework both --brain claude-haiku --world live`.

### Demo 2 in the terminal: `run.py`

| Command | What it does |
|---|---|
| `python run.py` | A price drop starts the team. All guardrails on; you approve or deny the purchase |
| `python run.py --yes` / `--deny` | Answer the approval without being asked |
| `python run.py --no-owner` | Guardrail 1 off: both buyers act, 2 items in the cart |
| `python run.py --no-budget --chaos` | Guardrail 2 off: a loop only the framework's recursion limit stops |
| `python run.py --chaos` | The same loop with the budget on: stops at 6 turns and escalates |
| `python run.py --no-approval` | Guardrail 3 off: it buys and nobody is asked |
| `python run.py --unsafe` | All three guardrails off |
| `python run.py --watch` | Wait for a real price change. In a second terminal: `python run.py --drop` |
| `python run.py --auto-drop 3` | The price drops by itself after 3 seconds |
| `python run.py --crash-after evaluator` | Kill the process mid-run (`watcher`, `scout`, `evaluator`, `deal` or `budget`) |
| `python run.py --resume` | Carry on the last run from its last checkpoint |
| `python run.py --history` | List the last run's checkpoints |
| `python run.py --rewind 4` | Replay the last run from checkpoint 4, with the guardrails you pass |
| `python run.py --drop` / `--reset-feed` | Drop the Sparx price to ₹849 / put every price back above budget |

### Each demo on its own

```bash
python -m patterns.server        # the live demo only, http://127.0.0.1:8701
python -m lab.server             # the guardrails lab (Demo 2) in the browser, http://127.0.0.1:8702
```

Both take `--port N` and `--no-browser`. The guardrails lab is not part of the talk; it's there for the
LangGraph deep dive's interrupt/checkpoint step if you want to show crash, resume and rewind for real.

### After you change the code

```bash
python web/build_code.py         # refresh the code excerpts in the talk's LangGraph and CrewAI tours
```

### Tests

```bash
python -m pytest -q              # 28 tests, offline, about 30 s
```

They cover the four patterns and their grades in both frameworks, the critic and the guardrail retry, the live world
(from the shipped recording, no network), both servers, every guardrail, crash and resume, and rewind. The CrewAI tests are
skipped if CrewAI isn't installed.

## Demo 1 · four patterns, one query

The query runs through four graphs: search three stores, check, pick, place a simulated order. Only the coordination
pattern changes. The grader checks: black running shoe · size 9 in stock · under ₹1,000 · genuine seller.

| Level | Pattern | Bought | Score | Why |
|---|---|---|---|---|
| L0 | **Pipeline**: search → filter → pick | Black canvas slip-on · ₹499 | 2/4 | The script searches "black" and takes the cheapest. Nobody checks "running" or "size 9" |
| L1 | **Planner → workers** (hub and spoke) | "Sparx" running shoe · ₹699 | 3/4 | The planner adds type and size checks, but no worker checks the seller: it's a reseller of fakes |
| L2 | **Team + critic** (fan out / fan in, rework loop) | Asian Wonder running shoe · ₹979 | 4/4 | One scout per store in parallel; a critic rejects the unverified seller and the evaluator picks again |
| L3 | **Event-driven** (publish/subscribe) | Sparx running shoe · ₹849 | 4/4 | A price drop wakes the L2 team. ₹130 cheaper, zero human steps, and it asks you before it buys |

Tokens grow with each level: autonomy is paid in tokens. With Claude Haiku the scores are the same, in about 100 s for all
four levels (LangGraph) or about 130 s (CrewAI).

On the page the stores sit on the left and each listing lights up as agents check, drop, pick, reject or order it. The
agent graph is in the middle, the messages on the right (live Claude calls show their model and time), and the scoreboard
below. The **Run log** under it is the transcript of what happened behind the boxes: every event with its time, and
every model call (click it to see the prompt or context and the raw reply). Filter it to *Model calls only*, or open
**Log file ↗** for the newest run's full log. The **Code** panel shows the file that just ran.

Level 2 in a few lines (`patterns/l2_team.py`):

```python
g.add_conditional_edges("lead", fan_out, ["scout"])                         # fan out: one scout per store, all at once
g.add_edge("scout", "evaluator")                                            # fan in: waits for every scout
g.add_conditional_edges("evaluator", after_evaluator, ["critic", "checkout"])
g.add_conditional_edges("critic", after_critic, ["evaluator", "checkout"])  # rejected? pick again
```

**Try this**

1. In `patterns/l2_team.py`, make `after_evaluator()` return `"checkout"` instead of `"critic"`. What does Level 2 buy now? (The ₹699 fake.)
2. Add a ₹599 "Campus" from another unverified reseller to `data/shoes.json`. Which levels buy it?
3. Run with the Claude brain. The planner writes its own checks: does it think of the seller?
4. Give L1 a seller-check worker. How close does it get to L2, and at what token cost?

### The same four patterns in CrewAI

`crews/` builds the same patterns with CrewAI: same stores, grader, page and Claude bridge. Both frameworks buy the same
shoes; what changes is how you express the pattern and what it costs.

| Level | LangGraph (`patterns/`) | CrewAI (`crews/`) | What changes |
|---|---|---|---|
| L0 | `add_edge("search", "filter")`, steps can be code | `Crew(tasks=[search, filter, pick], process=Process.sequential)` | Every CrewAI task is an agent turn: 3 model calls instead of 1 |
| L1 | the planner node chooses which workers run | a planner task; its plan is `context` for fixed worker tasks | A crew's task list is fixed when it is built |
| L2 | `Send("scout", …)`; critic node; `evaluator ⇄ critic` edges | `async_execution=True`; `guardrail=critic, guardrail_max_retries=2` | The rework loop is one argument: a failed guardrail re-runs the agent with the feedback |
| L3 | a watcher, then the L2 graph | a `Flow`: `@start` waits, `@router` decides, `@listen` runs the crew | Much the same; Flow state is a pydantic model |

LLM calls per level: 1 · 2 · 7 · 8 (LangGraph) and 3 · 5 · 5 · 6 (CrewAI). CrewAI spends more on the simple levels and
fewer on L2/L3, where its critic is a code guardrail instead of a model call.

### Live sites: real listings

Pick **World · Live sites** on the page, or `--world live`. `patterns/live.py` (a Python port of the CrewAI lab's browser
collector) drives your Chrome with Playwright: it searches Amazon.in, Flipkart and Myntra, reads up to 4 results per site and
opens up to 2 product pages each, in about 30–60 s. The collection is saved in `output/live/` and reused for 15 minutes, so
every level and both frameworks see the same evidence. Nothing is logged into, added to a cart or ordered.

| | Demo stores | Live sites |
|---|---|---|
| Query | black running shoes, size 9, under ₹1,000 | black running shoes under ₹1,000: a search page can't show size, so it stays *unverified* and checkout asks you |
| "Black running" | listing fields | "black" and "running" in the evidence text |
| Critic / guardrail checks | the seller register | the evidence: the store's own site, the product page read, not a search-index fallback, fresh |
| Grader | 4 checks | 4 checks: the size check is replaced by **cheapest match** (no cheaper listing passes the others) |
| Level 3 event | a price drop | a scheduled re-check of the stores (there is no real price feed) |

Results depend on the day's listings, so the 2 → 3 → 4 → 4 story isn't guaranteed: that's the point of trying it. Real
traps do appear, such as blue sneakers in a "black" search, or listings whose product page couldn't be read.

- The browser is visible by default (sites block headless Chrome more). Set `MARKETPLACE_BROWSER_HEADLESS=1` to hide it.
- A site that shows a captcha or nothing readable is reported as "no listings read". Evidence is never invented.
- **World · Live · recording** replays the last collection (or `data/live-sample.json`), for a stage without network.
- Automated browsing may conflict with a site's terms. Keep it to a demo: a few page loads, never ordering.

### The Claude bridge

LangGraph nodes and CrewAI agents call Claude the same way as the CrewAI lab: `lab/llm.py` → `claude -p --json-schema …
--tools ""` with your saved login. No API key, no model tools, evidence passed as untrusted data, and every answer validated
against a schema (CrewAI: `crews/llm.py`, a `BaseLLM` with pydantic contracts). If a call fails or times out, that call falls
back to the scripted answer and the page says so, so a run never hangs.

## Demo 2 · the guardrails lab

The same shoe stores, as a team that **starts on its own** when a price drops: a watcher, three scouts in parallel, an
evaluator, and two buyers who were both told purchases are their job. Switch its guardrails off one at a time, kill the
process mid-run, resume it, rewind it.

```
price drop → watcher → scout × 3 (parallel) → evaluator → deal ⇄ budget → checkout (you approve)
                                                              ↘ escalate (budget hit)
```

The three guardrails (`lab/guards.py`) are a few lines of code each. The models never enforce them; code does:

```python
def claim(state, name):                 # 1 · one owner per task: first claim wins
    owner = state.get("owner")
    return name if owner in (None, name) else None

def within_budget(state):               # 2 · budget and stop: checked before every hop
    return state.get("turn", 0) < MAX_TURNS and state.get("tokens", 0) < MAX_TOKENS

def approve(proposal):                  # 3 · human approval: pauses the graph until you answer
    return interrupt(proposal) == "approve"
```

Every step is saved to `output/checkpoints.sqlite`, which is what makes crash, resume and rewind work. In the browser each
button starts `run.py` as a subprocess, so a crash really kills a process.

## Settings (`.env`)

Copy `.env.example` to `.env`. Real environment variables win over it.

| Variable | Default | Meaning |
|---|---|---|
| `LAB_LLM` | `offline` | `offline` (scripted), `claude` (Claude Code CLI, no key), `anthropic` (API key), `openai` (any OpenAI-compatible server) |
| `LAB_MODEL` | — | `claude`: `sonnet` (default), `haiku` or `opus`. Required for `anthropic` and `openai` |
| `LAB_DELAY` | `0.7` | Seconds between messages, so a room can follow. `0` for testing |
| `LAB_TIMEOUT` | `20` (`90` for claude) | Seconds before a model call gives up and falls back to the script |
| `CLAUDE_BIN` | — | Path to `claude`, if it isn't on PATH or bundled with the VS Code extension |
| `ANTHROPIC_API_KEY` | — | For `LAB_LLM=anthropic` (also `pip install anthropic`) |
| `OPENAI_API_KEY`, `OPENAI_BASE_URL` | — | For `LAB_LLM=openai`: OpenAI, Groq, vLLM, Ollama… (also `pip install openai`) |
| `MARKETPLACE_BROWSER_HEADLESS` | `0` | `1` hides Chrome during a live collection |

## CrewAI practice notebooks

Three small CrewAI projects in `notebooks/`, to try on your own after the session. Each runs top to bottom in Jupyter.

| Notebook | Agents | What it shows |
|---|---|---|
| `01_article_writer.ipynb` | Planner → Writer → Editor | A sequential crew; `{topic}` inputs; each task's output is the next one's context |
| `02_customer_support.ipynb` | Support rep + QA reviewer | Tools at task level (`ScrapeWebsiteTool`), delegation, memory |
| `03_financial_analysis.ipynb` | Analyst, strategist, trade advisor, risk advisor | `Process.hierarchical`: a manager LLM delegates the four tasks |

```bash
pip install -r requirements-crewai.txt jupyterlab
jupyter lab notebooks/
```

The first cells install `crewai[tools]`. Then **Choose your LLM**: set `PROVIDER` and paste that provider's key over the
placeholder (or set the key in your environment):

| `PROVIDER` | Key | Extra install |
|---|---|---|
| `gemini` | Free, from [Google AI Studio](https://aistudio.google.com/api-keys) | `crewai[google-genai]` |
| `openai` | [platform.openai.com](https://platform.openai.com/api-keys) | none |
| `anthropic` | [console.anthropic.com](https://console.anthropic.com/settings/keys) | `crewai[anthropic]` |
| `openrouter` | [openrouter.ai](https://openrouter.ai/keys): one key, many models | none |
| `ollama` | No key: a local model via [Ollama](https://ollama.com) (`ollama pull llama3.2`) | none |

Notes: memory (notebook 2) uses OpenAI embeddings, so it's on only with `openai`. Google search in notebook 3 is
optional and needs a [Serper](https://serper.dev) key; without one the agents only read web pages. Notebook 3 is
practice, not financial advice.

## Where the output goes

Everything a run writes goes in `output/` (ignored by git). Older runs are deleted as new ones start, and the tests
write to a temp folder instead (`LAB_OUTPUT`), so `output/` only holds your own runs:

| Path | What |
|---|---|
| `output/live/latest.json`, `output/live/<time>.json` | Each live collection (the newest 10 are kept): every listing with its URL, price, evidence and timestamp |
| `output/live/<site>-latest.png` | What each store's page showed during the last collection |
| `output/patterns/<time>_<framework>_L<n>_<world>.jsonl` | Each live-demo run: every event and model call, one JSON object per line (the page's **Run log**). The newest 30 are kept |
| `output/<time>_<label>/` | Each Demo 2 run (the newest 20 are kept): `console.log`, `e2e.log` (every LLM call and node update), `diff.log` (the state before and after each node), `summary.json` |
| `output/checkpoints.sqlite` | Demo 2 checkpoints, for resume and rewind |
| `output/price_feed.json` | Demo 2's price feed |

## Troubleshooting

| Problem | Fix |
|---|---|
| `Port 8700 is already in use` | Another program has it. Stop it, or `python app.py --port 8800 --live-port 8801` |
| CrewAI button greyed out | `pip install -r requirements-crewai.txt` |
| Live sites greyed out | `pip install -r requirements-live.txt` |
| Claude options say "claude CLI not found" | Install Claude Code, run `claude` once to log in, or set `CLAUDE_BIN` |
| A message says "scripted (model unavailable…)" | That call failed or timed out and used the script. Check `claude` works in a terminal; raise `LAB_TIMEOUT` |
| A store shows "no listings read" | The site blocked or changed its page. Try again, show the browser (`MARKETPLACE_BROWSER_HEADLESS=0`), or use Live · recording |
| A live section in the talk says the demo isn't running | `python app.py` was stopped. Start it and press Retry |
| `run.py --resume` says there's nothing to resume | The last run finished. Run `python run.py --crash-after evaluator` first |

## Project layout

```
app.py                 python app.py: the talk + the live demo (ports 8700, 8701)
search.py              Demo 1 in the terminal
run.py                 Demo 2 in the terminal
web/                   talk.html (the four sections), patterns.html (the live demo), lab.html (the guardrails lab),
                       build_code.py (refreshes the code excerpts in talk.html)
patterns/              Demo 1 in LangGraph: l0_pipeline … l3_event, world.py (demo/live worlds),
                       live.py (browser collector), score.py (grader), common.py (events), server.py
crews/                 Demo 1 in CrewAI: l0_sequential … l3_flow, contracts.py, llm.py (BridgeLLM), kit.py
lab/                   Demo 2: team, guards, runner (resume/rewind), feed, trace, server.py
                       shared: llm.py (every model call), claude_cli.py (the Claude bridge), web.py (servers)
data/shoes.json        the demo world: three stores, eight listings, five sellers, one price drop
data/live-sample.json  one real collection from Amazon.in, Flipkart and Myntra, for replay and tests
notebooks/             three CrewAI practice notebooks: article writer, customer support, financial analysis
tests/                 python -m pytest -q
requirements*.txt      core · CrewAI (optional) · live sites (optional)
```

## Where this shows up in production

| Pattern | Real-world version |
|---|---|
| Event-driven start | **AWS DevOps Agent** starts investigating the moment an alert fires. JPMorgan Chase plans agents that run for hours without human intervention. |
| Orchestrator → workers | **Amazon's** Insight Agents: a manager routes to worker agents. **Walmart's** super agents are made of smaller agents. |
| Critic / reviewer | **Cognition's** Devin Review finds about 2 bugs per PR. **Uber** runs code-review agents on LangGraph. |
| One owner per task | **UC Berkeley** studied 1,642 multi-agent runs: most failures came from design, like unclear roles. |
| Budget and stop | A team reported a **~$47,000 bill** after two agents passed requests back and forth for 11 days. |
| Human approval | **Replit's** coding agent deleted a production database during a code freeze. |

Figures are as each company or author reports them. Further reading:
[Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) (UC Berkeley) ·
[How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (Anthropic) ·
[AWS DevOps Agent](https://aws.amazon.com/fr/blogs/mt/announcing-general-availability-of-aws-devops-agent/) ·
[Insight Agents](https://www.amazon.science/publications/insight-agents-an-llm-based-multi-agent-system-for-data) (Amazon Science)
