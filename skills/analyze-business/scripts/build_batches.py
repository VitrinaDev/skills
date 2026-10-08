#!/usr/bin/env python3
"""Build size-balanced, human-readable transcript batches for subagent analysis.

Usage: python3 build_batches.py <export-dir> <business-label> [target-bytes]

Reads conversations.json + messages.jsonl, writes <export-dir>/batches/batch-NN.txt.
~230KB per batch ≈ 60k tokens: one sonnet subagent reads one batch comfortably.
Roles are labeled <BUSINESS-LABEL> (staff) and PACIENTE/CLIENTE (customer).
"""
import json, os, sys, collections

exp = sys.argv[1]
label = (sys.argv[2] if len(sys.argv) > 2 else "NEGOCIO").upper()
TARGET = int(sys.argv[3]) if len(sys.argv) > 3 else 230_000
OUT = f"{exp}/batches"
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(f"{OUT}/{f}")

convs = json.load(open(f"{exp}/conversations.json"))
msgs = collections.defaultdict(list)
with open(f"{exp}/messages.jsonl") as f:
    for line in f:
        m = json.loads(line)
        msgs[m["conversation_id"]].append(m)


def render(c):
    out = [f"\n{'=' * 70}\nCONVERSACION {c['id'][:8]} | contacto: {c.get('contact_name') or 'sin nombre'}"
           f" | tel: {c.get('phone') or '-'} | inicio: {c['created_at'][:10]} | msgs: {c['msg_count']}\n{'=' * 70}\n"]
    last_day = None
    for m in msgs.get(c["id"], []):
        day = m["created_at"][:10]
        if day != last_day:
            out.append(f"--- {day} ---\n")
            last_day = day
        who = "CLIENTE" if m["sender_role"] == "user" else label
        content = (m.get("content") or f"[{m['type']}]").strip()
        out.append(f"[{m['created_at'][11:16]}] {who}: {content}\n")
    return "".join(out)


ordered = sorted(convs, key=lambda c: c["created_at"])
batch_no, buf, size, counts = 1, [], 0, []


def flush():
    global batch_no, buf, size
    if buf:
        with open(f"{OUT}/batch-{batch_no:02d}.txt", "w") as f:
            f.write("".join(buf))
        counts.append(size)
        batch_no += 1
        buf, size = [], 0


for c in ordered:
    t = render(c)
    if size + len(t) > TARGET and buf:
        flush()
    buf.append(t)
    size += len(t)
flush()
sizes = sorted(counts)
print(f"batches: {len(counts)} | bytes min/med/max: {sizes[0]}/{sizes[len(sizes) // 2]}/{sizes[-1]}")
