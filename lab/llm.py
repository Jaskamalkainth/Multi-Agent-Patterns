"""One function every agent calls: ask(agent, role, context, actions).

Returns (reply, tokens) where reply = {"action": <one of actions>, "say": <short text>}.

LAB_LLM=offline   (default) scripted replies. Same result every run. Use this on stage.
LAB_LLM=openai    any OpenAI-compatible server: OpenAI, vLLM, Ollama, LM Studio.
                  Set OPENAI_API_KEY, LAB_MODEL, and OPENAI_BASE_URL if not OpenAI.
LAB_LLM=anthropic Set ANTHROPIC_API_KEY and LAB_MODEL.

Real models are not deterministic. The guardrails in steps 3-5 are written in
code, so they hold whatever the model says. That is the point of the lab.
"""
import json
import os
import re

MODE = os.getenv("LAB_LLM", "offline").lower()


def ask(agent, role, context, actions):
    if MODE == "offline":
        reply = _offline(agent, context)
        tokens = _estimate(role, context, reply)
    else:
        reply, tokens = _real(agent, role, context, actions)
    if reply.get("action") not in actions:
        bad = reply.get("action")
        reply = {"action": actions[0], "say": f"(model gave action {bad!r}, using {actions[0]!r}) {reply.get('say', '')}"}
    return reply, tokens


# ---------------------------------------------------------------- offline script

def _offline(agent, ctx):
    ev = ctx.get("event", {})
    name, price = ev.get("name", "item"), ev.get("price")

    if agent == "watcher":
        return {"action": "trigger",
                "say": f"{name} dropped ₹{ev.get('old_price')} → ₹{price}. Matches the saved goal. Waking the team."}

    if agent == "evaluator":
        return {"action": "recommend",
                "say": f"Recommend {name} at ₹{price}: black, running shoe, under ₹{ev['goal']['max_price']:,}."}

    # deal / budget agents
    turn = ctx.get("turn", 0)
    other = ctx.get("other_last") or {}
    owner = ctx.get("owner")

    if ctx.get("owner_rule"):
        if owner and owner != agent:
            return {"action": "stand_down", "say": f"{owner.title()} agent owns this task. Standing down."}
        if owner == agent:
            if ctx.get("chaos") and agent == "deal":
                return {"action": "recheck", "say": "Price might drop further. Re-checking all stores…"}
            return {"action": "buy", "say": f"I own this task. Buying {name} at ₹{price}."}
        return {"action": "claim", "say": "Claiming the purchase task."}

    # No ownership rule: both agents think the purchase is theirs.
    if not other:
        return {"action": "claim", "say": "Good deal. I'll handle this purchase."}
    if not ctx.get("i_added") and turn >= 3:
        return {"action": "add_to_cart", "say": "Adding to cart now before the price goes back up."}
    lines = ["No, purchases are my job.", "You're wrong, I own this.", "Re-planning… still mine.",
             "I was assigned purchases.", "Please stand down."]
    return {"action": "dispute", "say": lines[turn % len(lines)]}


def _estimate(role, ctx, reply):
    # Rough token count: prompt + context + reply, about 4 characters per token.
    text = role + json.dumps(ctx, ensure_ascii=False) + json.dumps(reply, ensure_ascii=False)
    return 220 + len(text) // 4


# ---------------------------------------------------------------- real models

def _prompt(role, context, actions):
    return (
        f"{role}\n\nCurrent situation (JSON):\n{json.dumps(context, ensure_ascii=False)}\n\n"
        f"Reply with ONLY a JSON object: {{\"action\": one of {actions}, \"say\": \"one short sentence\"}}"
    )


def _parse(text):
    match = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(match.group(0)) if match else {"say": text}
    except json.JSONDecodeError:
        return {"say": text}


def _real(agent, role, context, actions):
    model = os.environ["LAB_MODEL"]
    prompt = _prompt(role, context, actions)
    if MODE == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        res = client.messages.create(model=model, max_tokens=200,
                                     messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in res.content if getattr(b, "type", "") == "text")
        tokens = res.usage.input_tokens + res.usage.output_tokens
    else:
        from openai import OpenAI
        client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL") or None)
        res = client.chat.completions.create(model=model, max_tokens=200, temperature=0.2,
                                             messages=[{"role": "user", "content": prompt}])
        text = res.choices[0].message.content or ""
        tokens = res.usage.total_tokens if res.usage else _estimate(role, context, {"say": text})
    return _parse(text), tokens
