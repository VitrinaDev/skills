---
name: clinic-agenda
description: "Read and manage a clinic's agenda in Vitrina (healthcare workspaces connected to Dentalink/Medilink via HealthAtom, or Reservo): who works when, free slots per professional, occupancy for the coming days, bookings, cancellations and no-shows, the waitlist, reminders, which services count as a first visit (entry services), and whether the vendor sync is healthy — so demand from ads and the agent actually has hours to land on. Use when the user asks about agenda, horas disponibles, cupos, ocupación, profesionales, citas de la semana, inasistencias, lista de espera, recordatorios, Dentalink/Medilink sync, 'no hay horas', or why the agent could not book — even without the word 'clinic'."
---

# Clinic agenda

The agenda lives in the clinic's own system (Dentalink or Medilink through HealthAtom; Reservo); Vitrina mirrors professionals, services, statuses and citas, books through the vendor's engine, and the AI agent uses the same `find_slots` / `book_appointment` tools. Two id spaces coexist: vendor ids (`profesional_id`, `sucursal_id` on `clinic_agenda_list`) and Vitrina uuids (`professional_id`, `location_id` on the feed and booking operations). Tool inputs: [`references/agenda-surface.md`](references/agenda-surface.md). Scopes `clinic:read` / `clinic:write` (+ `appointments:*`); the tools exist only on healthcare workspaces.

**Health data.** A plain API key returns real patient names, RUT and phones; a connected app gets pseudonyms. Keep outputs to counts and initials unless the user needs a specific patient; never paste rows into tickets or chats; the clinical record, consents and documents are not reachable over MCP at all.

## Step 1 — Who works and when

`clinic_professionals_list {active:true, limit}` (weekly `schedule` mon..sun; `null` = not yet synced, not "no days"), `clinic_agenda_profesionales {from, to}` for who has citas in the window, `clinic_services_list {is_entry:true}` for first-visit services, `clinic_statuses_list` for the estado vocabulary (buckets pending_hold | confirmed | cancelled | completed | no_show). `healthatom_sync_state {id}` first if numbers look stale (`healthatom_accounts_list` gives the id).

Done when: the roster, their hours, the entry services and the last sync time are known.

## Step 2 — Occupancy and free slots

`clinic_agenda_list {from, to}` (YYYY-MM-DD, `to` exclusive, ≤ 8 days; filter by vendor `profesional_id` = the roster's `external_id`; 100–180k chars for a busy week — count, do not read) is the booked side; `call_operation clinic_agenda_availability_list {from, to, limit ≤100}` is the free side (each slot has a `slot_ref`). **Known defects (filed as vitrina-app#3980):** its `professional_id` filter rejects both the roster uuid and the vendor id, `to` is inclusive, and the 100-slot cap has no truncation marker — so sweep the whole clinic in windows small enough to stay under 100 slots (one or two days at a time) and group by professional yourself; keep the sweep to the window the user asked for. Occupancy = booked / (booked + free) per professional per day; say it per professional, not as one clinic number. A professional with zero free slots for weeks while ads keep sending that service is the single most expensive agenda fact there is (`vitrina-ads` and `analyze-funnel` will have seen it from the other side).

Done when: for each professional in the window you can state booked, free and the next free slot.

## Step 3 — Book, move, cancel, waitlist

Book only through the vendor engine: `clinic_agenda_availability_list` → `clinic_agenda_appointments_create {slot_ref | professional_id + starts_at + ends_at, contact_id, service…}` (`clinic:write`). Never `appointments_create` for a clinic (it defaults to `kind: test_drive` and bypasses the engine). Move: `clinic_agenda_appointment_update`. Cancel: `appointment_cancel_create` (REST, `appointments:delete` + `messages:send`; it messages the patient — confirm first; the MCP `appointments_cancel` also messages but only checks `appointments:delete`). Attendance: `appointment_update {status: completed|no_show}`. Waitlist: `clinic_waitlist_list {status:"live"}`, `clinic_waitlist_add {contact_id, professional_id?, date_from/to, time_from/to, urgency rojo|amarillo|verde, note}` (one live entry per contact+professional; it triggers automatic WhatsApp offers when a slot opens — say so), `clinic_waitlist_cancel {id}`.

Done when: every booking change is confirmed by the user, applied through the engine, and the patient-facing consequence (a message) was stated beforehand.

## Step 4 — No-shows, reminders, sync

No-show and confirmation rates per professional: count `no_show` vs `completed` from the agenda window (the `/clinic/insights/inasistencias|confirmaciones` screens are REST-only). Reminders: `clinic_reminder_plan_get`, `clinic_reminders_list {limit, offset}` (what was sent, when; the plan itself is edited in the UI). Sync: `healthatom_sync_state {id}`, `healthatom_sync_run {id, backfill?}` only enqueues; a sync older than an hour during business hours, or citas the clinic sees that Vitrina does not, is Vitrina's to fix — file it with `ai_agents_change_request_create` or support and the account id.

Done when: no-show rate, reminder coverage and sync freshness are stated, and sync problems are filed.

## Step 5 — Report

Per professional: hours, booked, free, next free, no-shows; entry services; waitlist size; sync state; and the one agenda change that would move demand most (open hours for the service the ads sell, re-balance a professional, shorten a slot type). Counts and initials only.
