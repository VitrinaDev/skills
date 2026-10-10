# Conversation forensics — reading what the agent actually saw and did

Ids: REST `:id` and MCP string ids accept the UUID or the display id (`C-1234`, tickets `T-`, leads `L-`). Fields typed `.uuid()` (agent ids) do not.

## What one agent turn leaves in `message`

Columns: `sender_type` (`contact | ai_agent | human_user | system | api_key`), `sender_role`, `type`, `content`, `tool_calls jsonb`, `tool_call_id`, `metadata jsonb`, `created_at`. Per turn, in order:

| Row | sender_type / role / type | Content |
|---|---|---|
| reasoning | `system` / `assistant` / `reasoning` | model thoughts, ≤ 4000 chars (hidden from the customer and from history replay) |
| tool call | `ai_agent` / – / `tool_calls` | `tool_calls = [{id, type:'function', function:{name, arguments:"<json string>"}}]` |
| tool result | `system` / `tool` / `tool` | `tool_call_id` pairs it with the call; content = the tool's output (`{ok:false, error:'skill_not_loaded'}`, `could not reach …`, slots, KB chunks) |
| reply | `ai_agent` / – / `text` | the one persisted reply (split on `---` only at send time); `metadata.ai_agent_version_id` (often null — publish does not stamp it), `context_through`, `chunk_wamids` |

Each revision pass (freshness, pending-question, price gate) appends another reasoning/tool set before the final reply. Customer rows are `sender_type='contact'`; inbound button taps and ad context land in `metadata`.

## Ways to read a thread

Fastest path for one conversation: `conversations_export {id, format:"json"}` — accepts the display id, returns contact, ticket, attributes and every message row (10k chars for a short thread). `tickets_messages_thread` is keyed by **ticket** (`T-n`); a `C-n` there fails with `invalid input syntax for type uuid`.


- Connector: `call_operation conversation_messages_list {params:{id, order:"asc", limit≤200, cursor?}}` (tool fields intact), `conversation_export_list {params:{id, format:"json"}}`, `conversation_ai_status_list {params:{id}}`; named `conversations_list`, `conversations_linked_records`. `conversation_agent_turn_list {params:{id}}` (below) is published too; only the agent-runs route needs an `sk_` key.
- MCP (`sk_` key) `tickets_messages_thread {ticket_id, limit≤2000}` (keeps `type`, `tool_calls`, `tool_call_id`), `conversations_export {id, format: json}` (use JSON — markdown labels reasoning rows as "assistant"), `conversations_list {status?, channel?, search?, limit≤100}`, `conversations_linked_records {id}`.
- REST `GET /conversations/:id/messages?limit≤200&order=asc` (tool fields intact, plus `author`), `GET /conversations/:id/export?format=json`.
- **`GET /conversations/:id/agent-turn`** (`conversations:read`; connector `call_operation conversation_agent_turn_list {params:{id}}`, no model involved and none returned): the exact assembled `system_prompt`, replayed `messages`, `history_summary`, full `tools` definitions, `skills`, `knowledge_base`, `attributes`, `open_leads`, `previous_conversations`, `business_hours`, or `human_only` + `silence_reason` when the agent would not run. Reproduces the *current* config, not the one at the time of the turn.
- `GET /conversations/:id/agent-runs?limit≤20` → `agent_run` (status, timings; `sk_` key only — tokens, cost and model are no longer returned) with `agent_run_step` rows (`kb_lookup | tool_call | reply | ticket_change | lead_change | handoff | resolve | snooze | reasoning`).
- `GET /conversations/:id/ai-status` → why the AI is silent (`explainAiSilence`); `POST /copilot/explain {conversation_id, message_id}` → "why did it reply this".
- Conversation state: `handler` is `bot | human | external`; `assignee_user_id`, `ai_keep_with_human`, `awaiting_human_since`, `status` (`open|pending|snoozed|resolved|closed`), `summary` (close summary), `billable` + `billing_reason` (close analyzer), `conversation_attribute {key, value, source agent|tool|admin|system}`.

## Reading a failure

1. Find the failing reply row; walk **up** to its reasoning and tool rows: did it call `load_skill` / `search_knowledge_base`? With what query? What came back?
2. Compare the reply with the tool results — an amount, hour or name absent from every result and from the KB is a hallucination (the price gate should have blocked a bare amount; if it passed, the amount was "grounded" somewhere — find where).
3. Count steps: ≥ 8 tool calls in one turn = step cap; the last pass is a no-tools synthesis.
4. Check the prompt the turn saw (`agent-turn`): is the rule you expect actually in the prompt/skill content, or only in a KB doc the agent did not search?
5. Check `latency_metric` (kind `agent_turn`, revision flags; `analytics_latency` over MCP) for the turn's latency and whether a timeout explains a degraded reply. A tenant-facing report says "a platform timeout", never which model or provider, and never a cost figure (none is exposed). Vitrina staff can also read `model_usage` by SQL (recipe below) to see whether a provider swap or timeout explains it — internal only.
6. Mejoras: `conversation_review` (`outcome resolved_by_ai|resolved_by_human|unresolved|abandoned|noise`, `handoff`, `summary`) and `agent_finding` already classify recent conversations — read them before re-deriving.

## SQL recipes (direct database access, read-only)

Thread with tool calls:
```sql
select created_at, sender_type, sender_role, type,
       left(content, 300) as content,
       tool_calls->0->'function'->>'name' as tool, tool_call_id
from message
where conversation_id = (select id from conversation where display_id = 'C-1234' and tenant_id = '<tenant>')
order by created_at;
```
Recent failing tool results across the tenant (last 2 days):
```sql
select m.created_at, c.display_id, left(m.content, 160)
from message m join conversation c on c.id = m.conversation_id
where m.tenant_id = '<tenant>' and m.type = 'tool' and m.created_at > now() - interval '2 days'
  and (m.content ilike '%"ok":false%' or m.content ilike '%error%')
order by m.created_at desc limit 50;
```
Which skills got loaded (and which never do):
```sql
select tool_calls->0->'function'->>'arguments' as args, count(*)
from message where tenant_id = '<tenant>' and type = 'tool_calls'
  and tool_calls->0->'function'->>'name' = 'load_skill' and created_at > now() - interval '14 days'
group by 1 order by 2 desc;
```
KB retrieval log (what the agent searched and how many chunks came back):
```sql
select created_at, query_text, top_k, array_length(chunk_ids,1) as hits, latency_ms, conversation_id
from kb_retrieval_log where tenant_id = '<tenant>' order by created_at desc limit 50;
```

Turn cost/latency (Vitrina staff only — model, provider and cost are internal and never go into a tenant-facing report):
```sql
select created_at, model, input_tokens, output_tokens, cost_usd, latency_ms, metadata->>'steps' steps, metadata->>'provider' provider
from model_usage where conversation_id = '<uuid>' order by created_at;
```
The recipes were run against prod on 2026-10-08.
