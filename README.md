# Vitrina skills

Agent skills for working on [Vitrina](https://vitrinadev.com) AI agents — the WhatsApp/Instagram/email/voice agents a workspace runs on the platform. They teach Claude (chat or Claude Code), Codex, Cursor and other agents how an agent is assembled, how to read the conversations where it misbehaved, and how to change its prompt, skills and knowledge base safely through Vitrina's MCP connector: every prompt change is saved to the draft and published only after you approve the diff.

Small, composable, editable. Fork them, adapt them to your workspace.

## Installation

Two steps: install the skills, then connect Vitrina (next section).

<details open>
<summary><strong>Claude chat (claude.ai, Claude Desktop)</strong></summary>

On a paid plan: **Customize → Plugins → Add marketplace** → `VitrinaDev/skills`, then install **vitrina-skills** ([how plugins work in Claude](https://support.claude.com/en/articles/13837440)). Team and Enterprise owners can publish the plugin to the whole organization.

If the marketplace is not accepted there, upload the skills one by one: download a skill folder from this repository as a `.zip` (one folder under `skills/`, e.g. `improve-vitrina-agent`), then **Customize → Skills → Upload a skill**. Skills need **Settings → Capabilities → Code execution** turned on.

</details>

<details>
<summary><strong>Claude Code</strong></summary>

```
/plugin marketplace add VitrinaDev/skills
/plugin install vitrina-skills@vitrina
```

From a shell: `claude plugin marketplace add VitrinaDev/skills` and `claude plugin install vitrina-skills@vitrina`.

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

The skills read and write through Vitrina's MCP server (`https://api.vitrinadev.com/mcp`). Nothing runs outside your workspace and no model key of your own is needed — the analysis is your agent's own reasoning. Vitrina's **Configuración → Conectar tu IA (MCP)** page walks you through it; you sign in to Vitrina, and on the consent screen you tick what the connection may change. **Tick «Agentes de IA»** to let the skills edit your agent (draft, publish, skills, knowledge links, change requests).

- **Claude chat:** claude.ai → Customize → Connectors → add custom connector → `https://api.vitrinadev.com/mcp` → sign in → tick «Agentes de IA».
- **Claude Code:** `claude mcp add --transport http vitrina https://api.vitrinadev.com/mcp`, then `/mcp` → `vitrina` → Authenticate → sign in → tick «Agentes de IA».
- **Cursor and others:** add the same URL as a remote MCP server and sign in.

Connected before «Agentes de IA» existed, or without ticking it? In Vitrina, **Configuración → Conectar tu IA → Desconectar** that app, then connect again and tick it.

What a connection cannot do: simulate the agent or run test scenarios (they spend model budget — try changes in the agent's «Probar» tab in Vitrina), or upload knowledge-base files (the skill writes the file; you upload it in Vitrina). For scripts and automation, an API key from **Configuración → Claves de API** (`--header "Authorization: Bearer sk_…"`) reaches the full catalogue within its scopes. Details: [`skills/improve-vitrina-agent/references/connect.md`](./skills/improve-vitrina-agent/references/connect.md).

## The skills

Run `/vitrina` when unsure which one fits. The others are **model-invoked**: the agent reaches for them when your request matches; you can also type the name.

- **[improve-vitrina-agent](./skills/improve-vitrina-agent/SKILL.md)** — "The agent answered wrong in C-1234", "cambia lo que dice sobre precios", "why did the AI stay silent?". Reads the live config, inspects the conversation (messages, tool calls, reasoning), finds which layer is at fault — prompt, skill, KB, tool, or the harness itself — saves the fix to the draft, shows you the diff and publishes only on your yes (skill and KB changes, live on write, are confirmed first), and verifies.
- **[write-knowledge](./skills/write-knowledge/SKILL.md)** — "Agrega a la base de conocimiento cómo llegar", "actualiza el precio de la limpieza", "que sepa que ya no hacemos blanqueamiento". Writes the document or skill in the shape retrieval needs (one question per section, the customer's words, dates on prices), shows it to you before it goes live, confirms ingestion and proves the answer with a scenario run or the test bench.
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
