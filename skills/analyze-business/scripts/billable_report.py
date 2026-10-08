#!/usr/bin/env python3
"""Monthly billable stats + revenue + agent-model cost estimate.

Usage: python3 billable_report.py <export-dir> [--uf-per-conv 0.012] [--uf-clp 39300]
       [--usd-clp 950] [--in-price 0.10] [--out-price 0.60] [--cache-price 0.01]

Months come from MESSAGE dates, never conversation.created_at (coexistence
imports stamp every conversation with the import date). "Active billable" =
conversations with >=1 patient message that month whose verdict is billable —
that is the monthly invoice proxy. Partial first/last months are excluded from
the average automatically (months at the edges of the data range).

Model-cost assumptions (override in flags if needed): turns = patient msgs x0.7
(coalescing), 2.2 LLM calls/turn, 15k input tokens/call (80% cache read),
500 output tokens/call. Prints the cost at the given prices and at 2x prices
(= "sin oferta" when you pass the discounted prices).
"""
import json, collections, argparse

ap = argparse.ArgumentParser()
ap.add_argument("export_dir")
ap.add_argument("--uf-per-conv", type=float, default=0.012)
ap.add_argument("--uf-clp", type=float, default=39_300)
ap.add_argument("--usd-clp", type=float, default=950)
ap.add_argument("--in-price", type=float, default=0.10)
ap.add_argument("--out-price", type=float, default=0.60)
ap.add_argument("--cache-price", type=float, default=0.01)
a = ap.parse_args()
EXP = a.export_dir

rows = {}
for l in open(f"{EXP}/billable-analysis.jsonl"):
    r = json.loads(l)
    rows[r["id"]] = r
rows = list(rows.values())
bill_ids = {r["id"] for r in rows if r["billable"]}

pm = collections.Counter()
active = collections.defaultdict(set)
with open(f"{EXP}/messages.jsonl") as f:
    for line in f:
        m = json.loads(line)
        if m["sender_role"] == "user" and (m.get("content") or "").strip():
            mo = m["created_at"][:7]
            pm[mo] += 1
            active[mo].add(m["conversation_id"])

n, nb = len(rows), len(bill_ids)
det = sum(1 for r in rows if r.get("deterministic"))
pt = sum(r.get("prompt_tokens", 0) for r in rows)
ct = sum(r.get("completion_tokens", 0) for r in rows)
print(f"conversations: {n} | billable: {nb} ({100 * nb / n:.1f}%) | never-replied: {det}")
print(f"classification tokens: {pt / 1e6:.2f}M in + {ct / 1e6:.2f}M out"
      f" (deepseek flash ≈ ${pt / 1e6 * 0.09 + ct / 1e6 * 0.18:.2f})")

months = sorted(active)
full = months[1:-1] if len(months) > 2 else months
print("\nmes        activas  billables")
for mo in months:
    tag = "" if mo in full else "  (parcial)"
    print(f"{mo}   {len(active[mo]):7d}  {len(active[mo] & bill_ids):9d}{tag}")

avg_bill = sum(len(active[mo] & bill_ids) for mo in full) / max(1, len(full))
rev_clp = avg_bill * a.uf_per_conv * a.uf_clp
print(f"\npromedio meses completos: {avg_bill:.0f} convs billables/mes")
print(f"ingreso: {avg_bill:.0f} x {a.uf_per_conv} UF = CLP {rev_clp:,.0f}/mes (~USD {rev_clp / a.usd_clp:,.0f})")

avg_pm = sum(pm[mo] for mo in full) / max(1, len(full))
turns = avg_pm * 0.7
calls = turns * 2.2
fresh, cache, out = calls * 15_000 * 0.2, calls * 15_000 * 0.8, calls * 500
print(f"\nmodelo: {avg_pm:.0f} msgs cliente/mes -> {turns:.0f} turnos -> {calls:.0f} llamadas LLM")
print(f"tokens/mes: {fresh / 1e6:.1f}M fresh + {cache / 1e6:.1f}M cache + {out / 1e6:.1f}M out")
for mult, label in [(1, "precio dado"), (2, "precio x2 (sin oferta)")]:
    c = (fresh / 1e6) * a.in_price * mult + (cache / 1e6) * a.cache_price * mult + (out / 1e6) * a.out_price * mult
    cn = ((fresh + cache) / 1e6) * a.in_price * mult + (out / 1e6) * a.out_price * mult
    print(f"{label}: USD {c:.2f}/mes con cache | USD {cn:.2f}/mes sin cache"
          f" | USD {c / max(1, avg_bill):.3f}-{cn / max(1, avg_bill):.3f} por conv billable")
