# Vitrina skills

Agent skills for working on [Vitrina](https://vitrinadev.com) AI agents — the WhatsApp/Instagram/email/voice agents a workspace runs on the platform. They teach a coding agent (Claude Code, Codex, Cursor, …) how an agent is assembled, how to read the conversations where it misbehaved, and how to change its prompt, skills and knowledge base safely through Vitrina's MCP server and REST API.

Small, composable, editable. Fork them, adapt them to your workspace.

## Installation

Two routes. The **Claude Code plugin** is a managed bundle that updates when we ship. **skills.sh** copies editable files into your project. Pick one.

<details>
<summary><strong>Claude Code</strong></summary>

```
/plugin marketplace add VitrinaDev/skills
/plugin install vitrina-skills@vitrina
```

Then turn on updates for this marketplace: `/plugin` → Marketplaces → `vitrina` → **Enable auto-update** (off by default for marketplaces outside Anthropic's official one). New versions then install within minutes of a session starting; without it, `/plugin` → Installed → Update now.

</details>

<details>
<summary><strong>Codex, Cursor and other agents</strong></summary>

```bash
npx skills@latest add VitrinaDev/skills
```

Pick the skills you want and the agents to install them on. Update later with `npx skills update`.

</details>

<details>
<summary><strong>For tinkerers</strong></summary>

Clone the repo and symlink every skill into your harness directories (`~/.claude/skills`, `~/.agents/skills`, plus any project `.claude/skills` you pass):

```bash
git clone git@github.com:VitrinaDev/skills.git && cd skills
scripts/link-skills.sh ~/my-project/.claude/skills
```

</details>

## Connect your agent to Vitrina

Both skills read and write through Vitrina's MCP server; nothing runs outside your workspace and no model key of your own is needed — the analysis is the coding agent's own reasoning. Vitrina's **Configuración → Conectar tu IA (MCP)** page connects Claude, Claude Code or Cursor in three steps, but that connection is read-only and does not include the agent, skill or knowledge-base tools. For these skills use an API key from **Configuración → Claves de API** (scopes `ai_agents:read, ai_agents:write, ai_agents:simulate, kb:read, kb:write, conversations:read, messages:read, tenant:read, contacts:read, tickets:read, analytics:read, corrections:read, corrections:write, worker_failures:read, appointment_types:read, clinic:read, pipelines:read, teams:read, routing:read, leads:read, appointments:read, ads:read, healthatom:read, campaigns:read, followups:read, webhooks:read`):

```bash
claude mcp add --transport http vitrina https://api.vitrinadev.com/mcp \
  --header "Authorization: Bearer sk_…"
```

Details, the difference between the two kinds of key, and the REST fallbacks: [`skills/improve-vitrina-agent/references/connect.md`](./skills/improve-vitrina-agent/references/connect.md).

## The skills

Run `/vitrina` when unsure which one fits. The other four are **model-invoked**: the agent reaches for them when your request matches; you can also type the name.

- **[improve-vitrina-agent](./skills/improve-vitrina-agent/SKILL.md)** — "The agent answered wrong in C-1234", "cambia lo que dice sobre precios", "why did the AI stay silent?". Reads the live config, inspects the conversation (messages, tool calls, reasoning, the exact assembled prompt), finds which layer is at fault — prompt, skill, KB, tool, or the harness itself — edits it through MCP/REST (draft → publish; skills and KB go live immediately) and verifies.
- **[write-knowledge](./skills/write-knowledge/SKILL.md)** — "Agrega a la base de conocimiento cómo llegar", "actualiza el precio de la limpieza", "que sepa que ya no hacemos blanqueamiento". Writes the document or skill in the shape retrieval needs (one question per section, the customer's words, dates on prices), replaces in place, confirms ingestion and proves the answer with a scenario run.
- **[test-vitrina-agent](./skills/test-vitrina-agent/SKILL.md)** — "Que no vuelva a pasar lo de C-1234", "corre las pruebas antes de publicar". Builds a scenario from the conversation, runs it against the draft or the live agent, reads the transcript, and keeps it in the golden suite that gates publishing.
- **[analyze-business](./skills/analyze-business/SKILL.md)** — "How is my agent doing?", "por qué respondió mal", "revisa las conversaciones de la semana". Audits the workspace's conversations, contacts, tool runs and the platform's own nightly reviews over MCP, classifies every wrong answer, silence, handoff or tool error by cause, and splits the result into fixes the workspace applies itself (via `improve-vitrina-agent`) and requests it files to Vitrina.
- **[analyze-funnel](./skills/analyze-funnel/SKILL.md)** — "¿De dónde vienen mis pacientes?", "where do leads drop?", "cuántas conversaciones terminan en cita". Sources, channels and ads → conversations → leads and stages → bookings → won, with conversions per step, the weakest step with example conversations, and who owns each fix.
- **[vitrina-ads](./skills/vitrina-ads/SKILL.md)** — "¿Qué anuncio me trae pacientes?", "cuánto me cuesta cada paciente nuevo", "prepárame el resumen del lunes". Reads Vitrina Ads (overview, campaigns, scorecard, stages, cohorts, return, measurement health, Envío a Meta) with the product's own vocabulary and evidence rules, and recommends what to scale, pause or fix.
- **[weekly-review](./skills/weekly-review/SKILL.md)** — "¿Cómo nos fue la semana?", "resumen del lunes". Numbers vs last week, the ads brief, what the platform flagged, three actions — summaries only, under a minute.
- **[vitrina-contacts](./skills/vitrina-contacts/SKILL.md)** — "¿Tengo contactos duplicados?", "importa esta planilla", "que el bot no le responda a Juan". Directory hygiene: dedupe and merge (with confirmation), CSV import with a dry-run plan, RUT, consent and opt-outs, tags and attributes, who is marketable.
- **[vitrina-campaigns](./skills/vitrina-campaigns/SKILL.md)** — "Mándale una promo a todos los pacientes", "por qué está pendiente la plantilla", "qué pasó con el recontacto". Templates and Meta approval, audiences and consent, test-send → schedule → send, follow-ups, recontacto, the approval queue; every send needs your explicit go.
- **[clinic-agenda](./skills/clinic-agenda/SKILL.md)** — "¿Hay horas de TTM la próxima semana?", "ocupación por profesional", "lista de espera". The agenda from the vendor's side: hours, free slots, occupancy, bookings through the engine, waitlist, no-shows, sync health. Clinics only; counts and initials, not names.
- **[vitrina-api-integrator](./skills/vitrina-api-integrator/SKILL.md)** — "Quiero crear contactos desde mi CRM y recibir un webhook cuando se agende". Discover and call any published operation, mint the narrowest key, verify webhook signatures, idempotency, rate limits, pagination, the SDK.

## Contributing

See [`AGENTS.md`](./AGENTS.md) for the layout, validation and writing rules. Every skill ships with `references/` the agent loads on demand and, where it saves re-deriving, a script.

MIT — see [`LICENSE`](./LICENSE).
