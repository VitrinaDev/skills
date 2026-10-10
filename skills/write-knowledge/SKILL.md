---
name: write-knowledge
description: "Add or update what a Vitrina AI agent knows: write a knowledge-base document or an agent skill (playbook) in the shape retrieval and the runtime need, show the exact change and write it only after the user says yes (it goes live immediately), attach it to the agent over Vitrina's MCP connector or API, confirm ingestion and prove the agent now answers from it. Use when the user wants the agent to know something new (prices, hours, how to arrive, policies, promotions, FAQs, a procedure), says 'agrega a la base de conocimiento', 'que sepa que…', 'sube este documento', 'actualiza el precio de…', pastes a PDF/text to teach the agent, or wants a new playbook for a situation — even if they don't say 'knowledge base' or 'skill'."
---

# Teach the agent something

Two homes for knowledge, chosen by how it is used:

- **Knowledge-base document** — facts the agent looks up: prices, hours, addresses, policies, catalogue, FAQs. Retrieved by `search_knowledge_base` in ~500-token chunks, so **the chunk, not the document, is the unit**: a section must answer on its own.
- **Skill** — a procedure the agent follows at a moment: how to book, how to handle a complaint, how to quote. Loaded whole by `load_skill` when its `description` matches the situation; numbered steps, rules, verbatim templates.

A fact goes in a document; a sequence of actions goes in a skill; a fact the agent must always apply (tone, a hard limit) goes in the prompt via `improve-vitrina-agent`. Skills ≤ 20,000 chars; documents UTF-8 markdown preferred (≤ 25 MB). Calls per credential (connector with the «Agentes de IA» pack, or `sk_` key) are in `improve-vitrina-agent`'s [`references/surface.md`](../improve-vitrina-agent/references/surface.md); which credential this session has: its `connect.md`. Through MCP keep one call under ~1 MB of content; split larger documents.

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

## Step 4 — Confirm, then write

Both homes are **live the moment they are written**, on every agent attached. Show the user the exact change — the new or edited sections (before → after), or the skill text — say which agents it reaches, and write only after an explicit yes.

- Skill, connector: `call_operation skill_replace {params:{id}, body:{content, description?, expected_version}}`, or `skills_create {body:{name, description, content}}` then `ai_agent_skills_create {params:{id: <agent>}, body:{skill_id}}`. `sk_` key: `skills_update` / `skills_create` + `agent_skills_attach`.
- Document, `sk_` key: `kb_files_replace {id, filename, content, expected_version}` or `kb_files_upload {filename, content, attach_to_agent_id}`.
- Document, connector: `call_operation kb_file_content_replace {params:{id}, body:{filename, content, content_encoding:"utf8", expected_version}}` when a file already covers the topic (its id and agent links stay), else `call_operation kb_files_create {body:{filename, content, content_encoding:"utf8", content_type:"text/markdown"}}`. Once it exists, attach it with `call_operation ai_agent_knowledge_create {params:{id: <agent>}, body:{kb_file_id}}` if it is not attached yet. A website's content can be drafted with `call_operation kb_files_generate_from_url_create {body:{url}}` (returns markdown, stores nothing).
- Poll `kb_files_list` until `status: ingested` (seconds; `failed` → re-ingest: connector `call_operation kb_file_reingest_create {params:{id}}`, `sk_` `kb_files_reingest`).

Done when: the user approved the change and the file shows `ingested` with `kb_files_get_text` returning your text, or the skill is attached to the agent.

## Step 5 — Prove the agent answers from it

With an `sk_` key, build and run one scenario with the customer's question (`ai_agents_scenarios_build {id, from:"description", description:"…"}` → `ai_agents_scenario_create` → `ai_agents_scenarios_run {id, scenario_ids}` → `ai_agents_scenario_run_get`): the transcript must show the `search_knowledge_base` (or `load_skill`) call and a reply that quotes your fact. `ai_agent_simulate` alone is weaker (tools are declared, not executed). Keep the scenario; `test-vitrina-agent` turns it into a regression check.

On a connector, scenarios cannot be built or run (model spend): give the user the exact customer question to try in the agent's «Probar» tab in Vitrina (the test bench), and afterwards read the next real conversations that ask it.

Done when: one run or test-bench try shows the agent retrieving and using the new content, or you have said exactly what still prevents it.
