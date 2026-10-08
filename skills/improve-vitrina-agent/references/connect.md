# Reaching a tenant: MCP, REST, SQL

Prod API: `https://api.vitrinadev.com` · MCP: `https://api.vitrinadev.com/mcp` (Streamable HTTP, stateless, Bearer auth). Local stack: `http://localhost:8080` (same paths).

## Which credential — this decides what you can do

| Credential | How it is minted | What `/mcp` offers |
|---|---|---|
| **OAuth connector** (`claude mcp add … /mcp` then `/mcp` → authorise in the browser; Claude.ai custom connector) | `oauth:Claude` key, scopes = `mcp:connector` + read preset | **Read-only curated profile (~7–45 tools): no `ai_agents_*`, `skills_*`, `kb_files_*` at all**, and `call_operation` cannot reach agent routes because no write pack mints `ai_agents:write`/`kb:write`. Useless for agent work. |
| **Scoped `sk_` API key** (Settings → API keys, minted by a member whose role holds the scopes; owners/admins do) | `POST /api-keys {name, scopes, expires_at?}` | Full hand-written catalogue filtered by scopes (518 tools with `*`). This is the path for editing agents. |

Scopes to request for agent work: `ai_agents:read, ai_agents:write, ai_agents:simulate, kb:read, kb:write, conversations:read, messages:read, tenant:read` (+ `corrections:read, corrections:write` for change requests). Scopes are `resource:action`; a key can only carry scopes the minting member holds.

### Claude Code

```bash
claude mcp add --transport http vitrina https://api.vitrinadev.com/mcp \
  --header "Authorization: Bearer sk_…"
```
Then the `mcp__vitrina__*` tools appear (`ai_agents_get`, `skills_update`, `kb_files_replace`, …). Check with `/mcp`. If only ~7 tools show, the session is on an OAuth connector key: remove it and re-add with the header.

Size limits that bite: `skills_*` content ≤ 20,000 chars; `kb_files_*` content ≤ 34 MB; `ai_agents_save_draft.system_prompt` had a 40,000-char cap before app v11.98.1 (a 66k prompt failed with `-32602 String must contain at most 40000`). On an older server, use REST `PUT /ai-agents/:id/draft` (no cap).

### REST from a shell

```bash
curl -s https://api.vitrinadev.com/api/v1/ai-agents/<id> -H "Authorization: Bearer $VITRINA_API_KEY"
curl -s -X PUT https://api.vitrinadev.com/api/v1/ai-agents/<id>/draft -H "Authorization: Bearer $VITRINA_API_KEY" \
  -H 'content-type: application/json' --data-binary @draft.json
curl -s -X PUT https://api.vitrinadev.com/api/v1/kb-files/<id>/content -H "Authorization: Bearer $VITRINA_API_KEY" \
  -F file=@doc.md
```
Routes that only exist on REST (tier `interna`, unreachable via `call_operation`): `GET /conversations/:id/agent-turn`, `GET /conversations/:id/agent-runs`, `POST /ai-agents/:id/coach/run`, `PUT /ai-agents/:id/tools`.

### Scripted MCP calls without a configured server

`scripts/mcp-call.mjs <tool> '<json-args>'` (env `VITRINA_MCP_URL`, `VITRINA_API_KEY`; resolves the MCP SDK from `VITRINA_APP_DIR`, default `~/atribu/vitrina/vitrina-app`). `scripts/mcp-call.mjs --list` prints the tool names the key can see — the fastest way to tell a connector key from a scoped key.

## Direct database access (Vitrina staff only)

The SQL recipes in `forensics.md` run against the production Postgres; everyone else reaches the same facts through the MCP/REST reads above. When applying prompt or skill text by SQL, keep the previous value in `before/` first; KB documents go through the REST replace endpoint with a short-lived `kb:write` key, revoked afterwards.
