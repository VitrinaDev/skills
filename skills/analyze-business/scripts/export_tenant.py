#!/usr/bin/env python3
"""Export a tenant's conversations+messages from prod Supabase (READ-ONLY) to local files.

Usage: python3 export_tenant.py <tenant-slug-or-uuid> <output-dir>

Writes <output-dir>/conversations.json and <output-dir>/messages.jsonl.
Resume-safe: re-running overwrites cleanly (queries are cheap reads).
Uses curl (python urllib gets 403'd by Cloudflare on api.supabase.com).
"""
import json, subprocess, sys, time, os, re

PROJECT = os.environ.get("VITRINA_SUPABASE_PROJECT_REF", "")  # production Supabase project ref (Vitrina staff)
if not PROJECT:
    sys.exit("set VITRINA_SUPABASE_PROJECT_REF to the production Supabase project ref")
TOKEN = subprocess.check_output(
    ["security", "find-generic-password", "-s", "Supabase CLI", "-w"]).decode().strip()
URL = f"https://api.supabase.com/v1/projects/{PROJECT}/database/query"


def q(sql):
    body = json.dumps({"query": sql})
    for attempt in range(4):
        try:
            out = subprocess.check_output([
                "curl", "-s", "--fail-with-body", "-X", "POST", URL,
                "-H", f"Authorization: Bearer {TOKEN}",
                "-H", "Content-Type: application/json",
                "--data-binary", "@-"], input=body.encode(), timeout=180)
            return json.loads(out)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))


def main():
    ident, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)

    if re.fullmatch(r"[0-9a-f-]{36}", ident):
        tenant_id = ident
    else:
        rows = q(f"select id from tenant where slug='{ident}' or name ilike '%{ident}%'")
        assert len(rows) == 1, f"tenant lookup for {ident!r} returned {rows}"
        tenant_id = rows[0]["id"]
    print(f"tenant: {tenant_id}", flush=True)

    convs = q(f"""
select c.id, c.created_at, c.last_message_date, c.channel,
       ct.id as contact_id, ct.name as contact_name, ct.phone, ct.email,
       (select count(*) from message m where m.conversation_id=c.id) as msg_count
from conversation c join contact ct on ct.id=c.contact_id
where c.tenant_id='{tenant_id}' order by c.created_at""")
    with open(f"{outdir}/conversations.json", "w") as f:
        json.dump(convs, f, ensure_ascii=False)
    print(f"conversations: {len(convs)}", flush=True)

    BATCH = 40
    with open(f"{outdir}/messages.jsonl", "w") as f:
        for i in range(0, len(convs), BATCH):
            ids = ",".join(f"'{c['id']}'" for c in convs[i:i + BATCH])
            rows = q(f"""
select m.conversation_id, m.created_at, m.sender_role, m.type,
       left(m.content, 4000) as content
from message m where m.conversation_id in ({ids})
order by m.conversation_id, m.created_at""")
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"batch {i // BATCH + 1}/{(len(convs) + BATCH - 1) // BATCH}: {len(rows)} msgs", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
