# Session plan: from "Deep Research" to your own research team

Talk notes for the second half of the session. The first half shows the eight coordination patterns
(`python app.py`). This half shows that a product the audience already uses, Deep Research, is built from
those same patterns, and then they build a small one in `notebooks/06_build_your_own_deep_research.ipynb`.

| Part | Time | What happens |
|---|---|---|
| 1. The hook | 5 min | Show of hands, then the reveal: Deep Research is a team of agents |
| 2. How it works | 10 min | The architecture, the numbers, and which of the eight patterns it uses |
| 3. Build-along | 20 min | Walk through notebook 06, steps 1–6, running each cell |
| 4. Hands-on | 20 min | Everyone points the team at their own question and changes one thing |
| 5. Wrap-up | 5 min | When a team is worth it, and when it isn't |

## 1. The hook

Ask, and keep hands up as you go:

1. "Who has used **Deep Research** or **Research** mode, in Claude, ChatGPT, Gemini or Perplexity?"
2. "Keep your hand up if you noticed it takes **minutes**, not seconds."
3. "Keep it up if you saw it read **dozens or hundreds of sources** for one question."
4. "Why would it take that long? What do you think is happening behind the progress bar?"

Take two or three guesses, then reveal:

> When you press Research in Claude, you aren't talking to one AI. A **lead agent** reads your question,
> writes a plan, and sends out a team of **subagents** that search in parallel, each in its own context.
> They report back condensed findings, the lead decides whether it needs more, and a final agent checks the
> citations. That's a multi-agent system, and it uses five of the eight patterns you just saw.

## 2. How it works

Anthropic described the system in
[How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
(June 2025). The notebook's opening cell has the diagram. In words:

1. **The lead researcher** reads the question, thinks through an approach, and saves its plan to memory.
2. **It spawns subagents**, each with a specific task: an objective, what to search, and where its job ends.
3. **Subagents search in parallel**, each in its own context window, and return only condensed findings.
4. **The lead reviews** the findings and decides: done, or send more subagents for the gaps.
5. **A citation agent** goes through the report and the sources and ties every claim to a source.

### The numbers worth a slide

All from the Anthropic post:

| Claim | Number |
|---|---|
| Multi-agent (Claude Opus 4 lead, Claude Sonnet 4 subagents) vs single-agent Claude Opus 4, internal research eval | **90.2% better** |
| Token cost vs a normal chat: one agent / a multi-agent system | **~4× / ~15×** |
| Share of BrowseComp performance variance explained by token usage alone | **80%** |
| Research time saved by parallel subagents and parallel tool calls, complex queries | **up to 90%** |

The story the numbers tell: **a team works because it can spend more tokens in parallel**, each subagent
reading its own pages without filling the lead's context. That's also why it costs ~15× a chat.

The example that makes it concrete: asked to find the board members of every company in the Information
Technology S&P 500, the multi-agent system split the companies across subagents and found the answers; the
single agent searched one company at a time and failed.

### Which of the eight patterns are inside

Put the patterns slide back up and point at each one:

| Pattern from part one | Where it shows up in Deep Research |
|---|---|
| **Hierarchical process** | The lead plans and delegates; subagents report back |
| **Parallel fan-out / fan-in** | 3–5 subagents search at the same time; the lead waits for all of them |
| **Selective context** | Each subagent has its own context and returns only condensed findings |
| **Critic loop** | The lead reviews the findings and sends more research if there are gaps |
| **Shared state** | The plan is saved to memory, so it survives a context that grows too long |
| **Human in the loop** | Many deep research tools ask a clarifying question before they start |
| **Sequential handoff** | Research → citations → final report |
| **Event-driven** | Not used: a person starts every run. Ask the room: what would an event-driven research agent look like? (A watcher that re-runs when new papers appear.) |

### Nuances to mention

- **Not every "deep research" is multi-agent.** OpenAI describes its deep research as one model, a version of
  o3 trained with reinforcement learning to browse and reason over long tasks; it doesn't describe a team of
  subagents. Same product idea, different design: one strong agent with a long context vs a team with
  separate contexts. That's a good question for the room: which would you choose, and why?
- **Effort scales with the question.** Anthropic's prompts tell the lead: simple fact-finding, one agent with
  3–10 tool calls; a direct comparison, 2–4 subagents with 10–15 calls each; complex research, more than 10
  subagents. Early versions spawned 50 subagents for simple questions until the prompts taught the lead how
  to delegate.
- **It's a poor fit** when every agent needs the same context, when steps depend on each other, and for most
  coding tasks. Cognition's [Don't Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents)
  makes the opposite case well: subagents without shared context make conflicting decisions.

## 3. Build-along: notebook 06

`notebooks/06_build_your_own_deep_research.ipynb`. Plain Python and one LLM call function, no framework, so
every agent is visibly just a prompt and a function. Run the cells with the room; stop at each step:

| Step | Say this |
|---|---|
| The tool | "Eleven notes on *when is multi-agent worth it*, and one is a sponsored post with no evidence. Remember the fake reseller in the shopping demo? Same trap." |
| 1. One agent | "This is what you'd build first. It reads everything in one context." |
| 2. The lead | "The lead doesn't search. It writes the plan. The prompt *is* the team design." |
| 3. Researchers | "Each one reads only its own results and returns short notes. Rerun with `parallel=False` and watch the clock." |
| 4. Review | "The lead reads notes, not pages, and decides if it needs more. `max_rounds` is the way out." |
| 5. Writer | "Code checks the citations. An LLM can invent a source id; a set difference can't." |
| 6. Scoreboard | "More calls, more tokens, but look at *biggest prompt*: no agent had to read everything." |

## 4. Hands-on

Everyone does **Your turn 1**: set `SEARCH = "wikipedia"`, write their own question, run `deep_research()`.
Good questions have independent parts: comparisons, pros and cons, "how did X change over time".

Then each person picks one change:

- **Add a skeptic** to the team (edit `LEAD_PLAN_PROMPT`).
- **Let the lead choose how many researchers** (effort scaling).
- **Ask me first**: run `clarify_then_research()`.
- **A cheaper model for the researchers**, a strong one for the lead.
- **A real critic** that checks each finding against its source.

Or use the mini app at the end of the notebook: a question box, sliders for researchers and rounds, and a
Research button.

Ask two or three people to share: what question, what they changed, and what the scoreboard said.

**If the Wi-Fi or keys fail:** the `library` search works offline. Wikipedia can rate-limit a whole room on one
network (HTTP 429): the notebook prints the error and carries on, so switch back to `library` or retry. For
no key at all, use Ollama.

## 5. Wrap-up

Three lines to end on:

1. **A multi-agent system is prompts plus code that decides who runs when.** You just built one in a notebook, with no framework.
2. **Teams win when the work splits into parallel parts and there's more to read than one context holds.**
3. **They cost ~15× a chat, so start with one agent, measure, and add agents only when a check you care about
   fails.**

## Sources

- Anthropic, [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (June 2025)
- Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (December 2024)
- Cognition, [Don't Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents) (June 2025)
- Cemri et al., [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) (2025)
- OpenAI, [Introducing deep research](https://openai.com/index/introducing-deep-research/) (February 2025)
