---
name: vitrina-finanzas
description: "Review and fix how a Vitrina Finanzas workspace classifies its money, over Vitrina's MCP: whether the plan de cuentas (chart of accounts) is in order, what landed in each account, what is left unclassified, duplicate or unused accounts, and the rules that classify new documents and bank movements. Reads first, proposes with a reason, previews, and only then classifies, confirms, creates rules or adjusts accounts, always after the user's OK. Use when the user mentions Finanzas, plan de cuentas, cuentas contables, clasificar, sin clasificar, sin cuenta, reglas, egresos sin documento, Por resolver, Resultado, cierre de mes, or pastes the «Pídeselo a tu agente» prompt from a Vitrina Finanzas screen — even if they do not say 'Vitrina'."
---

# Vitrina Finanzas: review the plan, classify, create rules

Finanzas puts every document (boletas, facturas, boletas de honorarios, gastos) and every bank or card movement on an account of the workspace's **plan de cuentas**. Vitrina seeds the plan from a template for the workspace's vertical (a clinic gets `clinic.*` accounts), and an import can add its own accounts on top. The plan is a classification tree, **not double-entry accounting**. Each account has:
- `kind`: `ingreso`, `costo`, `gasto` or `no_operacional` («Fuera del resultado»: retiros, préstamos, activos, patrimonio);
- `behavior` (costos and gastos only): `fijo` (paid the same in a slow month: rent, salaries) or `variable` (moves with activity: supplies, labs, commissions);
- `no_document`: its payments need no boleta or factura (salaries, social security, taxes, withdrawals), so they never count as «egresos sin documento».

Most owners should never need to edit the plan. The job is usually: classify what is left, add a rule for repeating suppliers, and tidy duplicate or unused accounts.

Every call goes through `call_operation {operation_id, ...params}`. Amounts are whole CLP.

## Step 0: Connection and permissions
- `call_operation {operation_id:"finanzas_accounts_list"}`. A 402 `ENTITLEMENT_NOT_ACTIVE` means the workspace has no Finanzas: say so and stop. A 403 means the member's role has no Finanzas access: stop.
- Writing needs the connection's **«Finanzas»** pack (off by default). The first write that answers 403 means it is off. Tell the user: «Activa el permiso Finanzas en Vitrina › Configuración › Avanzado › Conectar tu IA (MCP) › Permisos, y vuelve a pedírmelo.» Rules and accounts also need an admin role: a Contador seat is read-only, so give them the proposals as a list to forward.
- Patient names arrive redacted («Paciente A. P.»). Never ask for or infer full names.

Done when: you know you can read, and whether you can write.

## Step 1: Frame the month (read only)
- Month: the one the user names, else the one in the pasted prompt, else the last closed month (`finanzas_accounts_review_get` with no `month` picks it).
- `finanzas_accounts_review_get {month}` gives `classified_pct`, `unclassified` (count, total, by kind, `with_proposal`), `unclassified_income`, and `findings` (`unclassified`, `duplicate_import` pairs, `unused` account ids).
- `finanzas_accounts_list {usage_month: month}` gives the tree with each account's `usage` (total, count, last used, used in 6 months).
- `finanzas_rules_list` gives the active rules (a rule names a contraparte and/or a text, an amount range, a direction, a document kind, and the account).

If `finanzas_accounts_review_get` is not available (an older server), fall back to `finanzas_resultado_list {from: month, to: month}` (rows `egresos_sin_clasificar`, `ingresos_sin_clasificar`, per-account rows) and compute the rest yourself.

Tell the user the answer in one line before anything else, e.g. «Octubre: 96 % de los egresos tiene cuenta. Quedan 7 sin cuenta ($1.590.984), hay 2 cuentas importadas repetidas y 31 sin uso.» If nothing is pending, say the plan is in order and stop unless they asked for more.

Done when: the user has the answer and you know what to propose.

## Step 2: Build proposals (still read only)
**Unclassified items.** `finanzas_resultado_items_list {row:"egresos_sin_clasificar", month}` (page with `offset` until `total` is covered), and `row:"ingresos_sin_clasificar"` if `unclassified_income.count > 0`. For each item, find the account in this order and keep the reason:
1. An open, ready `classify` case: `finanzas_cases_list {kind:"classify", month}`, then `finanzas_case_get {id}` for its proposal. Reason: «Vitrina ya lo propone».
2. The same contraparte's earlier items: `finanzas_contrapartes_list {q}`, then `finanzas_contraparte_timeline_list {id}` and `finanzas_classifications_list {type, ids}`. Reason: «Así quedaron sus documentos de septiembre».
3. A rule that almost matched (same contraparte, other amount range or text). Reason: «La regla X no aplicó por el monto».
4. Otherwise propose from the description and the account names, mark it **low confidence**, and let the user choose.
Income documents (`ingreso`) go to an `ingreso` account. A **movement is never put on an `ingreso` account** (income comes from documents).

**Rules.** A contraparte (or a stable text in the description) that shows up 2+ times with the same proposed account is a rule candidate. Prefer contraparte over text, and add an amount range only when the same supplier sells to two accounts. Check `finanzas_rules_list` for an existing rule first, since two active rules that disagree cancel each other and neither applies.

**Accounts.**
- `duplicate_import` pairs: propose to archive the imported one when it has no money in 6 months. When it has money, propose to reclassify its lines onto the template account first, then archive. Never delete.
- `unused`: list them grouped by kind. Archiving is optional and cosmetic: say so.
- Suspicious settings: a salary, social-security, tax or withdrawal account without `no_document`, or rent/salaries marked `variable`. Propose the change and explain the effect (Resultado's «Egresos sin documento», Costos y equilibrio's fixed costs).

Present **one table** for the items (item, date, amount, proposed account, reason, confidence), then a list of rules (condition → account, plus how many pending items each would take), then the account changes. Ask: «¿Lo aplico así? Puedes cambiar cualquier fila.» Write nothing yet.

Done when: every proposal has a reason the user can check, and the user answered.

## Step 3: Apply, in this order, only what the user approved
1. **Rules first**, since they clear pending items in bulk and keep classifying new ones:
   `finanzas_rules_create {contraparte_id|contraparte_rut|contraparte_name, text_contains?, amount_min_clp?, amount_max_clp?, direction?, document_kind?, target, account_name}` with an `Idempotency-Key`, then `finanzas_rule_pending_list {id}` **(the dry run: count, total, up to 10 items)**. Show it. On OK, call `finanzas_rule_apply_create {id}`. If the preview differs from what you promised, stop and ask (for example, it would take items the user put elsewhere).
2. **Ready cases** the user accepted: `finanzas_case_confirm_create {id}` (or `finanzas_case_confirm_edited_create` with the user's change).
3. **The rest:** `finanzas_classifications_bulk_create {items:[{type, id}], account_name, period?}` (`period` = `YYYY-MM` for the accrual month; omit it to keep each item's own month), where one call = one account, ≤ 500 items, one `Idempotency-Key` per call. It is all or nothing: on 409/422, read `details.reason` (`movement_linked`, `movement_to_income`, `account_ambiguous` with `details.candidates`, `sum_mismatch`), fix or ask, and retry only the failed call. For a split, or one item that changes account, use `finanzas_classification_replace`.
4. **Accounts:** `finanzas_account_update {id, behavior?|no_document?}`, `finanzas_account_archive_create {id}` (one explicit yes per account, or per listed group), `finanzas_accounts_create` only when the user asks for a new account.

Then re-read `finanzas_accounts_review_get {month}` and report: the new percentage, what changed (counts per account, rules created and what they took), and how to undo each part.

Done when: the re-read matches what you reported.

## Safety rules (always)
- **The first pass reads only.** No write without an OK on the exact table you showed.
- **Preview before applying:** every rule through `finanzas_rule_pending_list`. Bulk classification has no dry run, so the approved table IS the preview, and the call must match it item for item.
- **Ask again** (even after a general OK) when: one step changes more than 20 items; an item belongs to a **closed month** (the API needs `adjustment_reason`, so ask the user for the reason in their words and pass it); you would reclassify something a person classified (`source: "manual"`); or a rule would take more pending items than you announced.
- **Never:** delete accounts or rules; rename accounts; pause or archive rules unasked; touch a reconciled movement; put a movement on an `ingreso` account; connect or disconnect banks or the SII; close or reopen a month; give a password or a clave.
- When unsure about an account, ask. A wrong account moves the owner's Resultado and break-even.
- **Undo paths to report:** reclassify with `finanzas_classification_replace`; unclassify with `finanzas_classification_delete`; pause a rule with `finanzas_rule_pause_create` (archive is final); restore an account with `finanzas_account_restore_create`. Rule-applied items carry the marker «Regla» and show in Hecho por Vitrina (`finanzas_automatic_actions_list`).
- **Language:** answer in the user's language (Spanish, tú, short). Call accounts by their names in the plan. Imported accounts are «importadas»: never name the system they were imported from. No accounting jargon the screens don't use (no «asiento», «debe/haber»).

## Operations used
Reads: `finanzas_accounts_review_get`, `finanzas_accounts_list`, `finanzas_resultado_list`, `finanzas_resultado_items_list`, `finanzas_cases_list`, `finanzas_case_get`, `finanzas_rules_list`, `finanzas_rule_get`, `finanzas_rule_pending_list`, `finanzas_contrapartes_list`, `finanzas_contraparte_timeline_list`, `finanzas_classifications_list`, `finanzas_classification_get`, `finanzas_automatic_actions_list`.
Writes («Finanzas» pack): `finanzas_rules_create`, `finanzas_rule_apply_create`, `finanzas_rule_pause_create`, `finanzas_case_confirm_create`, `finanzas_case_confirm_edited_create`, `finanzas_classifications_bulk_create`, `finanzas_classification_replace`, `finanzas_classification_delete`, `finanzas_account_update`, `finanzas_account_archive_create`, `finanzas_account_restore_create`, `finanzas_accounts_create`, `finanzas_accounts_review_dismiss_create` (only when the user says a «duplicate» pair is not the same account).
