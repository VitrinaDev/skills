#!/usr/bin/env python3
"""Response-coverage baseline: when do customers write and how long do they wait.

Usage: python3 coverage_report.py <export-dir> [--open 8] [--close 20]
       [--staff-phones +5691...,+5692...] [--autoresp "sig1,sig2"]

- Hours/weekend segments in America/Santiago (adjust TZ below if needed).
- --staff-phones: comma-separated phones whose conversations are internal staff
  chats (exclude them — coexistence imports mix professionals into the corpus).
- --autoresp: comma-separated substrings identifying the business's out-of-hours
  autoresponder template; those messages do NOT count as a real response.
- "Consulta" = burst of customer messages until the first real team reply.
Latency table is the pre-agent baseline for the "AI answers in seconds" pitch.
"""
import json, collections, statistics, argparse
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

ap = argparse.ArgumentParser()
ap.add_argument("export_dir")
ap.add_argument("--open", type=int, default=8)
ap.add_argument("--close", type=int, default=20)
ap.add_argument("--staff-phones", default="")
ap.add_argument("--autoresp", default="")
a = ap.parse_args()
EXP = a.export_dir
CL = ZoneInfo("America/Santiago")
UTC = timezone.utc
OPEN, CLOSE = a.open, a.close

STAFF_PHONES = {p.strip() for p in a.staff_phones.split(",") if p.strip()}
_convs = json.load(open(f"{EXP}/conversations.json"))
staff_conv_ids = {c["id"] for c in _convs if c.get("phone") in STAFF_PHONES}

AUTORESP_SIG = tuple(s.strip().lower() for s in a.autoresp.split(",") if s.strip())

def parse(ts):
    return datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)

msgs = collections.defaultdict(list)
with open(f"{EXP}/messages.jsonl") as f:
    for line in f:
        m = json.loads(line)
        if m["conversation_id"] in staff_conv_ids:
            continue
        content = (m.get("content") or "").strip()
        msgs[m["conversation_id"]].append((parse(m["created_at"]), m["sender_role"], content))

def segment(dt_cl):
    wd, h = dt_cl.weekday(), dt_cl.hour
    if wd >= 5:
        return "fin de semana"
    if OPEN <= h < CLOSE:
        return f"L-V horario ({OPEN:02d}-{CLOSE:02d})"
    return f"L-V noche ({CLOSE:02d}-{OPEN:02d})"

def is_autoresp(content):
    if not AUTORESP_SIG:
        return False
    c = content.lower()
    return any(s in c for s in AUTORESP_SIG)

# build inquiries: first patient msg after a real HEAL msg (or conv start); response = next real HEAL msg
inquiries = []   # (dt_cl, segment, latency_seconds or None)
heat = collections.Counter()  # (weekday, hour) -> inbound patient msgs
total_in = 0
for cid, rows in msgs.items():
    rows.sort(key=lambda r: r[0])
    open_inq = None  # dt of first unanswered patient msg
    for dt, role, content in rows:
        dt_cl = dt.astimezone(CL)
        if role == "user":
            if content:
                total_in += 1
                heat[(dt_cl.weekday(), dt_cl.hour)] += 1
            if open_inq is None and content:
                open_inq = dt
        else:
            if is_autoresp(content):
                continue  # autoresponder is not a real answer
            if open_inq is not None:
                lat = (dt - open_inq).total_seconds()
                d = open_inq.astimezone(CL)
                inquiries.append((d, segment(d), lat))
                open_inq = None
    if open_inq is not None:
        d = open_inq.astimezone(CL)
        inquiries.append((d, segment(d), None))  # never answered

months = {i[0].strftime("%Y-%m") for i in inquiries}
full_months = sorted(months)[1:-1]
n_full = len(full_months)

print(f"conversaciones (sin staff): {len(msgs)} | mensajes de pacientes: {total_in} | consultas (bursts): {len(inquiries)}")
print(f"meses completos para promedios: {full_months}\n")

# heatmap summary
seg_in = collections.Counter()
for (wd, h), n in heat.items():
    if wd >= 5:
        seg_in["fin de semana"] += n
    elif OPEN <= h < CLOSE:
        seg_in[f"L-V horario ({OPEN:02d}-{CLOSE:02d})"] += n
    else:
        seg_in[f"L-V noche ({CLOSE:02d}-{OPEN:02d})"] += n
print("mensajes entrantes por segmento:")
for k in [f"L-V horario ({OPEN:02d}-{CLOSE:02d})", f"L-V noche ({CLOSE:02d}-{OPEN:02d})", "fin de semana"]:
    print(f"  {k:22s} {seg_in[k]:6d}  ({100*seg_in[k]/total_in:.1f}%)")

print("\nheatmap dia x bloque horario (mensajes de pacientes, hora Chile):")
DAYS = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
BLOCKS = [(0, 8, "00-08"), (8, 12, "08-12"), (12, 16, "12-16"), (16, 20, "16-20"), (20, 24, "20-24")]
print("      " + "".join(f"{b[2]:>8s}" for b in BLOCKS))
for wd in range(7):
    row = []
    for lo, hi, _ in BLOCKS:
        row.append(sum(heat[(wd, h)] for h in range(lo, hi)))
    print(f"{DAYS[wd]}   " + "".join(f"{v:8d}" for v in row))

# latency stats per segment
def fmt(sec):
    if sec is None:
        return "—"
    if sec < 3600:
        return f"{sec/60:.0f}m"
    if sec < 86400:
        return f"{sec/3600:.1f}h"
    return f"{sec/86400:.1f}d"

print("\nlatencia de PRIMERA respuesta real (autoresponder excluido):")
print(f"{'segmento':22s} {'consultas':>9s} {'/mes':>6s} {'mediana':>8s} {'p90':>8s} {'<5min':>7s} {'<1h':>6s} {'>4h':>6s} {'>12h':>6s} {'sin resp':>9s}")
for seg in [f"L-V horario ({OPEN:02d}-{CLOSE:02d})", f"L-V noche ({CLOSE:02d}-{OPEN:02d})", "fin de semana"]:
    xs = [i for i in inquiries if i[1] == seg]
    lats = [i[2] for i in xs if i[2] is not None]
    nr = sum(1 for i in xs if i[2] is None)
    if not lats:
        continue
    per_month = sum(1 for i in xs if i[0].strftime('%Y-%m') in full_months) / max(1, n_full)
    med, p90 = statistics.median(lats), sorted(lats)[int(len(lats)*0.9)]
    print(f"{seg:22s} {len(xs):9d} {per_month:6.0f} {fmt(med):>8s} {fmt(p90):>8s} "
          f"{100*sum(1 for l in lats if l<300)/len(xs):6.1f}% {100*sum(1 for l in lats if l<3600)/len(xs):5.1f}% "
          f"{100*sum(1 for l in lats if l>4*3600)/len(xs):5.1f}% {100*sum(1 for l in lats if l>12*3600)/len(xs):5.1f}% "
          f"{100*nr/len(xs):8.1f}%")

# weekend deep-dive: messages Sat/Sun answered when?
wk = [i for i in inquiries if i[1] == "fin de semana" and i[2] is not None]
if wk:
    next_bizday = sum(1 for i in wk if i[2] > 8*3600)  # rough: >8h ≈ waited for Monday/next morning
    print(f"\nfin de semana: {len(wk)} consultas respondidas; mediana {fmt(statistics.median([i[2] for i in wk]))}")
# evening callout: Fri-Sun 20:00+ and any day 20-23
eve = [i for i in inquiries if i[0].hour >= CLOSE or i[0].hour < OPEN]
eve_lat = [i[2] for i in eve if i[2] is not None]
if eve_lat:
    print(f"consultas 20:00-08:00 (todos los días): {len(eve)} | mediana espera {fmt(statistics.median(eve_lat))} | sin respuesta {100*sum(1 for i in eve if i[2] is None)/len(eve):.1f}%")

# monthly totals for the "AI improvement" line
ooh = [i for i in inquiries if i[1] != f"L-V horario ({OPEN:02d}-{CLOSE:02d})"]
ooh_month = sum(1 for i in ooh if i[0].strftime('%Y-%m') in full_months) / max(1, n_full)
slow = [i for i in inquiries if i[2] is not None and i[2] > 3600]
slow_month = sum(1 for i in slow if i[0].strftime('%Y-%m') in full_months) / max(1, n_full)
never = [i for i in inquiries if i[2] is None]
print(f"\nresumen mensual (meses completos): consultas fuera de horario ≈ {ooh_month:.0f}/mes | consultas que esperaron >1h ≈ {slow_month:.0f}/mes | nunca respondidas total: {len(never)}")
