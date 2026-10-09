---
name: vitrina
description: Which Vitrina skill fits your question, and whether your connection can answer it.
disable-model-invocation: true
---

# Vitrina — which skill, and are you connected?

Four skills, one per question:

| You want to… | Run |
|---|---|
| Fix what the agent said or did in a conversation; change its prompt, a skill or a knowledge document | `improve-vitrina-agent` |
| Know how the agent is doing over many conversations, and what is yours to fix vs. Vitrina's | `analyze-business` |
| See where people come from and where they drop before booking or buying | `analyze-funnel` |
| Understand or judge the Meta ads: cost per patient/customer, return, what to pause or scale, measurement health | `vitrina-ads` |

Before any of them, check the connection once: call `ai_agents_list`. If the tool is missing or only a handful of `mcp__vitrina__*` tools exist, the session is on a read-only connector key (the one the «Conectar tu IA (MCP)» page issues); editing agents needs an API key from **Configuración → Claves de API** added with `claude mcp add --transport http vitrina https://api.vitrinadev.com/mcp --header "Authorization: Bearer sk_…"`. Reading ads needs `ads:read`, which only admin roles hold. The exact scope list is in `improve-vitrina-agent`'s connect reference.

Typical chains: `analyze-business` or `analyze-funnel` finds the leak → `improve-vitrina-agent` fixes the agent's part → `vitrina-ads` judges the ad's part.
