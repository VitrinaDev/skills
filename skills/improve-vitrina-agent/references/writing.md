# Writing like the business's own team

How an agent *sounds* is a change like any other, with stricter rules, because the model copies every example it reads and a stilted register costs sales before a person ever takes over. Read this before you change tone, register, punctuation, greetings, examples, or anything a customer reads word for word.

## 1. Settings first, text last

Two things are workspace settings, not prompt text. Change the setting; never write a rule for them in a prompt, skill or KB document:

| What | Workspace setting (`PUT /tenant/settings`, key `voice`, sent whole) | Agent override (draft, `behavior_policies`) |
|---|---|---|
| Opening «¿» «¡» | `opening_marks`: `none` (default: no opening marks, the way people type in a Chilean chat) or `keep` | `opening_marks`: `inherit` / `none` / `keep` |
| Register of the AI | `agent_register`: `tu`, `usted`, `mirror` (tú until the customer uses usted); absent = the agent's instructions decide | `register`: `inherit` / `tu` / `usted` / `mirror` |

`none` is enforced at send time on every AI reply and follow-up, so old examples with «¿» do not need rewriting. `voice` is replaced whole on `PUT`: read it, change your key, send every stored key back (`brand_name` and `register` drive the WhatsApp templates). Find the call on a connector with `search_operations "tenant settings"`. Words the business never says (slang, bot phrases) go in `settings.agent_language.banned_terms`; a reply that uses one is rewritten before it is sent.

## 2. Measure against the team before writing a word

1. Pull the team's own messages from the workspace's conversations: `sender_type = human_user` rows (text and transcribed voice notes; ignore canned quick replies). Fifty or more, across several people.
2. Pull the agent's last few hundred replies (`sender_type = ai_agent`, type `text`).
3. Compare, in numbers: median length, share of replies ending in a question, share opening with the customer's name, share with «¿/¡», bubbles per turn, recurring openers («Perfecto,», «Genial,», «Entendido,»).
4. Quote real team lines; they become the examples in the prompt.

Done when you can state the gap in one line, for example «team: 41 chars, 12 % questions, name only in the greeting; agent: 171 chars, 41 % questions, a third of replies open with the name».

## 3. Rules every tone change must keep

- **Examples are templates.** The model copies an example over a rule that contradicts it. Every example in the prompt and skills must already look like the target (punctuation, register, length). Change examples first, rules second.
- **No varying facts inside an example.** Never hardcode hours, prices, dates or stock in an example («hoy estamos hasta las 19:00» was repeated on a Sunday). Use a placeholder («hasta las [cierre de hoy]») or leave the fact out.
- **Short.** One idea per bubble, two bubbles at most per turn; a short question gets a short answer. How bubbles are split belongs to the channel guide, not to the prompt.
- **Not every reply ends in a question.** Ask only when the next step needs a datum. «Gracias», «ok», «lo voy a pensar» get a short close with no question.
- **The customer's name at most once**, in the greeting.
- **No insisting.** Never re-ask the same question, or a reworded one, in the same or the next turn.
- **One truth.** A tone rule lives in one place (the prompt's tone section, or a setting). Skills do not restate it; they only carry examples that obey it.
- **Follow-ups inherit the prompt.** The follow-up and comment→DM composers read the agent's whole prompt as its voice, so a tone change there changes follow-ups too. Say so to the user.

## 4. Verify like any other change

Simulate (or test-bench) the same 6 to 10 real customer openings before and after: a greeting, a fact question («aceptan débito?»), a price question, «lo voy a pensar», «gracias», a visit, an off-hours question on a weekend. Check the facts did not move (hours, prices, rules) as well as the tone. After publishing, re-measure step 2 on the next real conversations.
