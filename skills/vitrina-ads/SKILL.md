---
name: vitrina-ads
description: "Read and explain Vitrina Ads (Meta campaigns attributed to WhatsApp/Instagram conversations, bookings and payments) for a workspace over Vitrina's MCP/REST: which campaigns and ads bring conversations, bookings, new paying patients or customers and at what cost, what the return (retorno) and cohorts mean, which ads are wearing out, whether measurement (tracking, Envío a Meta, pixel) is healthy, and what to pause, scale or fix. Use when the user mentions anuncios, Meta/Facebook/Instagram ads, campañas, costo por paciente/cliente/conversación, retorno de anuncios, ROAS, Envío a Meta, pixel, GTM, cohortes, 'qué anuncio funciona', the Vitrina Ads screens (Resumen, Campañas, Atribuidos, Creativos, Salud, Informe), or asks for the Monday ads summary — even if they do not say 'Vitrina Ads'."
---

# Vitrina Ads — read, explain, recommend

Vitrina Ads attributes Meta ads to what happened afterwards in the workspace: the conversation the click opened, the booking, the visit, the quote, the payment. Spend and clicks are read live from the attribution engine; conversations, bookings and payments are the workspace's own records. Every number you quote comes from one route, and the route tells you how it was counted — read [`references/ads-surface.md`](references/ads-surface.md) before the first call. No connection yet? `improve-vitrina-agent`'s connect reference covers the key; this skill needs `ads:read` (admin-tier) plus `analytics:read`.

## Step 1 — Frame the question and the window

Turn the request into one of the five questions the product answers: *is it working* (return, outcomes vs spend), *which campaign or ad deserves budget*, *where does the funnel leak* (writing → booked → attended → paid), *are the numbers trustworthy* (tracking, Envío a Meta), *what changed* (this period vs previous, cohorts). Fix `from`/`to` (YYYY-MM-DD, inclusive; default last 30 days) and check the add-on state with `call_operation {operation_id:"ads_state_list"}` — a 402 `ENTITLEMENT_NOT_ACTIVE` means the workspace has no Ads add-on; say so and stop, unless they want the sample (`sample:1`).

Done when: question type, window and entitlement are known.

## Step 2 — Read in this order, no more than needed

1. `ads_overview_get {from,to}` — totals for current and previous period: spend, clicks, outcomes, patient return, conversational funnel (Vitrina's own counts next to Meta's), gaps. If `spend_available` is false, spend/ROAS/clicks are **unknown**, not zero.
2. `ads_performance_list {by:"campaign"}` — per campaign: spend, people, conversations, bookings, paying patients, cost per booking / per paying patient, `best_campaign` with its rule.
3. Only if the question is about ads/creatives: `ads_performance_list {by:"ad"}` (scorecard: ranks, verdicts, `evidence.thin`) and `call_operation ads_creatives_list {window:"28d"}` (fatigue, top-performer likelihood — never present it as a probability).
4. Only for leaks: `call_operation ads_stages_list` (m1 cost per conversation → m2 answered/booked/attended rates with the healthy 10–15 % writing→booking band → m3 quote/accepted/paid) or `ads_funnel_get`.
5. Only for "is it paying back": `ads_monthly_return_get` and `call_operation ads_cohorts_list` (cost per new patient by arrival month, m0…m5 return, days to first payment).
6. Only for trust: `call_operation ads_health_list`, `ads_measurement_list` (open incidents with their fix path), `ads_conversion_sync_status_list` (Envío a Meta lanes).
7. Only for a weekly brief: `call_operation ads_briefing_list {screen:"resumen", from, to}` gives the platform's own lead sentence and facts; use it as the skeleton, not the answer.

Done when: every number you will quote has a route and a window behind it.

## Step 3 — Reason with the product's rules

- **Vocabulary is strict.** «Personas» wrote; «pacientes»/«clientes» paid. «Llegaron» = first message came from an ad; «volvieron» = a later ad-opened conversation. Return counts payments by people whose ad conversation happened within the previous 12 months.
- **Thin evidence is not a verdict.** Respect `evidence.thin`, `low_volume`, `credit_known`, `measured:false`; below ~50 outcomes the ranking is noise, say "early" rather than "best".
- **Cost per lead does not exist** in Vitrina Ads; the ladder is cost per conversation → per booking → per attended → per new/paying patient. Use the one that matches the business (a clinic optimises for new patients, a dealer for attended visits).
- **Entry classification matters:** only services marked `is_entry` count as a first visit for bookings/attended. If bookings look impossibly low, check `clinic_services_entry_proposals` before blaming the ads.
- **Comparisons need equal windows**; `meta_send/comparison` and `cohorts.comparison` already do this.
- **Meta's own counts ≠ Vitrina's.** `conversational.started` is Meta's; `conversational.vitrina` is what actually arrived and was answered.

Done when: each claim is tied to a rule above or a number, and uncertainty is stated.

## Step 4 — Answer and act

Give the verdict per campaign/ad in the user's language, one line each: spend, what it produced, cost per the chosen outcome, and the action (scale, hold, pause, fix tracking). Then the measurement caveats. Actions the platform offers live in `call_operation ads_actions_list {screen}` → `ads_actions_preview` / `ads_actions_execute` (need `ads:write`, every execution has a rollback); never change budgets or pause ads by any other path. When numbers are missing because tracking, Envío a Meta or the Meta connection is broken, point at the incident's `action.path` — that is a workspace setup task, not a Vitrina bug; a route erroring or an engine outage is Vitrina's and goes through `ai_agents_change_request_create` or support with the request id.

Done when: the user can act on every line without opening the screens, and knows which numbers to distrust.
