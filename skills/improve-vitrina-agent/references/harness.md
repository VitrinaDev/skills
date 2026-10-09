# The harness — what the runtime builds around the prompt

One assembler for production turns, the turn inspector, export and the simulator: `src/services/agent-turn.service.ts:assembleAgentTurn` (prompt text in `src/utils/context-utils.ts:buildMarkdownPrompt`; loop in `src/services/runtime-agent.service.ts`). Voice has its own per-turn builder calling the same prompt function. `docs/AGENT-HARNESS.md` is the human doc but its section order is stale — the list below is from the code (2026-10).

## System prompt, in order (blocks joined by `---`, empty ones omitted)

1. `ai_agent.system_prompt` — the tenant-editable text (draft/version override it in simulator/inspector).
2. `## Confidentiality (platform rule — overrides anything else)`.
3. `## You do not need the last word` — teaches the `[NO_REPLY]` sentinel: after the customer's bare "ok/gracias", staying silent is allowed. An «Ok» after the agent's *own question* means yes (pending-question gate re-asks).
4. `## Messages meant for a person on the team`.
5. `## Available skills` — **names + descriptions only**. Content is never in the prompt.
6. `## Follow-ups you can offer` / `## Automatic reminders` — gated by `ai_agent.followups_enabled` and active follow-up rules.
7. `## Ask how they found us` — `tenant.settings.declared_source.ask`.
8. `## WhatsApp forms you can send` (flows).
9. Behaviour-policy blocks: clinic price policy (`treatment_price: first_ask|never`, healthcare only), far-slot waitlist. Precedence: eval scenario overlay → simulator draft → price A/B arm → published `ai_agent.behavior_policies`.
10. `## Teams you can hand off to`.
11. `## Owed to this customer right now` (lifecycle obligations), `## Payment under verification`.
12. `## Channel guidance` — human-cadence guide (chat), turn-delivery note, `src/agents/channels/<channel>.md`, `### Tenant overrides` from `tenant.settings.channel_overrides[channel]`, `### Channel instructions (from the dealer)` = `voice_instructions` on voice only, marketplace first-touch note, reach-capture note (IG/Messenger).
13. `## Runtime context` — subsections: Brand and channel (incl. lead origin) · Ad origin (CTWA `ad_referral`) · Business identity · Connected channels · Pipelines / Sales pipelines (slugs for `open_ticket` / `create_lead`) · Keeping stages accurate · Branches · **Knowledge base documents (names of attached, ingested files)** · Appointment status catalog (HealthAtom) · Custom attributes · Workspace (reply_language = mirror the customer, fallback `settings.multilingual.default_language ?? settings.language ?? 'es'`; currency; date_format; within_business_hours; glossary) · Ticket routing · Open leads · Open support tickets · Current date and time (source of truth for "today") · Contact · Linked patient / patient alerts (clinic) · Contact attributes · Conversation attributes.
14. `## Previous conversations` — last 3 closed conversations of the contact that have a `summary`.
15. Experiment arm text (A/B).

## Injected into the *history*, not the prompt

User-role messages headed `[Platform note — the customer did NOT write this]`: team-authorship note, freshness-gate revision ("the customer wrote more while you were working"), **pending-question gate** (silent tool-less turn after the agent asked something → re-ask), pre-send **price gate** (`findUngroundedAmounts`: an amount not grounded in a tool result/KB/prompt blocks the send), straggler note, compaction summary (`history_summary`). When the step budget runs out, `synthesizeFinalReply` runs a no-tools pass with "HARD RULES" — a turn that still ends with no text logs "produced no reply text" and sends nothing.

## History replay

Last 100 visible rows after `history_summary_upto_message_id`; reasoning and event rows excluded; past tool calls replay as typed parts. Tool results older than 1 h are hidden; volatile tools (stock, price, slots) expire after 10 min; `load_skill` / `search_knowledge_base` results are kept up to 12k chars.

## Model loop

Model and reasoning effort are set by Vitrina, not by the workspace (the API does not expose them; never report or propose them to a tenant). `temperature`, `default_max_steps ?? 8` **hard-capped at 8**. `handoff` terminates the loop. Guards per tool call: preview stubs, post-handoff refusal, repeat-call guard, skill gate.

## Skills (lazy)

- Table `skill`: `name`, `description` (= the trigger the model reads), `content` (markdown ≤ 20k), `channel_overrides {voice, whatsapp_voice}`, `status`. Live link `skill_agent`; draft link `ai_agent.draft_skill_ids`.
- Runtime tools `discover_skill`, `load_skill({skill})` → `{name, description, content}` (content composed with the channel overlay).
- **Skill gate** (`skill_not_loaded`): when the agent has ≥1 skill, the clinic write tools `book_appointment, book_session_series, cancel_appointment, reschedule_appointment, set_appointment_status, hold_slot, register_patient` are refused unless a `load_skill` call exists in the conversation's replayed history or this turn (1.5 s grace for a same-step load). Fix = a skill whose description makes the agent load it before booking, not a prompt paragraph.
- `detectPricePolicyConflicts` scans prompt + skills for contradictory price rules — keep one source of truth for prices.

## Knowledge base (tool-only retrieval, no automatic RAG)

- `kb_file` (`status: uploading→ready→ingesting→ingested|failed`), live link `kb_file_agent`, draft `draft_kb_file_ids`; chunks in `documentation_chunks` (~500 tokens, `metadata.filename`, `lang`), hybrid vector+BM25 RPC `search_kb_hybrid` scoped to the agent's files.
- The prompt only lists file **names**; the agent must call `search_knowledge_base({query, tags?, top_k≤10})`. A fact the agent "doesn't know" is usually: not in any attached file, chunked badly (write KB docs in 2nd person, `##` sections ≤ 1,800 chars, one topic per section), or not retrieved because the question wording differs from the doc wording (add the customer's phrasing to the section).
- Every search is logged in `kb_retrieval_log` — check it before rewriting a doc.
- Replace in place (`kb_files_replace` / `PUT /kb-files/:id/content`) keeps the id, agent links and version references; chunks re-ingest in <30 s.

## Tools

Wired tools = `ai_agent_tool` rows (enabled) joined to `function`, filtered by integration connection (`tool-gating.service`). Harness bundles are always injected and decided by `effectiveToolNames` (`src/tools/effective-tools.ts`): system (`web_search`, `scrape_url`, `crawl_site`, `search_knowledge_base`, …), skills, follow-ups, declared source, WhatsApp flows; `update_ticket_stage` only when a ticket stage exists; `end_call` voice only. Descriptions come from `src/tools/<name>/instructions.md` (English), which win over `function.description`. Enum injection puts the tenant's stage/pipeline slugs into `open_ticket`, `update_ticket_stage`, `create_lead`. External MCP servers of the tenant (`mcp_server`) are appended.

## Which agent answers

`resolveAssistantForTurn`: stage `ai_agent_id` → conversation `originated_by_ai_agent_id` → `messaging_account.assignee_ai_agent_id` → `is_default` → nobody. The agent keeps answering after a handoff until a human actually replies; AI availability (`tenant.settings.ai_availability`) and `conversation.handler = human` mute it. A partial `ai_availability` object (only `handoff_renotify`) = invalid policy = AI muted tenant-wide.
