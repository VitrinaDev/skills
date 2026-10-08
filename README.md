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

The skills work over Vitrina's MCP server with an API key from **Settings → API keys** (scopes `ai_agents:read, ai_agents:write, ai_agents:simulate, kb:read, kb:write, conversations:read, messages:read, tenant:read`):

```bash
claude mcp add --transport http vitrina https://api.vitrinadev.com/mcp \
  --header "Authorization: Bearer sk_…"
```

An OAuth connection (the one `/mcp` offers in the browser) is read-only and does not expose the agent, skill or knowledge-base tools — use an API key. Details and the REST fallbacks: [`skills/improve-vitrina-agent/references/connect.md`](./skills/improve-vitrina-agent/references/connect.md).

## The skills

All are **model-invoked**: the agent reaches for them when your request matches the description; you can also type the name.

- **[improve-vitrina-agent](./skills/improve-vitrina-agent/SKILL.md)** — "The agent answered wrong in C-1234", "cambia lo que dice sobre precios", "why did the AI stay silent?". Reads the live config, inspects the conversation (messages, tool calls, reasoning, the exact assembled prompt), finds which layer is at fault — prompt, skill, KB, tool, or the harness itself — edits it through MCP/REST (draft → publish; skills and KB go live immediately) and verifies.
- **[analyze-business](./skills/analyze-business/SKILL.md)** — "Build the agent for X", "haz el análisis de la clínica X". Researches a business from its imported conversation corpus (or, for a new number, from interviews) and drafts the agent package: instructions, skills, knowledge documents, setup checklist, billing estimate. The corpus export needs direct database access, so that phase is for Vitrina staff.

## Contributing

See [`AGENTS.md`](./AGENTS.md) for the layout, validation and writing rules. Every skill ships with `references/` the agent loads on demand and, where it saves re-deriving, a script.

MIT — see [`LICENSE`](./LICENSE).
