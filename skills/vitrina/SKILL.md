---
name: vitrina
description: Which Vitrina skill fits your question, and whether your connection can answer it.
disable-model-invocation: true
---

# Vitrina — which skill, and are you connected?

Eleven skills, one per question:

| You want to… | Run |
|---|---|
| Fix what the agent said or did in a conversation; change its prompt, a skill or a knowledge document | `improve-vitrina-agent` |
| Teach the agent a fact, a price, a procedure (a KB document or a skill) | `write-knowledge` |
| Make sure a fixed bug stays fixed; run the suite before publishing | `test-vitrina-agent` |
| Know how the agent is doing over many conversations, and what is yours to fix vs. Vitrina's | `analyze-business` |
| See where people come from and where they drop before booking or buying | `analyze-funnel` |
| Understand or judge the Meta ads: cost per patient/customer, return, what to pause or scale, measurement health | `vitrina-ads` |
| The Monday summary: numbers vs last week, ads brief, flags, three actions | `weekly-review` |
| Clean the contact directory: duplicates, import, consent, RUT, tags, who is marketable | `vitrina-contacts` |
| Send something to many people: templates, audiences, campaigns, follow-ups, recontacto | `vitrina-campaigns` |
| The clinic's agenda: free slots, occupancy, bookings, waitlist, no-shows, sync | `clinic-agenda` |
| Connect your own system: operations, keys, webhooks, SDK | `vitrina-api-integrator` |

Before any of them, check the connection once:
- **No Vitrina tools at all** → not connected. Connect Vitrina as a connector: in Claude chat, Customize → Connectors → add custom connector `https://api.vitrinadev.com/mcp`; in Claude Code, `claude mcp add --transport http vitrina https://api.vitrinadev.com/mcp` then `/mcp` → vitrina → Authenticate. Sign in and tick the packs the work needs (**«Agentes de IA»** to edit the agent).
- **`ai_agents_get` and `call_operation` present** → a connector. Reading works. To edit the agent, `describe_operation {operation_id:"ai_agent_draft_replace"}` must answer with the operation; if it answers `Unknown operation`, the «Agentes de IA» pack is missing: the user disconnects the app in Vitrina (Configuración → Conectar tu IA → Desconectar) and connects again from Claude ticking «Agentes de IA».
- **`ai_agents_save_draft` present** → an `sk_` API key (scripts, automation): full catalogue within its scopes.
- **No `ai_agents_get`** → an old connection or a role without agent access; reconnect, or ask an owner or admin.

Reading ads needs `ads:read`, which only admin roles hold. Details, the write packs and the `sk_` scopes: `improve-vitrina-agent`'s connect reference.

Typical chains: `weekly-review` → `analyze-business` or `analyze-funnel` finds the leak → `improve-vitrina-agent` or `write-knowledge` fixes the agent's part → `test-vitrina-agent` keeps it fixed → `vitrina-ads` judges the ad's part.
