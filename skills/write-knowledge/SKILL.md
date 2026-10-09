---
name: write-knowledge
description: "Add or update what a Vitrina AI agent knows: write a knowledge-base document or an agent skill (playbook) in the shape retrieval and the runtime need, upload or replace it in place over Vitrina's MCP, attach it to the agent, confirm ingestion and prove the agent now answers from it. Use when the user wants the agent to know something new (prices, hours, how to arrive, policies, promotions, FAQs, a procedure), says 'agrega a la base de conocimiento', 'que sepa que…', 'sube este documento', 'actualiza el precio de…', pastes a PDF/text to teach the agent, or wants a new playbook for a situation — even if they don't say 'knowledge base' or 'skill'."
---

# Teach the agent something

Two homes for knowledge, chosen by how it is used:

- **Knowledge-base document** — facts the agent looks up: prices, hours, addresses, policies, catalogue, FAQs. Retrieved by `search_knowledge_base` in ~500-token chunks, so **the chunk, not the document, is the unit**: a section must answer on its own.
- **Skill** — a procedure the agent follows at a moment: how to book, how to handle a complaint, how to quote. Loaded whole by `load_skill` when its `description` matches the situation; numbered steps, rules, verbatim templates.

A fact goes in a document; a sequence of actions goes in a skill; a fact the agent must always apply (tone, a hard limit) goes in the prompt via `improve-vitrina-agent`. Tools and sizes: documents via `kb_files_upload` / `kb_files_replace` (≤ 34 MB, UTF-8 markdown preferred), skills via `skills_create` / `skills_update` (≤ 20,000 chars); scopes `kb:write` and `ai_agents:write`.

## Step 1 — Capture the fact, in the business's words

Read everything the user gave (text, PDF, screenshot, a previous conversation). Resolve every ambiguity the retrieval will not forgive: units and currency, validity dates («vigente hasta»), exceptions, who it applies to, the exact names the customers use. Ask only what blocks writing; assume nothing about prices or hours. A new fact that **contradicts** what the agent already says (another address, another price) is a blocking question, not an edit: changes go live the moment they are saved.

Done when: you can list the facts as short declarative sentences with their source.

## Step 2 — Find the home

`agent_knowledge_list {agent_id}` and `kb_files_get_text {id}` for the files that could already cover the topic; `agent_skills_list` + `skills_get` for a procedure. **Update in place over creating a sibling**: a second document on the same topic produces two competing chunks and the agent will quote the stale one. If the fact also lives in the prompt or a skill, align those (one rule, one truth).

Done when: you know which file or skill changes, or that a new one is justified because no existing one covers the topic.

## Step 3 — Write for the retriever (documents)

- Title the file by topic (`horarios-y-como-llegar.md`), one `#` title, then `##` sections of **≤ 1,800 characters, each about one question**, each answering on its own (repeat the subject in the section; a chunk does not see its heading's parent).
- Second person, the customer's phrasing in the section text ("¿Tienen estacionamiento?" → a section that contains those words), numbers with units and dates (`$34.990 (vigente hasta 31-12-2026)`), no tables wider than three columns, no procedures ("to book, first…" belongs in a skill).
- Facts the agent must never say (internal notes) do not go in the KB at all.

Write for the runtime (skills): frontmatter `name` + `description` = *when to use it*, phrased as the situations a customer creates ("Usar cuando pregunta cuánto cuesta…"); body = Cuándo / Cómo (numbered steps naming the tools) / Reglas / Plantillas verbatim. The description is the trigger: if the agent fails to load the skill, sharpen the description before touching the body.

Done when: every section passes "would this chunk alone answer the customer?", and nothing in it contradicts prompt or skills.

## Step 4 — Publish

Document: `kb_files_replace {id, filename, content, expected_version}` or `kb_files_upload {filename, content, attach_to_agent_id}`; poll `kb_files_list` until `status: ingested` (seconds; `failed` → `kb_files_reingest`). Skill: `skills_update {id, content, description?, expected_version}` or `skills_create` + `agent_skills_attach`. Both are **live immediately** on every agent attached — say so.

Done when: the file shows `ingested` and `kb_files_get_text` returns your text; or the skill is attached to the agent.

## Step 5 — Prove the agent answers from it

Build and run one scenario with the customer's question (`ai_agents_scenarios_build {id, from:"description", description:"…"}` → `ai_agents_scenario_create` → `ai_agents_scenarios_run {id, scenario_ids}` → `ai_agents_scenario_run_get`): the transcript must show the `search_knowledge_base` (or `load_skill`) call and a reply that quotes your fact. `ai_agent_simulate` alone is weaker (tools are declared, not executed). Keep the scenario; `test-vitrina-agent` turns it into a regression check.

Done when: one run shows the agent retrieving and using the new content, or you have said exactly what still prevents it.
