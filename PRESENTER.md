# Presenter runbook: 13 minutes

For Jaskamal. Comes right after Rahul's n8n demo, which ends on the human approval gate.
Two terminals side by side, font size 20+, dark theme.
Terminal A runs the lab. Terminal B is for `tools/drop_price.py` and `diff`.

## Before you go on stage

```bash
cd autonomy-lab && source .venv/bin/activate
export LAB_LLM=offline LAB_DELAY=0.7
python tools/drop_price.py --reset
python run.py 3 && python run.py 4 --chaos    # quick check, then clear the screen
```

Have `steps/step3_owner.py` open in an editor, scrolled to the `# NEW` block.

## Run sheet

| Min | Do | Say |
|---|---|---|
| 0:00 | **A:** `python run.py 1` (it waits) | "Rahul's flow starts when a person fills a form. This one has no form. The agents are watching a store feed." |
| 0:30 | **B:** `python tools/drop_price.py` | "A price just changed in the world." |
| 1:00 | Point at the summary: **Human inputs 0** | "Nobody asked. The work started because something changed." |
| 2:30 | **A:** `python run.py 2` | "Now two agents react to the same event. Both were told purchases are their job." |
| 3:30 | Point at the cart: **2 items**, tokens climbing | "They argue. Both add to cart. Nobody decides." |
| 4:30 | Point at **KILLED** | "The only thing that stopped them was the framework's recursion limit. That's luck, not design." |
| 5:30 | Show the `claim()` function in the editor (5 lines) | "Fix 1: one owner per task. First claim wins. Code enforces it, not the prompt." |
| 6:30 | **A:** `python run.py 3` | "Same agents, same prompts. One stands down. One item." |
| 7:30 | **A:** `python run.py 3 --chaos` | "But what if the owner keeps re-checking prices forever?" Let it run a few seconds. |
| 8:30 | Show `within_budget()` + `escalate()` | "Fix 2: a budget on turns and tokens. When it's hit, stop and hand over to a human." |
| 9:30 | **A:** `python run.py 4 --chaos` | "Six turns, then it stops by itself and escalates." |
| 11:00 | **B:** `diff steps/step2_broken.py steps/step4_budget.py \| head -40` | "Two fixes, two small functions. All in code, none in the prompt." |
| 12:00 | Closing | "Agents can start on their own. Code decides who owns the work and when to stop. And as Rahul showed, a human decides when money moves." |

## If something goes wrong

| Problem | Do this |
|---|---|
| Step 1 doesn't trigger | Ctrl+C, then `python run.py 1 --auto-drop 2` |
| Feed file got corrupted | `python tools/drop_price.py --reset` |
| Running behind | Skip `run.py 3 --chaos`. Go straight to `run.py 4 --chaos`. |
| Running far behind | Run only steps 2 and 4, and say fix 1 is in the repo. |
| Output too fast/slow | `export LAB_DELAY=0.4` or `1.0` |

## Live coding (optional)

To type fix 1 live instead of switching files: open `step2_broken.py`, paste the `claim()` function and the 6-line block from `step3_owner.py` that calls it. If it breaks, run `python run.py 3`. The finished file is always there.
