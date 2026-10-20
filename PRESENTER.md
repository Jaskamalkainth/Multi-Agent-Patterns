# Presenter runbook: 15 minutes

For Jaskamal. Two terminals side by side, font size 20+, dark theme.
Terminal A runs the lab. Terminal B is for `tools/drop_price.py` and `diff`.

## Before you go on stage

```bash
cd autonomy-lab && source .venv/bin/activate
export LAB_LLM=offline LAB_DELAY=0.7
python tools/drop_price.py --reset
python run.py 3 && python run.py 5 --yes      # quick check, then clear the screen
```

Have `steps/step3_owner.py` open in an editor, scrolled to the `# NEW` block.

## Run sheet

| Min | Do | Say |
|---|---|---|
| 0:00 | **A:** `python run.py 1` (it waits) | "No prompt, no form. The agents are watching a store feed." |
| 0:30 | **B:** `python tools/drop_price.py` | "A price just changed in the world." |
| 1:00 | Point at the summary: **Human inputs 0** | "Nobody asked. The work started because something changed." |
| 3:00 | **A:** `python run.py 2` | "Now two agents. Both were told purchases are their job." |
| 4:00 | Point at the cart: **2 items**, tokens climbing | "They argue. Both add to cart. Nobody decides." |
| 5:00 | Point at **KILLED** | "The only thing that stopped them was the framework's recursion limit. That's luck, not design." |
| 6:00 | Show the `claim()` function in the editor (5 lines) | "Fix 1: one owner per task. First claim wins. Code enforces it." |
| 7:00 | **A:** `python run.py 3` | "Same agents, same prompts. One stands down. One item." |
| 8:00 | **A:** `python run.py 3 --chaos` | "But what if the owner keeps re-checking forever?" Let it run a few seconds. |
| 9:00 | Show `within_budget()` + `escalate()` | "Fix 2: a budget. When it's hit, stop and ask a human." |
| 9:30 | **A:** `python run.py 4 --chaos` | "Six turns, then it stops by itself." |
| 11:00 | Show `interrupt(proposal)` | "Fix 3: money moves only when a human says yes." |
| 11:30 | **A:** `python run.py 5`, type `approve` | "The graph paused, saved its state, and resumed when I answered." |
| 13:00 | **B:** `diff steps/step2_broken.py steps/step5_approval.py \| head -40` | "Three fixes: three small functions. All in code, none in the prompt." |
| 14:00 | Closing | "Agents can start on their own. Code decides what they're allowed to do. A human decides when money moves." |

## If something goes wrong

| Problem | Do this |
|---|---|
| Step 1 doesn't trigger | Ctrl+C, then `python run.py 1 --auto-drop 2` |
| Feed file got corrupted | `python tools/drop_price.py --reset` |
| Running behind | Skip `run.py 3 --chaos`. Go straight to `run.py 4 --chaos`. |
| Running far behind | Run only steps 2 and 5, and say the other fixes are in the repo. |
| Output too fast/slow | `export LAB_DELAY=0.4` or `1.0` |

## Live coding (optional)

If you want to type a fix live instead of switching files: open `step2_broken.py`, paste the `claim()` function and the 6-line block from `step3_owner.py` that calls it. If it breaks, run `python run.py 3`. The finished file is always there.
