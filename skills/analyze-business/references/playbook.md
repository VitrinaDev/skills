# Audit playbook — tools, classification, filing

All tools below need an `sk_` API key (not an OAuth connector). Ids accept UUIDs; conversation ids also accept `C-1234`.

## Reading tools

| Need | Tool / route | Inputs |
|---|---|---|
| Agents | `ai_agents_list`, `ai_agents_get {id}` | live + draft config, `behavior_policies`, model |
| Health numbers | `ai_agents_metrics_get {id, days≤90}`, `insights_ai_agents_get`, `insights_conversations_get`, `insights_csat_get`, `insights_sla_get` (`from`/`to` or window args) | |
| Cost / latency | `analytics_cost {from, to?}`, `analytics_latency {kind?, since_minutes≤10080}` | kind `agent_turn` |
| Platform reviews | `coach_reviews_list {ai_agent_id, limit≤200 — use 50, 200 is ~200k chars, with_handoff?}` — outcome `resolved_by_ai | resolved_by_human | unresolved | abandoned | noise`, summary, handoff | |
| Findings | `coach_findings_list {ai_agent_id, status? active|open|investigating|investigated|addressed|dismissed|all}`, `coach_finding_get {ai_agent_id, finding_id}` (evidence + proposals), `coach_finding_investigate` (queues the investigator, needs `ai_agents:simulate`) | |
| Proposals | `coach_proposals_list {ai_agent_id?, status? proposed|accepted|rejected}`, `coach_proposal_decide {proposal_id, decision}` (applies to the draft) | |
| Requests already filed | `ai_agents_change_requests_list {id, status?, conversation_id?}` (`corrections:read` since app v12.4; `corrections:write` before), `coach_feature_requests_list`, `coach_stats` | |
| Platform failures | `worker_failures_list {queue?, unreplayed?, limit≤200}` — final-failed jobs (`messageQueue` = an inbound that never got a turn) | |
| Conversations | `conversations_list {page, limit≤100, channel?, status?, search?}`, `conversations_export {id, format:"json"}`, `conversations_linked_records {id}`, `conversations_calls` | |
| Thread by ticket | `tickets_messages_thread {ticket_id, limit≤2000, before?}` | |
| Exact turn | REST `GET /api/v1/conversations/:id/agent-turn` (assembled prompt, tools, replayed history, or `human_only` + `silence_reason`), `GET /conversations/:id/agent-runs?limit≤20` (steps: `kb_lookup | tool_call | reply | handoff | …`, tokens, cost), `GET /conversations/:id/ai-status` | `conversations:read` |
| Contacts | `contacts_stats`, `contacts_duplicates`, `contacts_search {q, limit≤100}`, `contacts_get {id}`, `contact_completeness_check` | |
| Leads | `lead_conversations_list`, `leads_kanban`, `lead_interests_list` | |

Export JSON message rows: `sender_type` (`contact | ai_agent | human_user | system`), `type` (`text | tool_calls | tool | reasoning | event`), `tool_calls[].function.{name, arguments}`, `tool_call_id` pairs a result with its call, `metadata` (delivery, ad context, version).

## Symptom → cause → owner

| Symptom in the thread | Likely cause | Owner | Evidence to record |
|---|---|---|---|
| Wrong price, hours, policy, name | Fact missing or stale in the KB, or contradicted between prompt and a skill | Workspace | the reply + the `search_knowledge_base` result (or its absence) |
| Right facts, wrong order (price before qualifying, booking before identity) | Prompt flow, skill content, or a `behavior_policies` setting | Workspace | reply + the skill loaded (`load_skill` args) |
| Tool refused `skill_not_loaded` | Skill description never made the agent load it | Workspace | the tool result row |
| Agent never used a tool it should have | Tool not attached/enabled for the agent, or integration not connected | Workspace (attach) / Vitrina (connection) | `ai_agent_tools_list`, agent-turn `tools` |
| Tone, length, emojis, formality | Prompt (tone principles), channel guidance | Workspace | three example replies |
| Hours/branches/date wrong in a reply | Workspace settings (business hours, locations, timezone) or runtime context bug | Workspace first; Vitrina if settings are right | agent-turn `workspace`/`branches` block |
| Tool result `could not reach …`, HTTP 4xx/5xx, timeouts | Integration or platform defect | Vitrina | the tool result text + time |
| Silent turn after correct tool calls, "produced no reply text", reply cut mid-sentence | Step cap / synthesis bug | Vitrina | agent-runs for the turn (steps, status) |
| Two replies to one message, reply ignores the customer's last message | Coalescing / revision gate | Vitrina | message timestamps |
| Message sent but customer never received it | Delivery | Vitrina | `metadata.delivery_*` |
| Agent kept answering after a human replied, or stayed silent when the human never did | Handling rules | Vitrina (check `conversation.handler` first) | ai-status output |
| Reply took minutes | Latency / provider | Vitrina | `analytics_latency`, agent-runs latency |
| Inbound never answered at all | Job failed, AI muted by availability rules, contact set to no-bot | Vitrina (failure) / Workspace (availability, contact flag) | `worker_failures_list`, ai-status |
| Confused who it was talking to | Duplicate/merged contacts, shared phone | Workspace (data) / Vitrina (identity logic) | `contacts_duplicates`, contact record |
| Needs a tool or integration that does not exist | Capability gap | Vitrina | the customer's ask, count of occurrences |

Rule of thumb: if a prompt, skill, KB document, tool attachment or setting can change the behaviour, the workspace owns it; otherwise Vitrina does.

## Filing tools

| Purpose | Tool | Inputs |
|---|---|---|
| Request a behaviour change the business requires | `ai_agents_change_request_create` | `id` (agent), `verbatim` (≤5000 chars, the client's own words), `reporter_kind: member | client_via_member`, `conversation_refs[{conversationId, messageId?}]` ≤20 |
| Follow it | `ai_agents_change_request_get`, `_transition`, `_scenario`, `_scenario_evaluate`, `_propose` — statuses `received → grounded → reproduced → proposed → applied → verified`, or `ya_cumple` (already behaves), `harness` (platform change) |
| Missing capability | `coach_escalate_to_vitrina` | `capability_key`, `title`, `description?`, `category? integration|tool|channel|reporting|automation|other`, `reason?`, `ai_agent_id?` |
| Freeze evidence | `coach_correction_capture {conversation_id, title?}`, `coach_annotation_add` |
| Handoff verdict | `coach_handoff_feedback_submit {conversation_id, verdict: missing_knowledge|missing_capability|wrong_behavior|correct_handoff|skipped, note?}` |
| Apply a platform proposal | `coach_proposal_decide {proposal_id, decision}` (lands in the agent draft; publish afterwards) |

## Report template

```markdown
# Audit — <agent> — <window>
## Numbers
conversations · AI-resolved · handed off · unresolved · CSAT · p95 latency · cost
## Findings
| # | Conversation | Symptom | Evidence | Cause | Owner |
## Workspace fixes (ranked)
1. <fix> — <n> conversations — layer: prompt/skill/KB/tools/settings → improve-vitrina-agent
## Requests to Vitrina
- SR-n <title> — evidence C-…, C-…
- capability: <key>
## Open questions for the owner
```
