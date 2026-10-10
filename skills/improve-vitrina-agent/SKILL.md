---
name: improve-vitrina-agent
description: Diagnose and fix a Vitrina AI agent (tenant-facing WhatsApp/Instagram/email/voice bot) — read its live config (system prompt, skills, knowledge base, tools, behaviour policies), inspect the conversations where it misbehaved, decide which layer is at fault, apply the change through Vitrina's MCP connector or API (prompt changes saved to the draft and published only after the user approves the diff; skill and KB changes confirmed before writing) and verify. Use when the user reports an agent answered wrong in a conversation ("C-1234", "el bot dijo…", "la agente cotizó mal"), asks to change what an agent says/does, asks to edit a prompt, skill or KB document, asks why the AI stayed silent or handed off, or wants to connect Claude, Claude Code or Cursor to Vitrina to do any of this.
---

# Improve a Vitrina AI agent

One agent = `ai_agent` row (prompt + settings) + attached **skills** (lazy playbooks loaded by `load_skill`) + attached **KB files** (searched by `search_knowledge_base`) + wired **tools** + **behaviour policies**, all assembled per turn by one harness. Most misbehaviour is one of these layers being wrong; the rest is harness or platform behaviour that no prompt edit can change. Find the layer first, then edit.

Reference, read on demand:
- [`references/connect.md`](references/connect.md) — the connector (OAuth, «Agentes de IA» pack) vs. an `sk_` key, how to tell which one this session has, how to connect or reconnect. **Read first if no Vitrina tools are loaded or a write is refused.**
- [`references/harness.md`](references/harness.md) — what the runtime builds around the prompt: section order, skill gate, KB retrieval, tool catalog, platform notes, revision gates. **Read before blaming the prompt.**
- [`references/surface.md`](references/surface.md) — every edit as a connector `call_operation` id and as an `sk_` tool, and the writes that bypass the draft. **Read before Step 4.**
- [`references/forensics.md`](references/forensics.md) — how a turn is persisted (reasoning, tool_calls, tool results, reply rows), the assembled prompt of a turn (`conversation_agent_turn_list`), SQL recipes.

Mechanics that cost fresh sessions the most time:
- A conversation thread: connector `call_operation conversation_messages_list {params:{id:"C-1234", order:"asc", limit:200}}`; `sk_` key `conversations_export {id, format:"json"}`. `tickets_messages_thread` takes a **ticket** id (`T-n`), never a conversation.
- Read one agent with `ai_agents_get {id}`; the list tools answer with summaries and omit prompt and skill bodies (`skills_get` for a body). A tool result over the harness limit is saved to a file whose path is in the error: read that file instead of re-calling.
- On a connector every write is `call_operation`; the exact ids are in `surface.md`. Pass `expected_version` (draft) / `expected_draft_version` (publish) from what you read so a concurrent edit is refused instead of overwritten.
- With an `sk_` key, a whole prompt (60k+ chars) is safer through `scripts/mcp-call.mjs <tool> "$(cat args.json)"` (see `connect.md`); the one REST route the catalogue lacks (`/conversations/:id/agent-runs`) takes the same Bearer key with `curl`.
- Model and reasoning effort are Vitrina's: never report, compare or propose changing the agent's model or provider to the user.

## Step 1 — Fix the target

Check the credential once (`connect.md` → «Which one is this session on?»). Resolve tenant → agent → conversation(s). `ai_agents_list` names the agents; the one that answers is decided per turn (stage → originating agent → channel assignee → `is_default`), so when a tenant has several, confirm from the conversation's reply rows (`sender_id` = agent id) rather than assuming the default.

Done when: you hold the agent id, the conversation ids (UUID or `C-nnnn`), and the complaint restated in one sentence ("quoted a price before qualifying").

## Step 2 — Read the live config

Pull `ai_agents_get` (prompt, `behavior_policies`, step limit, draft fields and `draft_version`), `agent_skills_list` + `skills_get` for each attached skill (name, description = trigger, content), `agent_knowledge_list` + `kb_files_get_text` for KB files the complaint could touch, the agent's tools (`ai_agent_tools_list`; connector `call_operation ai_agent_tools_list {params:{id}}`). Save every artifact you will edit **before** editing (local folder `<tenant-slug>/agent-update-<date>/before/`): publish snapshots exist for the prompt, not for skills or KB.

Done when: you can say where in the config the behaviour was *supposed* to be governed, or that nothing governs it.

## Step 3 — Forensics on the conversation

Follow `references/forensics.md`. Minimum: the full message thread with `type`, `tool_calls` and tool results, and the reasoning rows; also the assembled prompt for the failing turn (`call_operation conversation_agent_turn_list {params:{id}}` on a connector; no model is involved, it reproduces the *current* config). `call_operation conversation_ai_status_list {params:{id}}` explains a silent AI. If the AI is silent because the conversation is pinned to a human or gated, `conversation_ai_control_update {params:{id}, body:{keep_with_human:false}}` or `conversation_bot_gate_override_create {params:{id}, body:{enabled:true}}` switch that one conversation back (pack «Conversaciones»; it changes live behaviour for a real customer, so only with the user's yes). Classify the failure:

| Symptom | Usual layer |
|---|---|
| Wrong fact, invented price/hours | KB content missing/stale, or prompt rule contradicted by a skill (`detectPricePolicyConflicts`) |
| Right fact, wrong moment (price first, no qualifying) | prompt flow / skill content / `behavior_policies.treatment_price` |
| Tool write refused `skill_not_loaded` | skill gate: agent never called `load_skill` (see harness.md) |
| Silent turn, `[NO_REPLY]`, handoff, "produced no reply text" | harness: step cap (8), `NO_LAST_WORD_GUIDE`, pending-question gate, handler=human, AI availability — not the prompt |
| Tool error in results (`could not reach`, 400) | integration / platform bug → file an issue, do not prompt around it |
| Reply ignored customer's last message | coalescing / freshness revision; check `latency_metric` revision flags |

Done when: each complaint maps to one layer with the evidence line (message id or tool result) that proves it.

## Step 4 — Edit the right layer

Read `references/surface.md` for the exact call. Rules that keep the tenant safe:
- **Prompt, policies and wiring go through the draft, and publishing needs the user's yes.** Save the full edited prompt text (never a fragment; keep the existing structure and language) to the draft, then show the user the diff — before → after, only the changed lines, one line on why — and ask whether to publish (verify first, Step 5). Publish only after an explicit yes in this conversation; otherwise leave it in the draft and say it is pending there. The REST publish (`ai_agent_publish_create`) runs the golden-suite gate; if it answers `evals_blocked`/`evals_stale`, show the failing scenarios and use `force` only on a second, explicit yes.
- **Skills and KB are live the moment you write them, so confirm before writing.** Show the exact change (the skill text or KB section, before → after) and write only after an explicit yes. A skill update changes every agent sharing that skill; say which. Prefer editing content over adding a parallel skill or document; a skill `description` is its trigger, so sharpen it when the agent failed to load the skill. On a connector, upload and replace KB documents with a JSON body through `call_operation` (`surface.md`).
- **Someone else's unpublished draft.** If the draft already differs from live (`draft_updated_at` set; compare `draft_system_prompt` with `system_prompt`), say what it contains, add your change on top, and never publish it without the user confirming both changes.
- **Attach through the draft when you also publish:** a publish with non-null `draft_skill_ids` / `draft_kb_file_ids` *replaces* the live attachment set — include every currently attached id.
- Platform-emitted text is English; the agent's prompt, skills and KB stay in the tenant's language (Spanish here). Principles over phrase bans; never hardcode a reply language.
- **One rule, one truth, aligned everywhere.** Before editing, list every place the rule already lives (prompt sections, skill content, KB sections); change the layer that failed and align the others, or the agent will read two versions. Back every edited artifact up first.
- **Platform-owned causes are filed, not prompted around.** A failing integration (`could not reach …`, HTTP 5xx), a silent turn after correct tool use, undelivered or duplicated messages, a handoff nobody received: file a change request with the evidence (conversation refs, the tool result text; connector `call_operation ai_agent_change_requests_create`, `sk_` `ai_agents_change_request_create`) and report the `SR-n` id; a missing tool or integration is `coach_escalate_to_vitrina` (`sk_` key) or a change request. On a connector, change requests are **file and read only**: the analysis steps (ground, scenario, scenario refine, propose) spend model budget and are excluded, so file the request with the evidence and let Vitrina process it. A prompt rule for how the agent *talks* about a failure is still a fair workspace fix; the failure itself is not.

Done when: every change the user approved is written in Vitrina (prompt changes published only on their yes, otherwise left in the draft and said so) and saved in `<slug>/agent-update-<date>/` (after/), with a README line per change and its evidence.

## Step 5 — Verify

- **`sk_` key:** simulate the draft (`ai_agent_simulate {use_draft:true}` / `POST /:id/simulate`) with the failing customer messages verbatim before publishing; if the tenant has Agent Evals, run the suite (`ai_agents_scenario_suite_run`).
- **Connector:** simulation and scenario runs spend model budget and are excluded. Read `ai_agents_publish_gate_get` and the latest `ai_agents_scenario_runs_list` results, and ask the user to try the failing message on the draft in the agent's «Probar» tab in Vitrina (the test bench) before saying yes to publishing.
- **Both:** after publishing, watch the next real conversations (`conversations_list` + the thread) and confirm the new behaviour on at least one live turn.

Done when: the original failing input produces the intended behaviour (simulation, test bench or scenario run) and, once published, in one live conversation; or you have told the user what is still unverified and how they check it.

## Step 6 — Record

Write the memory/README note: what was wrong, which layer, what changed (ids, version number, published or pending in the draft), evidence conversations, and what is still open for the client (questions for the owner). Keep untouched the things the client must decide.
