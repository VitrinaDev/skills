# Vitrina Ads surface — routes, fields, meanings

All under `/api/v1`, tag Ads, tier beta, scope `ads:read` (writes `ads:write`). Four hand-written MCP tools; everything else via `call_operation {operation_id, params}`. Period reads take `from`/`to` (YYYY-MM-DD inclusive), `model` (default `last_touch`), `sample` (1 = deterministic sample, no add-on needed). The add-on gate answers 402 `ENTITLEMENT_NOT_ACTIVE` or 409 `ADS_KEY_NEEDS_REMINT`; `GET /ads/state` (`ads_state_list`) is never gated.

## MCP tools (defaults: last 30 days, Santiago)

| Tool | Route | Input |
|---|---|---|
| `ads_overview_get` | `/ads/overview` | `from?, to?` |
| `ads_performance_list` | `/ads/campaigns` or `/ads/scorecard` | `by: campaign|ad, from?, to?` |
| `ads_funnel_get` | `/ads/funnel` | `from?, to?` |
| `ads_monthly_return_get` | `/ads/monthly-return` | `from?, to?` (default 6 months) |

`call_operation` example: `{"operation_id":"ads_stages_list","params":{"from":"2026-09-01","to":"2026-09-30"}}`. `describe_operation {operation_id}` prints the exact params.

## Reads and what they mean

| Operation id | Returns |
|---|---|
| `ads_overview_list` (+`grain=day`) | `current`/`previous`: `spend`, `spend_available` (false ⇒ spend/roas/clicks are null = unknown), `clicks`, `revenue`, `roas`, `outcomes`, `patient_return{patient_first_value, patient_later_value, patients}`, `conversational.started` (Meta: conversations, cost_per_conversation) vs `conversational.vitrina` (conversations, replied, appointments, closed, cost_per_conversation), `meta_send`, `gaps` |
| `ads_campaigns_list` (`limit≤500`, `series=1`) | per campaign: `campaign_external_id`, `spend`, `outcome_count/value`, `roas`, `people`, `appointments_booked`, `cost_per_appointment`, `paying_patients`, `cost_per_paying_patient`, `patient_return`, `top_ad`, `website.booking_drafts`; `totals`, `best_campaign{rule, reason}` |
| `ads_scorecard_list` | every ad: spend, cash, people, bookings, attended, accepted, `cost_per_person`, rank, verdict, `best_ad_external_id`, `basis` (accepted|cash), `evidence.thin` |
| `ads_creatives_list` (`window` 7d|14d|28d|lifetime, `limit≤100`) | `composite_score`, `top_performer_likelihood`, `fatigue_state`, `attributed_revenue`, `roas` |
| `ads_booking_rate_list` | AI booking rate on ad conversations the AI handled alone: overall, per campaign, per ad, per hour; `low_volume` |
| `ads_funnel_list` | people cohort by first contact in window: `steps[]` contacted→booked→attended→quote_presented→accepted→paid, each `ads`, `ads_returned`, `other`, `total`, `conversion`; `credit_known` |
| `ads_stages_list` | `m1{conversations, spend, cost_per_conversation}` · `m2{ad_conversations, answered, answered_rate, median_first_response_minutes, booked, attended, booked_rate, attended_rate}` · `m3{quote_presented, accepted, paid, paid_rate, budget_cohorts}` · `reference` (healthy writing→booking 10–15 %) · `weakest` |
| `ads_cohorts_list` (≤366 d) | per arrival month: `spend`, `patients`, `cost_per_new_patient`, `m0..m5`, `to_date`; `comparison`, `days_to_first_payment{median,p25,p75}`, `pipeline_uncollected` |
| `ads_monthly_return_list` | per month `first_value`, `later_value`, `spend`, `measured` (null months = unmeasured) |
| `ads_report_list` (`level` campaign|ad_set|ad) | the «Informe» table: `spend`, `funnel{conversations, replied, appointments, attended, closes}`, `cost_per{conversation, appointment, attended, close}`, `cash`, `return`, `accepted_*`, `patient_return`, `meta{conversations_started, cost_per_conversation}`; `tail` (non-ad conversations), `totals`, `reconciliation` |
| `ads_attributed_sales_list` (`campaign_id` required, `ad_id?`) | credited conversions and people with payments (names need `contacts:read` + `clinic:read`) |
| `ads_people_list` (`metric`, one of `campaign_id|ad_id|unplaced`, `limit` default 1000) | the people behind one number — personal data, large; ask before pulling |
| `ads_conversion_source_list` | where bookings, sales, payments come from |
| `ads_feed_list` (`stage`, `only_ads`, `campaign_id`, `since`, `before`, `limit≤50`), `ads_feed_journey_list {id}` | outcomes one by one; a journey's `join_method` (ctwa_referral, click_id, link_token, anonymous_id) |
| `ads_health_list {days}` | `trust{traceable_pct_by_value, instrumentation.tracking_healthy}`, `utm`, `attribution_coverage` |
| `ads_measurement_list` | `open`/`recent` incidents, each with `action.path` (the screen that fixes it) |
| `ads_conversion_sync_status_list` | Envío a Meta: state not_started|on|partial|off|blocked, datasets (WhatsApp, website pixel, Instagram), one lane per stage with Meta event, value, on/off, wiring verdict, 7-day deliveries |
| `ads_meta_send_list`, `ads_meta_send_comparison_list` | when sending started; equal windows before/after: booking rate, spend, citas, first-time payers |
| `ads_briefing_list {screen, from, to | window, wait=1}` | `lead` sentence, `lines[]`, `facts[]`, `source` |
| `ads_experiments_list`, `ads_experiments_current_list`, `ads_experiments_readout_get {id}` | A/B arms (control/test, `optimization_event`), readout = cost per paying patient / per accepted quote per arm |
| `ads_actions_list {screen: resumen|campanas|atribuidos|creativos|salud|envio, from, to}` (from/to required) → `ads_actions_preview`/`_execute`/`_dismiss`, `ads_actions_executions_list`, `_rollback` | the only sanctioned way to change something (budget, pause, send setup); `ads:write` |
| `ads_goal_*` | the monthly goal |
| Integrations: `GET /integrations/meta-ads` (+ `/ads`, `/pages`) | the Meta connection (`integrations:read` or `ads:read`) |

## How an ad reaches a conversation

- Click-to-WhatsApp: Meta's `referral` lands in `conversation.ad_referral` (ad id, headline, body); REST `GET /conversations` exposes it as `ad_origin{platform, kind, ad_external_id, ad_name, campaign_name}` and filters with `fromAd=true`. The MCP `conversations_list` has no such filter — use `call_operation conversations_list {fromAd:true, fromDate, toDate}`.
- `conversation.source` / `lead.source` **never** say "ad" (closed vocabulary: conversation, marketplace, manual, import, ai_agent, website, form, portals). Ad origin lives only in `ad_referral` / `ad_origin`.
- Imported history: `contact_ad_touch` matches within 24 h before / 2 min after the first message. Website and booking page: `contact.first_touch`, `appointment.attribution` (UTMs, fbclid/gclid).
- Ads «lead_created» = a contact's first conversation (skipped if they ever paid); it is not a CRM lead.
- Declared source («¿Cómo nos conociste?»): contact attribute `declared_source` from the harness tool; taxonomy facebook, instagram, tiktok, google, friend_family, … ; tenant setting `declared_source.ask`.

## Envío a Meta (conversions)

Facts queue in `atribu_outcome_outbox` per stage (lead_created, appointment_booked, checkout_started, deposit_paid, appointment_attended, quote_presented, closed_won, first_payment, returning_first_payment, payment_received) and go to Meta CAPI. Website lane: Lead, Schedule, InitiateCheckout, Purchase; clinic events as opaque custom events without value; **new-patient Purchase** = first payment with the accepted plan value (capped at the tenant p95); returning patients = custom event without value; instalments are not exported; WhatsApp lane uses Meta's 14 standard names (LeadSubmitted, QualifiedLead, …). No health words ever reach Meta; opted-out contacts are attributed but never exported. Changes only via `ads_actions_list {screen:"envio"}`.

## Vocabulary and rules (ADR 0119, 0111)

- personas = wrote; pacientes/clientes = paid. llegaron = first message from an ad; volvieron = later ad-opened conversation. Return counts payments within 12 months of an ad conversation.
- ~50 outcomes before a ranking means anything; accepted value is sent once.
- Entry services (`clinic_service.is_entry`) are the only bookings that count as first visits: `clinic_services_entry_proposals` / `clinic_services_set_entry {service_ids, is_entry}`.
- Add-on: CLP 99.000/month; sandbox workspaces always get the sample.

## Size traps

`ads_people_list` (1000 rows of personal data), `ads_scorecard_list` / `by:"ad"` on large accounts, `ads_report_list?level=ad`, `series=1` on campaigns/creatives/overview, `ads_conversion_sync_status_list` (per-day series per lane), `ads_attributed_sales_list` (`people[]`), `ads_briefing_list wait=1` (~8 s). Results are pretty-printed JSON; when one overflows, the harness saves it to a file — read the file.
