---
name: vitrina-campaigns
description: "Plan and run outbound messaging in a Vitrina workspace over MCP/REST: WhatsApp templates (create, submit to Meta, categories, buttons, media header, approval status), audiences and who is marketable, campaigns (create, test-send, schedule, send, pause, stats, replies), follow-up rules and subscriptions, recontacto (re-engaging lost leads) and the approval queue for outbound messages. Use when the user mentions campaña, plantilla de WhatsApp, template, enviar un mensaje masivo, audiencia, recontacto, seguimiento, follow-up, aprobaciones pendientes, 'mandar una promo', 'avisar a todos los pacientes', or asks why a template is pending or rejected — even without the word 'campaign'."
---

# Campaigns, templates, follow-ups

Three ways Vitrina reaches people proactively: a **campaign** (one template to an audience, WhatsApp/email/voice), a **follow-up** (a rule that schedules a message for one person after a trigger, fulfilled by the AI or a human) and **recontacto** (daily re-engagement of lost leads under a cap). WhatsApp templates must be approved by Meta before any of them can use them. Every send that reaches a customer is listed in [`references/campaigns-surface.md`](references/campaigns-surface.md) with the scope it needs; **confirm with the user before any step that sends**, and never bypass the approval queue.

## Step 1 — What exists

`whatsapp_templates_list {messaging_account_id?, status?}` (APPROVED is the only usable status; PENDING waits for Meta; REJECTED carries the reason), `whatsapp_templates_categories_list` (the workspace's usage categories), `audiences_list` + `audience_counts {audience_id}`, `campaigns_list {status?}` + `campaign_stats {campaign_id}`, `followups_list` + `followups_overview`, `followups_recontacto_stats {since_days}`, `outbound_approvals_list {rail?}` (sends waiting for a human). Reply measurement: `campaign_stats` (delivered, read, replied) and `insights_sources_get` for conversations the campaign opened.

Done when: you know which templates are approved, which audiences exist with counts, what is scheduled or waiting approval, and how past sends performed.

## Step 2 — Template

Name `^[a-z0-9_]+$`, language `es`/`es_CL`, category MARKETING | UTILITY | AUTHENTICATION (run `whatsapp_templates_category_check_create` first: Meta reclassifies promotional UTILITY to MARKETING, which costs more and needs marketing consent), body with `{{n}}` placeholders bound to contact fields, optional header (text or media: upload media over REST first, multipart), footer, buttons (QUICK_REPLY | URL | PHONE_NUMBER | FLOW, text ≤ 25). `whatsapp_templates_create` returns PENDING; approval is asynchronous (minutes to a day) — `whatsapp_templates_sync_create {messaging_account_id}` refreshes. Write the body in the business's register, one idea, a clear reason to reply; a template nobody answers is wasted spend.

Done when: the template is APPROVED or the user knows it is PENDING and what to do if REJECTED.

## Step 3 — Audience and consent

An audience is a saved filter (REST `/audiences`, campaigns:write; preview needs contacts:read). Before sizing, `contacts_marketable_count` and the consent rules in `vitrina-contacts`: marketing templates go only to people with marketing consent; service/utility messages to anyone with an open relationship. Exclude staff and bot-disabled contacts. Say the final count and what was excluded.

Done when: audience id, count and consent basis are written down.

## Step 4 — Send safely

Campaigns are REST-only writes (`POST /campaigns` → `/:id/test-send {recipients ≤5}` → `/:id/schedule {scheduled_at}` or `/:id/send`; `campaign_pause`/`campaign_resume` over MCP). Always test-send to the user first. Sends by API keys trip loop protection (same content to > 20 contacts in 10 min, or > 60 sends/min → 409 `OUTBOUND_WARNING` until repeated with `acknowledge`; 422 `OUTBOUND_BLOCKED` is final); connected apps instead queue past 3 distinct contacts in 10 minutes. Single messages from a conversation need `conversations:write` + `messages:send`. The approval queue (`outbound_approvals_approve` sends; `_reject`) is where parked sends wait — approve only what the user explicitly confirms.

Done when: the campaign is scheduled or sent with the user's explicit go, and the test message was seen.

## Step 5 — Follow-ups and recontacto

Rules: `followups_create {name, description, trigger_key}`; subscribe a person `followups_subscribe {followup_id, contact_id, conversation_id?, fire_at?, preferred_channel?, fulfiller_kind: ai_agent|human_self}` (schedules a future message); cancel with `followups_subscription_cancel`. Recontacto: `followups_recontacto_readiness` (templates, caps, lookback) → `followups_recontacto_preview` (who would be contacted today) → `followups_recontacto_config {enabled, daily_cap, lost_lookback_days, …}` → `followups_recontacto_run` (**sends when the key holds campaigns:write**) → `followups_recontacto_attempts` / `_stats`. The lead reviewer (`followups_lead_review_config`) decides which lost leads qualify.

Done when: the rule or the recontacto config is in place, the preview was shown, and nothing was sent without a go.

## Step 6 — Report

What exists, what was created (ids, template status), audience size and consent basis, what was sent or scheduled, replies so far, and the approvals still waiting. Costs: Meta charges per template conversation by category; say which category the send used.
