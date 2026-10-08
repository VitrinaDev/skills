# Edit surface — MCP tools, REST routes, scopes, and the writes that bypass the draft

Scopes: `ai_agents:read|write|simulate`, `kb:read|write`, `conversations:read`, `messages:read`, `corrections:read|write`. MCP tool names below are the hand-written catalogue (needs an `sk_` key; connector/OAuth keys never see them).

## Agent

| Action | MCP | REST | Notes |
|---|---|---|---|
| List / read | `ai_agents_list`, `ai_agents_get {id}` | `GET /ai-agents`, `GET /ai-agents/:id`, `GET /:id/export` | `ai_agents_get` returns live + `draft_*` columns and `behavior_policies`. |
| Save draft | `ai_agents_save_draft {id, system_prompt?, voice_instructions?, comment_dm_criteria?, model?, skill_ids?, kb_file_ids?}` | `PUT /ai-agents/:id/draft` body also takes `temperature, reasoning_effort, max_steps (1–20), tool_wiring[], knowledge_tags, behavior_policies {treatment_price: unset|first_ask|never, far_slot_waitlist}` | Draft is never live. `GET/DELETE /:id/draft` to read/discard. |
| Publish | `ai_agents_publish {id}` — **skips the eval publish gate, does not queue evals**; publishes the whole draft | `POST /:id/publish {skip_eval?, force?}` — editable window → golden-suite gate (`blocked`/`stale` → 409 unless `force`) → atomic publish → version snapshot → evals + webhook | A publish with non-null `draft_skill_ids`/`draft_kb_file_ids` **replaces** the live attachment set. |
| Versions | `versions_list {ai_agent_id}`, `versions_restore {ai_agent_id, version_number}` (**into the draft only**; publish afterwards) | `GET /:id/versions`, `GET /:id/versions/:v`, `POST /:id/versions/:v/restore`, `POST /:id/versions/:v/rollback` (restore + publish, no gate) | Snapshot has prompt, voice, policies, model, temperature, max_steps, tool/skill/kb snapshots — not `reasoning_effort`. |
| Tools | `tools_list`, `ai_agent_tools_list {ai_agent_id}` (read only) | `PUT /ai-agents/:id/tools {tool_names[]}` (live, immediate), `GET /ai-agents/tools-catalog` | No MCP write for tools. |
| Policies | via save_draft on REST | `GET /:id/behavior-policies`; price A/B `GET/POST /:id/price-policy-test[/start|/end]` | |

Which agent a tenant actually uses: check `is_default`, `status`, and the `sender_id` on recent `ai_agent` reply rows.

## Skills — live immediately

| Action | MCP | REST |
|---|---|---|
| List/read | `skills_list`, `skills_get {id}` | `GET /skills`, `GET /skills/:id` |
| Create | `skills_create {name ≤120, description? ≤2000, content? ≤20000, channel_overrides? {voice?, whatsapp_voice?}, status? active|inactive}` | `POST /skills` |
| Update | `skills_update {id, …same fields}` — `channel_overrides` replaces the whole map; **affects every agent attached to the skill** | `PUT /skills/:id` |
| Attach / detach | `agent_skills_list {agent_id}`, `agent_skills_attach {agent_id, skill_id}`, `agent_skills_detach` — live link `skill_agent`, no draft | `POST /ai-agents/:id/skills {skill_id}`, `DELETE /ai-agents/:id/skills/:skillId` |

## Knowledge base — live immediately

| Action | MCP | REST |
|---|---|---|
| List / text | `kb_files_list`, `kb_files_get_text {id}` | `GET /kb-files`, `GET /kb-files/:id/text`, `GET /kb-files/:id/content` |
| Upload | `kb_files_upload {filename, content, content_encoding? utf8|base64, content_type?, attach_to_agent_id?}` | `POST /kb-files` multipart `file` (25 MB) |
| Replace in place | `kb_files_replace {id, filename, content, content_encoding?, content_type?}` | `PUT /kb-files/:id/content` multipart |
| Re-ingest / delete | `kb_files_reingest {id}`, `kb_files_delete {id}` | `POST /kb-files/:id/reingest`, `DELETE /kb-files/:id` |
| Attach | `agent_knowledge_list {agent_id}`, `agent_knowledge_attach {agent_id, kb_file_id}`, `agent_knowledge_detach` | `GET|POST /ai-agents/:id/knowledge`, `DELETE /ai-agents/:id/knowledge/:fileId` |

Wait for `status = ingested` (`kb_files_list`) before testing retrieval.

## Testing and improvement loops

- Simulate (draft-aware): MCP `ai_agent_simulate {ai_agent_id, user_message, use_draft?, channel?}`; REST `POST /ai-agents/:id/simulate {messages[], use_draft, channel?, max_steps≤8}` (+ `/simulate/stream`). Scope `ai_agents:simulate`.
- Test bench sessions (ADR 0090): `POST /ai-agents/:id/test-sessions`, `/:sid/messages`, comments → coach. MCP read-only `ai_agents_test_sessions_list/_get`.
- Agent Coach (REST only, `ai_agents:simulate`): `POST /ai-agents/:id/coach/run {feedback, transcript[], target_message?, use_draft=true}` — edits the draft (prompt append/rewrite, create/update/attach skill, attach knowledge/tools). `docs/AGENT-COACH.md`.
- Agent Evals (ADR 0098): `/ai-agents/:id/scenarios[…]`, suites, runs; MCP `ai_agents_scenario*`, `ai_agents_scenario_suite*`, `ai_agents_publish_gate_get`. Runs need the `evals` worker pool.
- Change requests (ADR 0103, display id `SR-n`): `/ai-agents/:id/change-requests[…]`; MCP `ai_agents_change_request_*` (create → ground → scenario → evaluate → propose).
- Mejoras (ADR 0095): `conversation_review` + `agent_finding`; MCP `coach_reviews_list {ai_agent_id, with_handoff?}`, `coach_findings_list`.

## Not reachable from MCP (REST only; tier `interna`)

`GET /conversations/:id/agent-turn`, `GET /conversations/:id/agent-runs`, `POST /ai-agents/:id/coach/run`, `PUT /ai-agents/:id/tools`, `POST /copilot/explain`.
