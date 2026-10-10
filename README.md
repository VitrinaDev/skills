# Vitrina skills

Agent skills for working on [Vitrina](https://vitrinadev.com) AI agents — the WhatsApp/Instagram/email/voice agents a workspace runs on the platform. They teach Claude (chat or Claude Code), Codex, Cursor and other agents how an agent is assembled, how to read the conversations where it misbehaved, and how to change its prompt, skills and knowledge base safely through Vitrina's MCP connector: every prompt change is saved to the draft and published only after you approve the diff.

Small, composable, editable. Fork them, adapt them to your workspace.

## Installation

Two steps: install the skills, then connect Vitrina (next section).

<details open>
<summary><strong>Claude chat (claude.ai, Claude Desktop)</strong></summary>

On a paid plan: **Customize → Plugins → Add marketplace** → `VitrinaDev/skills`, then install **vitrina-skills** ([how plugins work in Claude](https://support.claude.com/en/articles/13837440)). Turn on **Sync automatically** for the marketplace to get new versions. Type `/` in a chat to see the skills. On Team and Enterprise, an owner may have to allow user-added marketplaces (Organization settings → Plugins & skills).

If your organization blocks marketplaces, upload the skills one by one: download a ready zip from the [latest release](https://github.com/VitrinaDev/skills/releases/latest) (for example [`improve-vitrina-agent.zip`](https://github.com/VitrinaDev/skills/releases/latest/download/improve-vitrina-agent.zip)), then **Customize → Skills → + → Upload a skill**. Skills need **Settings → Capabilities → Code execution** turned on. Uploaded skills do not update themselves: download the zip again after a new release.

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

The skills read and write through Vitrina's MCP server (`https://api.vitrinadev.com/mcp`). Nothing runs outside your workspace and no model key of your own is needed — the analysis is your agent's own reasoning. Vitrina's **Configuración → Conectar tu IA (MCP)** page walks you through it; you sign in to Vitrina, and on the consent screen you tick what the connection may change. Every pack is off by default, and a connection only gets the permissions your own role in Vitrina already holds.

- **Claude chat:** claude.ai → Customize → Connectors → add custom connector → `https://api.vitrinadev.com/mcp` → sign in → tick the packs you need.
- **Claude Code:** `claude mcp add --transport http vitrina https://api.vitrinadev.com/mcp`, then `/mcp` → `vitrina` → Authenticate → sign in → tick the packs you need.
- **Cursor and others:** add the same URL as a remote MCP server and sign in.

Reading is included for every connection. Writing is granted per area, with the packs below; each pack gives the connection everything the Vitrina screen for that area does, except the exclusions listed after the table.

| Pack | What it unlocks | Skills that use it |
|---|---|---|
| «Contactos» | create, edit, merge, tag and import contacts; consent, legal identity, file attributes | `vitrina-contacts` |
| «Leads» | create leads, move them between stages and pipelines | `analyze-funnel` |
| «Casos» | edit, assign, move tickets; claim a ticket | |
| «Conversaciones» | assign, resolve, claim, tag conversations; AI on/off for a conversation (ai-control, bot-gate override); handoff feedback | `improve-vitrina-agent` |
| «Mensajes a clientes» | send a message, template, flow or file to a customer; apply a macro (with «Conversaciones»). Also required by every act that notifies a customer: sending a campaign, test-sends, cancelling an appointment | `vitrina-campaigns`, `clinic-agenda` |
| «Agentes de IA» | edit the agent (draft, publish, versions), its skills, knowledge base (files up to ~1 MB per call) and its change requests; resolve or dismiss Mejoras | `improve-vitrina-agent`, `write-knowledge` |
| «Agenda» | create and move appointments, appointment types, schedule configuration; for clinics also the clinic agenda (agenda appointments, professionals, services, lab orders, pack sessions) when your role holds `clinic:write`; cancelling an appointment also needs «Mensajes a clientes» | `clinic-agenda` |
| «Seguimientos» | follow-up rules, subscriptions, recontacto configuration and its approval queue | `vitrina-campaigns` |
| «Campañas y plantillas» | WhatsApp templates (incl. header media), flows, campaigns, audiences, email templates; sending, scheduling and test-sends also need «Mensajes a clientes» | `vitrina-campaigns` |
| «Centro de ayuda» | help centers, sections, articles, translations, media | |
| «Configuración del inbox» | macros, custom fields and attributes, SLAs, triggers, routing and assignment rules, pipelines and stages | `vitrina-contacts` |
| «Catálogo» | products, marketplace sync | |

Some permissions inside a pack are optional and only granted when your role holds them (for example the clinic agenda inside «Agenda»). A pack missing from your connection is never an error in the skill: it says which pack to add.

**Add a pack later, without reconnecting:** in Vitrina, **Configuración → Conectar tu IA (MCP) → Apps conectadas → «Editar permisos»**. Only the member who connected the app can add permissions. Connected before a pack existed? Open «Editar permisos» once; an older «Agenda» picks up cancelling and the clinic agenda there too.

What a connection cannot do:
- anything that spends the workspace's model budget: simulating the agent, running test scenarios or evals, the change-request analysis steps (ground, scenario, scenario refine, propose — a connection files and reads change requests only), AI-generated help-center translations, tag suggestions, the WhatsApp template category check and parameter binder, follow-up AI drafts (try changes in the agent's «Probar» tab in Vitrina);
- show or change model and provider names, or cost and token figures: Vitrina removed them from every API and MCP response;
- create or delete AI agents;
- reach sensitive clinic data (patients register, clinical record, consents, documents, payments) or list the members of an audience (health data).

For scripts and automation, an API key from **Configuración → Claves de API** (`--header "Authorization: Bearer sk_…"`) reaches the full catalogue within its scopes, including the internal-tier reads (`agent-runs`, coach runs). Details: [`skills/improve-vitrina-agent/references/connect.md`](./skills/improve-vitrina-agent/references/connect.md).

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
