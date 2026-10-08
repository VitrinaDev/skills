#!/usr/bin/env python3
"""Classify every exported conversation with the PROD close-analyzer prompt.

Usage: python3 billable_run.py <export-dir> [channel]

- Model: ~deepseek/deepseek-v4-flash-latest via OpenRouter (key from vitrina-app/.env).
- Same recipe as prod close-analyzer.service: system = instructions.md, user =
  dated transcript ([Customer]/[Agent] labels, last 500 msgs), temp 0, and the
  deterministic short-circuit (customer never wrote -> not billable, no LLM).
- Resume-safe: appends to <export-dir>/billable-analysis.jsonl, skips done ids.
  Re-run the script until "DONE ... err=0" (transient nulls/parse errors retry).
Cost reference: ~1,700 convs ≈ $0.40 on flash pricing.
"""
import json, subprocess, collections, concurrent.futures, os, re, threading, time, datetime, sys

APP = os.environ.get("VITRINA_APP_DIR", os.path.expanduser("~/atribu/vitrina/vitrina-app"))
EXP = sys.argv[1]
CHANNEL = sys.argv[2] if len(sys.argv) > 2 else "whatsapp"
OUT = f"{EXP}/billable-analysis.jsonl"
MODEL = "~deepseek/deepseek-v4-flash-latest"

KEY = None
with open(f"{APP}/.env") as f:
    for line in f:
        m = re.match(r"OPENROUTER_API_KEY=(.+)", line.strip())
        if m:
            KEY = m.group(1).strip().strip('"').strip("'")
assert KEY, "no OPENROUTER_API_KEY in vitrina-app/.env"

INSTR = open(f"{APP}/src/agents/close-analyzer/instructions.md").read()

convs = {c["id"]: c for c in json.load(open(f"{EXP}/conversations.json"))}
msgs = collections.defaultdict(list)
with open(f"{EXP}/messages.jsonl") as f:
    for line in f:
        m = json.loads(line)
        msgs[m["conversation_id"]].append(m)

done = set()
if os.path.exists(OUT):
    with open(OUT) as f:
        for line in f:
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                pass

WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def day_stamp(iso):
    if not iso:
        return "unknown-date"
    d = datetime.date.fromisoformat(iso[:10])
    return f"{iso[:10]} {WD[d.weekday()]}"


def transcript(c):
    out = []
    for m in msgs.get(c["id"], [])[-500:]:
        content = (m.get("content") or "").strip()
        if not content:
            continue
        role = "Customer" if m["sender_role"] == "user" else "Agent"
        out.append(f"[{day_stamp(m['created_at'])}] [{role}] {content}")
    return "\n".join(out)


now = datetime.datetime.now(datetime.timezone.utc)
lock = threading.Lock()


def call_llm(system, user):
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0, "max_tokens": 2000})
    for attempt in range(4):
        try:
            out = subprocess.check_output([
                "curl", "-s", "--fail-with-body", "--max-time", "120",
                "https://openrouter.ai/api/v1/chat/completions",
                "-H", f"Authorization: Bearer {KEY}",
                "-H", "Content-Type: application/json",
                "--data-binary", "@-"], input=payload.encode())
            r = json.loads(out)
            if "error" in r:
                raise RuntimeError(str(r["error"])[:200])
            return r
        except Exception:
            if attempt == 3:
                raise
            time.sleep(4 * (attempt + 1))


def parse_verdict(text):
    t = re.sub(r"^```(json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", t, re.S)
    return json.loads(m.group(0))


def classify(c):
    customer_spoke = any(m["sender_role"] == "user" and (m.get("content") or "").strip()
                         for m in msgs.get(c["id"], []))
    if not customer_spoke:
        row = {"id": c["id"], "billable": False, "should_close": True,
               "reason": "El cliente nunca respondió.", "deterministic": True,
               "prompt_tokens": 0, "completion_tokens": 0, "created_at": c["created_at"]}
    else:
        user = "\n".join([
            f"Current date: {day_stamp(now.isoformat())} ({now.isoformat()})",
            f"Channel: {CHANNEL}",
            f"Conversation started: {day_stamp(c['created_at'])}",
            "Resolved at: (not resolved)", "", "# Transcript", transcript(c)])
        r = call_llm(INSTR, user)
        msg = r["choices"][0]["message"]
        # flash sometimes returns null content with the verdict in reasoning
        text = msg.get("content") or msg.get("reasoning") or msg.get("reasoning_content") or ""
        v = parse_verdict(text)
        u = r.get("usage", {})
        row = {"id": c["id"], "billable": bool(v.get("billable")),
               "should_close": bool(v.get("should_close")),
               "reason": str(v.get("reason", ""))[:300], "deterministic": False,
               "prompt_tokens": u.get("prompt_tokens", 0),
               "completion_tokens": u.get("completion_tokens", 0),
               "created_at": c["created_at"]}
    with lock:
        with open(OUT, "a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


todo = [c for c in convs.values() if c["id"] not in done]
print(f"todo: {len(todo)} (done: {len(done)})", flush=True)
ok = err = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    futs = {ex.submit(classify, c): c["id"] for c in todo}
    for i, fut in enumerate(concurrent.futures.as_completed(futs)):
        try:
            fut.result()
            ok += 1
        except Exception as e:
            err += 1
            print(f"ERR {futs[fut][:8]}: {str(e)[:120]}", flush=True)
        if (i + 1) % 100 == 0:
            print(f"{i + 1}/{len(todo)} ok={ok} err={err}", flush=True)
print(f"DONE ok={ok} err={err}", flush=True)
