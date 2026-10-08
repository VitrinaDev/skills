---
name: analyze-business
description: "Audit how a Vitrina workspace's AI agent is performing by reading its conversations, contacts, tool runs and the platform's own reviews over Vitrina's MCP/REST, classify every wrong answer, silence, handoff or tool error by its cause, and decide what the workspace can fix itself (prompt, skills, knowledge base, tool wiring, policies) versus what must be reported to Vitrina as a platform defect or missing capability — then file both. Use when the user asks how their agent is doing, why it gives wrong answers, wants a review of recent conversations, mentions 'auditar', 'revisar las conversaciones', 'por qué el agente respondió mal', wants to analyze contacts or tool runs, or asks whether a problem is theirs to fix or Vitrina's — even without naming a specific conversation."
---

# Analyze a workspace's agent performance

Breadth first: this skill audits many conversations to find patterns and assigns each problem an **owner** — the workspace (fixable through the agent's configuration) or Vitrina (platform behaviour, integration error, missing capability). Fixing one configuration problem in depth is the `improve-vitrina-agent` skill; this one ends by handing it the list.

Read on demand:
- [`references/playbook.md`](references/playbook.md) — the tools to call with their inputs, the symptom → cause → owner table, and the filing tools. **Read before Step 2.**
- No MCP tools loaded? Run `improve-vitrina-agent`'s connect reference: an `sk_` API key with the scopes listed there (this skill also needs `corrections:read`, `corrections:write`, `analytics:read`, `contacts:read`, `tickets:read`, `worker_failures:read`).

## Step 1 — Frame the audit

Agree the agent (`ai_agents_list`), the window (default the last 7 days; 30 for a monthly review), the channels, and the question behind the request ("why do people ask for a human", "are prices right", "is it slow"). Pull the numbers first: `ai_agents_metrics_get {id, days}`, `insights_ai_agents_get`, `insights_csat_get`, `coach_stats`, `analytics_latency`, `analytics_cost`.

Done when: you can state the volume (conversations, AI-resolved vs. handed off, unresolved), and the two or three numbers that look wrong.

## Step 2 — Start from what the platform already found

The platform reviews conversations nightly. `coach_reviews_list {ai_agent_id, with_handoff:true}` gives outcome + summary per conversation; `coach_findings_list {ai_agent_id}` gives the aggregated findings with evidence; `coach_proposals_list` the proposed fixes; `ai_agents_change_requests_list {id}` what people already requested; `worker_failures_list {unreplayed:true}` jobs the platform itself failed on. Read these before opening a single thread — most audits are already half written.

Done when: every active finding and every unreplayed failure is in your working list with its status.

## Step 3 — Sample and read conversations

Choose the sample deliberately: every handoff and unresolved conversation in the window, every one the reviews flag, plus a random slice of resolved ones (`conversations_list {status, channel, limit, page}`; `search` for words like "humano", "no me sirve", "equivocado", "precio"). For each: `conversations_export {id, format:"json"}` (messages with `type`, `tool_calls`, tool results, reasoning rows, contact, attributes); for a turn that needs the exact prompt and tool list, REST `GET /conversations/:id/agent-turn` and `GET /conversations/:id/agent-runs`.

Read as an investigator: locate the first wrong reply, walk up to its reasoning and tool rows, and record the **evidence line** (message id, tool name, the result text).

Done when: each sampled conversation has one line — fine, or symptom + evidence.

## Step 4 — Classify by cause and owner

Use the table in `references/playbook.md`. Two buckets:

- **Workspace fixes** — wrong or missing fact (knowledge base), wrong moment or flow (prompt, skill content, skill description that never triggers), behaviour policy, tool not attached, tone, hours/branches/business data in settings.
- **Vitrina** — tool result errors from an integration, silent turns after correct tool use, duplicate or out-of-order replies, undelivered messages, the agent replying after a human took over, stale runtime context (wrong date, hours), latency spikes, worker failures, or a capability the catalogue lacks.

When unsure, check whether the configuration *could* express the fix: if no prompt, skill, KB or setting can change the behaviour, it is Vitrina's.

Done when: every symptom row has cause, owner and the evidence that proves the assignment.

## Step 5 — Contacts and data quality

`contacts_stats` (reachability, duplicate candidates), `contacts_duplicates`, and the contact behind each problematic conversation (`contacts_get`). Family members on one phone, merged or duplicated contacts, missing identity data and wrong attributes explain a class of "the agent confused who it was talking to" failures. Data problems are the workspace's; identity-resolution behaviour is Vitrina's.

Done when: contact-related causes are either in the workspace list (clean-up tasks) or in the Vitrina list.

## Step 6 — Report and file

Write `analysis/AUDIT-<agent>-<date>.md`: numbers (Step 1), findings table (conversation, symptom, evidence, cause, owner), **workspace fixes** ranked by frequency × damage, **requests to Vitrina**, and open questions for the business owner. Then file:

- Workspace fixes → run `improve-vitrina-agent` per fix (draft → publish for prompts; skills and KB are live immediately).
- Behaviour the business requires and cannot configure → `ai_agents_change_request_create {id, verbatim, conversation_refs}` in the client's own words, up to 20 conversation refs; a request Vitrina resolves as a platform change ends in status `harness`.
- Capability the catalogue lacks (tool, integration, channel, report) → `coach_escalate_to_vitrina {capability_key, title, description, category}` — emails Vitrina once per capability.
- Evidence to preserve → `coach_correction_capture {conversation_id, title}`; handoff verdicts → `coach_handoff_feedback_submit {conversation_id, verdict}`.
- Platform defects (errors, silences, delivery, duplicates) → a change request with the evidence lines plus a message to Vitrina support quoting the display ids.

Done when: every finding is either fixed, filed with its evidence, or explicitly left open with a reason, and the report says which.
