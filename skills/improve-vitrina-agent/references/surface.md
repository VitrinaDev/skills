# Edit surface — connector operations, `sk_` tools, REST routes, and the writes that bypass the draft

Two columns per action. **Connector**: a named read tool, or `call_operation {operation_id, params, body}` (`params` = path and query parameters, flat; `body` = the JSON body). Connector writes need the «Agentes de IA» pack (see `connect.md`); run `describe_operation {operation_id}` once before the first call of an operation to read its exact body schema. **`sk_` key**: the hand-written MCP tool. REST paths are under `/api/v1`.

Model and reasoning effort are managed by Vitrina: the API neither returns nor accepts them. Never tell a tenant which model or provider their agent runs on, and never offer to change it.

## Agent

| Action | Connector | `sk_` MCP tool | Notes |
|---|---|---|---|
| List / read | `ai_agents_list`, `ai_agents_get {id}` | same | Live + `draft_*` fields, `draft_version`, `config_version`, `behavior_policies`. `GET /ai-agents/{id}/draft` = `call_operation ai_agent_draft_list {id}`. |
| Save draft | `call_operation ai_agent_draft_replace {params:{id}, body:{system_prompt?, voice_instructions?, comment_dm_criteria?, temperature?, max_steps 1–20?, tool_wiring?, skill_ids?, kb_file_ids?, knowledge_tags?, behavior_policies?, expected_version}}` | `ai_agents_save_draft {id, system_prompt?, voice_instructions?, comment_dm_criteria?, skill_ids?, kb_file_ids?, expected_version?}` | Never live. Fields merge over the previous draft; an empty string stages a clear. `expected_version` = the `draft_version` you read; stale → 409 `VERSION_CONFLICT`. `behavior_policies` is a partial patch (`treatment_price: unset|first_ask|never`, `far_slot_waitlist`). |
| Discard draft | `call_operation ai_agent_draft_delete {params:{id}}` | — | Only with the user's yes. |
| Publish | `call_operation ai_agent_publish_create {params:{id}, body:{expected_draft_version, force?, skip_eval?}}` | `ai_agents_publish {id}` (skips the eval gate) | REST publish runs the golden-suite gate: `blocked`/`stale` → 409 `evals_blocked`/`evals_stale` unless `force:true` (audited; ask first). `draft_base_stale` 409 = the live agent changed after the draft began: re-read and re-show the diff. A publish with non-null `draft_skill_ids`/`draft_kb_file_ids` **replaces** the live attachment set. |
| Publish gate | `ai_agents_publish_gate_get {id}` | same | `none|ready|pending|stale|blocked`, failing scenarios with `run_id`s. |
| Versions | `versions_list {ai_agent_id}`; `call_operation ai_agent_version_get {params:{id, version}}` | `versions_list`, `versions_restore {ai_agent_id, version_number}` | Restore: `call_operation ai_agent_version_restore_create {params:{id, version}}` loads the version **into the draft** (then the publish rule applies). Rollback `ai_agent_version_rollback_create {params:{id, version}}` restores **and publishes** with no gate: same yes as a publish. |
| Name, description | `call_operation ai_agent_replace {params:{id}, body:{name?, description?, followups_enabled?, allowed_url_prefixes?}}` | REST `PUT /ai-agents/{id}` | **Live immediately**, no draft: show and confirm first. |
| Tools | `call_operation ai_agent_tools_list {params:{id}}`, `ai_agents_tools_catalog_list` | `ai_agent_tools_list {ai_agent_id}`, `tools_list` | Wiring changes go in the draft (`tool_wiring`). `ai_agent_tools_replace` (`PUT /ai-agents/{id}/tools`) is live, no draft — avoid. |
| Live prompt write | — | — | `ai_agent_system_prompt_replace` (`PUT /ai-agents/{id}/system-prompt`) writes the **live** prompt with no draft. Never use it; it also makes a staged draft stale. |

Which agent a tenant actually uses: check `is_default`, `status`, and the `sender_id` on recent `ai_agent` reply rows.

## Skills — live immediately

| Action | Connector | `sk_` MCP tool |
|---|---|---|
| List / read | `skills_list`, `skills_get {id}`, `agent_skills_list {agent_id}` | same |
| Create | `call_operation skills_create {body:{name ≤120, description? ≤2000, content? ≤20000, channel_overrides? {voice?, whatsapp_voice?}, status? active|inactive}}` | `skills_create` |
| Update | `call_operation skill_replace {params:{id}, body:{…same fields, expected_version}}` | `skills_update {id, …}` |
| Attach | `call_operation ai_agent_skills_create {params:{id: <agent>}, body:{skill_id}}` | `agent_skills_attach {agent_id, skill_id}` |
| Detach | `call_operation ai_agent_skill_delete {params:{id: <agent>, skillId}}` | `agent_skills_detach` |

An update changes **every agent attached to the skill**; `channel_overrides`, when sent, replaces the whole map. History: `call_operation skill_versions_list {params:{id}}`.

## Knowledge base — live immediately

| Action | Connector | `sk_` MCP tool |
|---|---|---|
| List / text | `kb_files_list`, `kb_files_get_text {id}`, `agent_knowledge_list {agent_id}` | same |
| Upload / replace a document | **Not over a connector** (`POST /kb-files` and `PUT /kb-files/{id}/content` are multipart). Hand the user the finished `.md` file to upload in Vitrina's «Base de conocimiento», or use an `sk_` key. | `kb_files_upload {filename, content, attach_to_agent_id?}`, `kb_files_replace {id, filename, content, expected_version?}` |
| Draft a document from a website | `call_operation kb_files_generate_from_url_create {body:{url, crawl?, max_pages ≤25?}}` → `{title, markdown}`; **returns, does not store** | same op via `call_operation` |
| Attach an existing file | `call_operation ai_agent_knowledge_create {params:{id: <agent>}, body:{kb_file_id}}` | `agent_knowledge_attach {agent_id, kb_file_id}` |
| Detach | `call_operation ai_agent_knowledge_delete {params:{id: <agent>, fileId}}` | `agent_knowledge_detach` |
| Re-ingest | `call_operation kb_file_reingest_create {params:{id}}` | `kb_files_reingest {id}` |
| Delete | `call_operation kb_file_delete {params:{id}}` (destructive) | `kb_files_delete {id}` |

Wait for `status = ingested` (`kb_files_list`) before testing retrieval.

## Testing and improvement loops

- **Connector (reads only):** `ai_agents_publish_gate_get`, `ai_agents_scenarios_list`, `ai_agents_scenario_runs_list`, `ai_agents_scenario_run_get`, `ai_agents_scenario_suites_list`, `coach_reviews_list`, `coach_findings_list`, `coach_finding_get`, `coach_proposals_list`, `ai_agents_change_requests_list`, `ai_agents_change_request_get`. Simulating, building or running scenarios is not available; the person tries the draft in the agent's «Probar» tab in Vitrina (the test bench).
- **Change request** (ADR 0103, `SR-n`): connector `call_operation ai_agent_change_requests_create {params:{id}, body:{verbatim ≤5000, reporter_kind: member|client_via_member, conversation_refs?:[{conversationId, messageId?}]}}`; `sk_` `ai_agents_change_request_create`.
- **`sk_` key only** (`ai_agents:simulate`): `ai_agent_simulate {ai_agent_id, user_message, use_draft?, channel?}`; REST `POST /ai-agents/:id/simulate {messages[], use_draft, channel?, max_steps≤8}`; scenario build/create/run and suite runs (`test-vitrina-agent`); Agent Coach `POST /ai-agents/:id/coach/run`; `coach_finding_investigate`.
- Test bench sessions (ADR 0090): `POST /ai-agents/:id/test-sessions`; MCP read-only `ai_agents_test_sessions_list/_get` (`sk_`).

## Not reachable from MCP (REST only; tier `interna`)

`GET /conversations/:id/agent-turn`, `GET /conversations/:id/agent-runs`, `POST /ai-agents/:id/coach/run`, `POST /copilot/explain`.
