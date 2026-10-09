# Reaching a tenant: connector, API key, REST, SQL

Prod API: `https://api.vitrinadev.com` · MCP: `https://api.vitrinadev.com/mcp` (Streamable HTTP, stateless). Local stack: `http://localhost:8080` (same paths).

## Two credentials — the connector comes first

| Credential | How you get it | What `/mcp` offers |
|---|---|---|
| **Connector** (OAuth, the main path) | Vitrina → **Configuración → Conectar tu IA (MCP)**, or add the MCP URL in Claude / Claude Code / Cursor and sign in. The consent screen lists write packs; tick **«Agentes de IA»** to edit agents. | A curated read profile (agents, skills, KB, findings, change requests, scenario results, inbox, insights) plus `search_operations` / `describe_operation` / `call_operation`. Every write goes through `call_operation`, only in the packs ticked, only where the person's role already reaches. |
| Scoped `sk_` API key (secondary) | **Configuración → Claves de API** (a member whose role holds the scopes) | The full catalogue filtered by scopes (~500 tools: `ai_agents_save_draft`, `skills_update`, `kb_files_replace`, `ai_agent_simulate`, …). For scripts and automation, and for what no pack grants: simulating and running scenarios (`ai_agents:simulate`), uploading or replacing KB files from a chat (multipart), audit reads outside the profile (`analytics_cost`, `worker_failures_list`, `conversations_export`). |

Write packs a connector can carry: «Contactos», «Leads», «Casos», «Conversaciones», **«Agentes de IA»** (`ai_agents:write` + `kb:write` + `corrections:write`: the draft, publish, versions, skills, knowledge links, change requests), «Agenda», «Catálogo», «Mensajes a clientes», plus the economics checkbox. The agent reads (`ai_agents:read`, `kb:read`, `corrections:read`) come with the connection for owners and admins. `ai_agents:simulate` is in no pack: a connector cannot simulate or start scenario runs; it reads their results.

In Claude chat (claude.ai web and desktop) a custom connector is OAuth-only and takes no headers, so an `sk_` key cannot be used there. Use the connector.

## Which one is this session on?

1. `ai_agents_save_draft` among the tools → `sk_` key. Use the MCP tool names in [`surface.md`](surface.md).
2. `ai_agents_get` and `call_operation` present, `ai_agents_save_draft` absent → connector. Run `describe_operation {operation_id:"ai_agent_draft_replace"}`:
   - it answers with the operation → «Agentes de IA» is granted; edit with the `call_operation` ids in [`surface.md`](surface.md).
   - it answers `Unknown operation …` → the pack was not ticked, the connection predates it, or the person's role cannot edit agents (owners and admins can). Reads still work.
3. No `ai_agents_get` at all (only a handful of Vitrina tools) → a connector minted before the agent reads existed, or a member whose role lacks `ai_agents:read`. Reconnect; if it persists, the role is the limit (owners and admins hold it).
4. No Vitrina tools → not connected; connect below.

A write answering `403` with an insufficient-scope error means the person's role does not hold that scope; reconnecting will not help, an owner or admin must do it.

**To add «Agentes de IA» to an existing connection:** in Vitrina, **Configuración → Conectar tu IA → Desconectar** on that app (or switch «Agentes de IA» on for that connection there, when available), then connect again from Claude and tick «Agentes de IA» on the consent screen. Tell the user exactly this; it takes a minute.

## Connecting

- **Claude chat (web/desktop):** claude.ai → Customize → Connectors (`claude.ai/customize/connectors`) → add custom connector → URL `https://api.vitrinadev.com/mcp` → sign in to Vitrina → tick «Agentes de IA» → allow.
- **Claude Code:** `claude mcp add --transport http vitrina https://api.vitrinadev.com/mcp`, then `/mcp` → `vitrina` → Authenticate → sign in → tick «Agentes de IA».
- **Cursor and other MCP clients:** add the same URL as a remote (HTTP) MCP server and sign in when prompted; Vitrina's «Conectar tu IA» page shows the exact steps per client.
- **`sk_` key (scripts, automation):** `claude mcp add --transport http vitrina https://api.vitrinadev.com/mcp --header "Authorization: Bearer sk_…"` and skip the Authenticate step (it would swap in a connector). Scopes for full agent work: `ai_agents:read, ai_agents:write, ai_agents:simulate, kb:read, kb:write, conversations:read, messages:read, tenant:read, contacts:read, tickets:read, analytics:read, corrections:read, corrections:write, worker_failures:read, appointment_types:read, clinic:read, pipelines:read, teams:read, routing:read, leads:read, appointments:read, ads:read, healthatom:read, campaigns:read, followups:read, webhooks:read`. A key carries only scopes its minting member holds.

## REST from a shell (`sk_` key)

```bash
curl -s https://api.vitrinadev.com/api/v1/ai-agents/<id> -H "Authorization: Bearer $VITRINA_API_KEY"
curl -s -X PUT https://api.vitrinadev.com/api/v1/ai-agents/<id>/draft -H "Authorization: Bearer $VITRINA_API_KEY" \
  -H 'content-type: application/json' --data-binary @draft.json
curl -s -X PUT https://api.vitrinadev.com/api/v1/kb-files/<id>/content -H "Authorization: Bearer $VITRINA_API_KEY" \
  -F file=@doc.md
```
REST-only routes (tier `interna`, never reachable through `call_operation`): `GET /conversations/:id/agent-turn`, `GET /conversations/:id/agent-runs`, `POST /ai-agents/:id/coach/run`, the scenario and suite writes and runs.

### Scripted MCP calls without a configured server

`scripts/mcp-call.mjs <tool> '<json-args>'` with `VITRINA_API_KEY` (`VITRINA_MCP_URL` for a non-production host). It needs the MCP SDK installed once: `npm i -g @modelcontextprotocol/sdk` (the script finds the global install itself). `scripts/mcp-call.mjs --list` prints the tool names the key can see.

## Direct database access (Vitrina staff only)

The SQL recipes in `forensics.md` run against the production Postgres; everyone else reaches the same facts through the MCP/REST reads above. When applying prompt or skill text by SQL, keep the previous value in `before/` first; KB documents go through the REST replace endpoint with a short-lived `kb:write` key, revoked afterwards.
