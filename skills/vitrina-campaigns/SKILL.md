---
name: vitrina-campaigns
description: "Plan and run outbound messaging in a Vitrina workspace over MCP/REST: WhatsApp templates (create, submit to Meta, categories, buttons, media header, approval status), audiences and who is marketable, campaigns (create, test-send, schedule, send, pause, stats, replies), follow-up rules and subscriptions, recontacto (re-engaging lost leads) and the approval queue for outbound messages. Use when the user mentions campaña, plantilla de WhatsApp, template, enviar un mensaje masivo, audiencia, recontacto, seguimiento, follow-up, aprobaciones pendientes, 'mandar una promo', 'avisar a todos los pacientes', or asks why a template is pending or rejected — even without the word 'campaign'."
---

# Campaigns, templates, follow-ups

Three ways Vitrina reaches people proactively: a **campaign** (one template to an audience, WhatsApp/email/voice), a **follow-up** (a rule that schedules a message for one person after a trigger, fulfilled by the AI or a human) and **recontacto** (daily re-engagement of lost leads under a cap). WhatsApp templates must be approved by Meta before any of them can use them. Every send that reaches a customer is listed in [`references/campaigns-surface.md`](references/campaigns-surface.md) with the scope it needs; **confirm with the user before any step that sends**, and never bypass the approval queue. On a connector the writes need packs: «Campañas y plantillas» (templates, flows, audiences, campaigns, email templates), «Seguimientos» (follow-ups, recontacto) and, for anything that reaches a customer (send, schedule, resume, test-send, flow test-send, approving a recontacto attempt), also «Mensajes a clientes». Probe with `describe_operation {operation_id}`; `Unknown operation` means the pack is missing — tell the user to add it in Vitrina → Configuración → Conectar tu IA (MCP) → Apps conectadas → «Editar permisos» (no reconnect).

## Step 1 — What exists

`whatsapp_templates_list {messaging_account_id?, status?}` (APPROVED is the only usable status; PENDING waits for Meta; REJECTED carries the reason), `whatsapp_templates_categories_list` (the workspace's usage categories), `audiences_list` + `audience_counts {audience_id}` (`call_operation audience_counts_list {params:{id}}`), `campaigns_list {status?}` + `campaign_stats {campaign_id}` (`call_operation campaign_get {params:{id}}` and `campaign_recipients_list` for delivery states), `email_templates_list`, `whatsapp_flows_managed_list`, `followups_list` + `followups_overview`, `followups_recontacto_stats {since_days}`, `outbound_approvals_list {rail?}` (sends waiting for a human). Reply measurement: `campaign_stats` (delivered, read, replied) and `insights_sources_get` for conversations the campaign opened.

Done when: you know which templates are approved, which audiences exist with counts, what is scheduled or waiting approval, and how past sends performed.

## Step 2 — Template

Name `^[a-z0-9_]+$`, language `es`/`es_CL`, category MARKETING | UTILITY | AUTHENTICATION (Meta reclassifies promotional UTILITY to MARKETING, which costs more and needs marketing consent: choose the category by what the message does. Vitrina's category predictor and parameter binder spend model budget and are not available to a connector; creating the template still runs them server-side, as the UI's save does), body with `{{n}}` placeholders bound to contact fields, optional header (text, or media: `call_operation whatsapp_templates_header_media_create {body:{filename, content, content_encoding: utf8|base64, content_type}}` returns a public `url` for `header_media`; JPEG/PNG ≤ 5 MB, MP4/PDF ≤ 16 MB, keep one MCP call under ~1 MB), footer, buttons (QUICK_REPLY | URL | PHONE_NUMBER | FLOW, text ≤ 25). `call_operation whatsapp_templates_create` (pack «Campañas y plantillas») returns PENDING; approval is asynchronous (minutes to a day) — `whatsapp_templates_sync_create {messaging_account_id}` refreshes. Write the body in the business's register, one idea, a clear reason to reply; a template nobody answers is wasted spend.

Done when: the template is APPROVED or the user knows it is PENDING and what to do if REJECTED.

## Step 3 — Audience and consent

An audience is a saved filter (`call_operation audiences_create` / `audience_update` / `audience_overrides_create` / `audience_duplicate_create`, pack «Campañas y plantillas»). Definitions and counts are readable; **listing the members of an audience is not available to a connector** (health data) — reason from counts and the filter. Before sizing, `contacts_marketable_count` and the consent rules in `vitrina-contacts`: marketing templates go only to people with marketing consent; service/utility messages to anyone with an open relationship. Exclude staff and bot-disabled contacts. Say the final count and what was excluded.

Done when: audience id, count and consent basis are written down.

## Step 4 — Send safely

Campaign writes are published operations (`campaigns_create` → `campaign_test_send_create {recipients ≤5}` → `campaign_schedule_create {scheduled_at}` or `campaign_send_create`; `campaign_pause_create`, `campaign_resume_create`, `campaign_cancel_create`), exact params in [`references/campaigns-surface.md`](references/campaigns-surface.md). Send, schedule, resume and test-send need «Campañas y plantillas» **and** «Mensajes a clientes». Before the user says yes, state the customer impact in one line: how many people (the audience count), through which channel and template, when, and that a sent message cannot be recalled (pause stops the rest only). Always test-send to the user first. Sends by API keys trip loop protection (same content to > 20 contacts in 10 min, or > 60 sends/min → 409 `OUTBOUND_WARNING` until repeated with `acknowledge`; 422 `OUTBOUND_BLOCKED` is final); connected apps instead queue past 3 distinct contacts in 10 minutes. Single messages from a conversation need `conversations:write` + `messages:send`. The approval queue (`outbound_approvals_approve` sends; `_reject`) is where parked sends wait — approve only what the user explicitly confirms.

Done when: the campaign is scheduled or sent with the user's explicit go, and the test message was seen.

## Step 5 — Follow-ups and recontacto

Rules (pack «Seguimientos»; connector ids, `sk_` names in the surface reference): `followups_create {name, description, trigger_key}`, `followup_replace`, `followup_active_create`, `followup_delete`. Subscribe a person with `followups_subscriptions_create {followup_id, contact_id, conversation_id?, fire_at?, preferred_channel?, fulfiller_kind: ai_agent|human_self}` — it schedules a future message to that person, so say so first; cancel with `followups_subscription_cancel_create`. Recontacto: `followups_recontacto_readiness_list` (templates, caps, lookback) → `followups_recontacto_preview_list` (who would be contacted today) → `followups_recontacto_replace {enabled, daily_cap, lost_lookback_days, …}` (turning it on, or any self-sending rung, also needs «Campañas y plantillas») → `followups_recontacto_run_create` (forces both sweeps and **sends** when the connection also holds «Campañas y plantillas»; the sweep writes AI-made reasons, so confirm first) → `followups_recontacto_attempts_list` / `followups_recontacto_stats_list`. Approving one attempt (`followups_recontacto_attempt_approve_create`) delivers it in the same call and needs «Seguimientos», «Campañas y plantillas» and «Mensajes a clientes»; name the customer and the message before asking. The lead reviewer is `followups_lead_review_replace`. Follow-up AI drafts are not available to a connector (model spend): write the text yourself and show it.

Done when: the rule or the recontacto config is in place, the preview was shown, and nothing was sent without a go.

## Step 6 — Report

What exists, what was created (ids, template status), audience size and consent basis, what was sent or scheduled, replies so far, and the approvals still waiting. Meta charges per template conversation by category; say which category the send used.
