# Clinic agenda surface (healthcare workspaces only)

| Tool | Inputs | Scope |
|---|---|---|
| `clinic_agenda_list` | `from, to` YYYY-MM-DD (`to` exclusive, ≤8 days), vendor `profesional_id?`, `sucursal_id?` — includes cancelled citas; large for a busy clinic | clinic:read |
| `clinic_agenda_profesionales {from, to}`, `clinic_agenda_me {}` | | clinic:read |
| `clinic_professionals_list` | `search? (≥2), active?, page?, limit ≤200` — `schedule` mon..sun, null = not synced | clinic:read |
| `clinic_professional_get {id}` | includes the full vendor payload | clinic:read |
| `clinic_services_list` | `search?, active?, review_state?, is_entry true|false|'unclassified', page?, limit?` | clinic:read |
| `clinic_services_entry_proposals {}` → `clinic_services_set_entry {service_ids ≤500, is_entry}` | entry services are the only bookings Ads counts as first visits | clinic:read / write |
| `clinic_service_review`, `clinic_status_create/_update` (buckets pending_hold|confirmed|cancelled|completed|no_show) | | clinic:write |
| `clinic_statuses_list {active?}` | | clinic:read |
| `clinic_waitlist_list {status live|all}`, `clinic_waitlist_add {contact_id, professional_id?, date_from, date_to, time_from?, time_to?, urgency rojo|amarillo|verde, note?}` (triggers automatic WhatsApp offers), `clinic_waitlist_cancel {id}` | | clinic:read / write |
| `clinic_reminder_plan_get {}`, `clinic_reminders_list {limit, offset}` | plan PUT is UI-only | clinic:read |
| `healthatom_accounts_list/_get`, `healthatom_sync_state {id}` | need `healthatom:read` explicitly (`healthatom:*` → `clinic:*` is one-way; `clinic:read` does not open these) | healthatom:read |
| `healthatom_accounts_create {name, product dentalink|medilink, token, …}`, `healthatom_accounts_test`, `healthatom_sync_run {id, backfill?}` (enqueues only), `healthatom_patient_invoices_list` | | write / read |
| `appointments_list {status[], kind[], from, to, owner_user_id?, limit ≤100, cursor?}` → `{rows, next_cursor}` (app v12.5+), `appointments_get {id}`, `appointments_availability`, `appointments_config_get/_set`, `appointment_types_list/get` | generic agenda (test drives etc.); `appointments_create` defaults `kind: test_drive` and bypasses the clinic engine — do not use for clinics | appointments:* |

`call_operation` (Clinic Agenda ops, beta): `clinic_agenda_feed_list {from, to, professional_id? (uuid), location_id? (uuid)}`, `clinic_agenda_availability_list {from, to (inclusive today), limit ≤100, allow_overbook?:false}` → slots with `slot_ref` (`professional_id` filter broken as of 2026-10-09 — see the SKILL note), `clinic_agenda_appointments_create {slot_ref | professional_id + starts_at + ends_at, contact_id, …}` (clinic:write), `clinic_agenda_appointment_update`, `clinic_waitlist_demand_list`, `appointments_list` (cursor, `contact_id`), `appointment_update {status completed|no_show}`, `appointment_cancel_create` (appointments:delete + messages:send), `clinic_professionals_*`, `clinic_services_*`, `clinic_specialties_*`, `clinic_insights_comercial_list`, `clinic_insights_resultados_list`, `clinic_insights_resultados_people_list {metric}`, `clinic_booking_drafts_list` (+contacts:read).

REST-only (interna): `/clinic/insights/ocupacion|inasistencias|confirmaciones` (clinic:read or clinic_insights:read), `/clinic/professionals/{id}/patterns`, `/clinic/exceptions`, reminder plan PUT, waitlist offer/accept/decline, `POST /clinic/appointments/{id}/status` (Reservo).

Never over MCP: patients register, clinical record, consents, documents (`clinic_patients:*`, `clinic_record:*` over REST only). Pseudonyms («M.F. · #1001») apply to connected apps only; API keys see real identities. Clinical `flags` need `clinic_record:read`.

Display id for appointments: `A-n`. Webhooks: `appointment.booked|rescheduled|cancelled|completed|no_show|reminded|imported`.
