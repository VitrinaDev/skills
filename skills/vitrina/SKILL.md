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

Before any of them, check the connection once: call `ai_agents_list`. If the tool is missing or only a handful of `mcp__vitrina__*` tools exist, the session is on a read-only connector key (the one the «Conectar tu IA (MCP)» page issues); editing agents needs an API key from **Configuración → Claves de API** added with `claude mcp add --transport http vitrina https://api.vitrinadev.com/mcp --header "Authorization: Bearer sk_…"`. Reading ads needs `ads:read`, which only admin roles hold. The exact scope list is in `improve-vitrina-agent`'s connect reference.

Typical chains: `weekly-review` → `analyze-business` or `analyze-funnel` finds the leak → `improve-vitrina-agent` or `write-knowledge` fixes the agent's part → `test-vitrina-agent` keeps it fixed → `vitrina-ads` judges the ad's part.
