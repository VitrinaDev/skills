---
name: improve-vitrina-agent
description: Diagnose and fix a Vitrina AI agent (tenant-facing WhatsApp/Instagram/email/voice bot) — read its live config (system prompt, skills, knowledge base, tools, behaviour policies), inspect the conversations where it misbehaved (messages, tool calls, reasoning, the exact assembled prompt), decide which layer is at fault, apply the change through the Vitrina MCP/REST surface (draft → publish; skills and KB go live immediately) and verify. Use when the user reports an agent answered wrong in a conversation ("C-1234", "el bot dijo…", "la agente cotizó mal"), asks to change what an agent says/does, asks to edit a prompt, skill or KB document of a tenant, asks why the AI stayed silent or handed off, or wants to connect Claude Code to Vitrina's MCP to do any of this.
---

# Improve a Vitrina AI agent

One agent = `ai_agent` row (prompt + model) + attached **skills** (lazy playbooks loaded by `load_skill`) + attached **KB files** (searched by `search_knowledge_base`) + wired **tools** + **behaviour policies**, all assembled per turn by one harness. Most misbehaviour is one of these layers being wrong; the rest is harness or platform behaviour that no prompt edit can change. Find the layer first, then edit.

Reference, read on demand:
- [`references/connect.md`](references/connect.md) — how to reach the tenant: MCP (`claude mcp add` with an `sk_` key), REST, or direct SQL (Vitrina staff). **Read first if no Vitrina MCP tools are loaded.**
- [`references/harness.md`](references/harness.md) — what the runtime builds around the prompt: section order, skill gate, KB retrieval, tool catalog, platform notes, revision gates. **Read before blaming the prompt.**
- [`references/surface.md`](references/surface.md) — the MCP tools / REST routes for every edit, their scopes, and the writes that bypass the draft.
- [`references/forensics.md`](references/forensics.md) — how a turn is persisted (reasoning, tool_calls, tool results, reply rows), `GET /conversations/:id/agent-turn`, SQL recipes.

Mechanics that cost fresh sessions the most time:
- A conversation thread is `conversations_export {id, format:"json"}` (accepts `C-1234`). `tickets_messages_thread` takes a **ticket** id (`T-n`), never a conversation.
- Read one agent with `ai_agents_get {id}`; the list tools answer with summaries and omit prompt and skill bodies (`skills_get` for a body). A tool result over the harness limit is saved to a file whose path is in the error: read that file instead of re-calling.
- Writing a whole prompt (60k+ chars) through a tool call is fragile: run `scripts/mcp-call.mjs <tool> "$(cat args.json)"` from this skill's folder with `VITRINA_API_KEY` set to the same key the MCP server uses (`VITRINA_MCP_URL` for a non-production host). Pass `expected_version` / `expected_config_version` from the row you read so a concurrent edit is refused instead of overwritten.
- REST routes the catalogue lacks (`/conversations/:id/agent-turn`, `/agent-runs`, `/ai-status`) take the same Bearer key with `curl`.

## Step 1 — Fix the target

Resolve tenant → agent → conversation(s). `ai_agents_list` (or `GET /ai-agents`) names the agents; the one that answers is decided per turn (stage → originating agent → channel assignee → `is_default`), so when a tenant has several, confirm from the conversation's reply rows (`sender_id` = agent id) rather than assuming the default.

Done when: you hold the agent id, the conversation ids (UUID or `C-nnnn`), and the complaint restated in one sentence ("quoted a price before qualifying").

## Step 2 — Read the live config

Pull `ai_agents_get` (prompt, model, `reasoning_effort`, `default_max_steps`, `behavior_policies`, draft columns), `agent_skills_list` + `skills_get` for each attached skill (name, description = trigger, content), `agent_knowledge_list` + `kb_files_get_text` for KB files the complaint could touch, `ai_agent_tools_list`. Save every artifact you will edit **before** editing (local folder `<tenant-slug>/agent-update-<date>/before/`): publish snapshots exist for the prompt, not for skills or KB.

Done when: you can say where in the config the behaviour was *supposed* to be governed, or that nothing governs it.

## Step 3 — Forensics on the conversation

Follow `references/forensics.md`. Minimum: the full message thread with `type`, `tool_calls` and tool results, the reasoning rows, and the assembled prompt for the failing turn (`GET /conversations/:id/agent-turn`, REST only). Classify the failure:

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

Rules that keep the tenant safe:
- **Prompt and model go through the draft:** `ai_agents_save_draft` → `ai_agents_publish` (MCP publish skips the eval gate; REST `POST /:id/publish` runs it). Edit the whole prompt text locally, keep structure and language of the existing prompt, then save the full text — never a fragment.
- **Skills and KB are live the moment you write them.** `skills_update` changes every agent sharing that skill; `kb_files_replace` re-ingests in <30 s. Prefer editing content over adding a parallel skill/doc; a skill `description` is its trigger, so sharpen it when the agent failed to load the skill.
- **Attach through the draft when you also publish:** a publish with non-null `draft_skill_ids` / `draft_kb_file_ids` *replaces* the live attachment set — include every currently attached id.
- Platform-emitted text is English; the agent's prompt, skills and KB stay in the tenant's language (Spanish here). Principles over phrase bans; never hardcode a reply language.
- **One rule, one truth, aligned everywhere.** Before editing, list every place the rule already lives (prompt sections, skill content, KB sections); change the layer that failed and align the others, or the agent will read two versions. Back every edited artifact up first.
- **Publish or hand over?** If the user asked you to fix it, publish and say so. If they asked what happened or how to fix it, leave the change in the draft (prompt) or describe it (skills/KB are live the moment you write them, so for those propose first) and tell them exactly what is pending.
- **Platform-owned causes are filed, not prompted around.** A failing integration (`could not reach …`, HTTP 5xx), a silent turn after correct tool use, undelivered or duplicated messages, a handoff nobody received: file an `ai_agents_change_request_create` with the evidence (conversation refs, the tool result text) and report the `SR-n` id; a missing tool or integration is `coach_escalate_to_vitrina`. A prompt rule for how the agent *talks* about a failure is still a fair workspace fix; the failure itself is not.

Done when: the edited artifacts are saved both in Vitrina and in `<slug>/agent-update-<date>/` (after/), with a README line per change and its evidence.

## Step 5 — Verify

Simulate with the draft (`ai_agent_simulate` / `POST /:id/simulate {use_draft:true}`) using the failing customer messages verbatim; then watch the next real conversations (`conversations_list` + thread) and confirm the new behaviour on at least one live turn. If the tenant has Agent Evals, run the suite (`ai_agents_scenario_suite_run`).

Done when: the original failing input now produces the intended behaviour in simulation and one live conversation, and no new refusal/handoff appeared in the agent-runs of the turns you checked.

## Step 6 — Record

Write the memory/README note: what was wrong, which layer, what changed (ids, version number), evidence conversations, and what is still open for the client (questions for the owner). Keep untouched the things the client must decide.
