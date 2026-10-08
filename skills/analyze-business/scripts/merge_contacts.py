#!/usr/bin/env python3
"""Merge per-batch extracted contact data into one CSV draft (dedup by phone).

Usage: python3 merge_contacts.py <analysis-dir-with-batch-*.json> <output-csv>

Expects each batch JSON to carry a `contacts` array with the extraction-schema
fields (see references/analysis-workflow.md). Longest value wins per field;
motivo/flags/conversation accumulate with ' | '.
"""
import json, csv, glob, re, sys

adir, out = sys.argv[1], sys.argv[2]
FIELDS = ["name", "phone", "nombre_completo", "rut", "email", "fecha_nacimiento",
          "direccion", "comuna", "isapre_convenio", "motivo_consulta",
          "profesional", "servicio", "flags", "conversation"]

rows, bad = {}, []
for path in sorted(glob.glob(f"{adir}/batch-*.json")):
    try:
        data = json.load(open(path))
    except Exception as e:
        bad.append(f"{path}: {e}")
        continue
    for c in data.get("contacts", []):
        phone = re.sub(r"\D", "", str(c.get("phone") or ""))
        key = phone or (str(c.get("name", "")) + str(c.get("conversation", "")))
        cur = rows.setdefault(key, {f: "" for f in FIELDS})
        for f in FIELDS:
            v = str(c.get(f) or "").strip()
            if v and (not cur[f] or len(v) > len(cur[f])):
                if f in ("motivo_consulta", "flags", "conversation") and cur[f] and v not in cur[f]:
                    cur[f] = f"{cur[f]} | {v}"
                else:
                    cur[f] = v

with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    for key in sorted(rows, key=lambda k: rows[k]["name"]):
        w.writerow(rows[key])

n_rut = sum(1 for r in rows.values() if r["rut"])
n_mail = sum(1 for r in rows.values() if r["email"])
print(f"contacts: {len(rows)} | con rut: {n_rut} | con email: {n_mail}")
if bad:
    print("BAD FILES:", *bad, sep="\n  ")
