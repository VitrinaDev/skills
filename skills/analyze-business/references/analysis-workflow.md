# Corpus-analysis workflow template (26-ish extractors + 3 synthesizers)

Adapt this Workflow script per business. Replace `{{BIZ}}` (name + one-line context: rubro, ciudad, sistema de agenda/ERP), `{{DIR}}` (the `<slug>-agent` folder), `{{N}}` (batch count from build_batches.py), and the domain-specific field hints (the example below is the clinic version — for an automotora swap motivo_consulta/profesional for vehículo/presupuesto, etc.).

Scale: one **sonnet** extractor per batch (`effort: 'medium'`), three **opus** synthesizers. ~1,700 conversations ≈ 26 batches ≈ 6M subagent tokens ≈ 30 min. Extractors WRITE their JSON to disk (so the CSV merge and any re-synthesis read files, not workflow memory) and return only a tiny summary.

```js
export const meta = {
  name: '{{slug}}-conversation-analysis',
  description: 'Analyze {{BIZ}} conversations: tone, flows, FAQ, templates, contact data',
  phases: [
    { title: 'Extract', detail: 'one sonnet agent per transcript batch' },
    { title: 'Synthesize', detail: '3 opus agents: tone / flows / knowledge+templates' },
  ],
}

const BATCHES = Array.from({length: {{N}}}, (_, i) => `batch-${String(i + 1).padStart(2, '0')}`)
const DIR = '{{DIR}}'

const TINY = {
  type: 'object',
  required: ['file', 'conversations_analyzed', 'notable'],
  properties: {
    file: { type: 'string' },
    conversations_analyzed: { type: 'number' },
    notable: { type: 'array', items: { type: 'string' }, maxItems: 5 },
  },
  additionalProperties: false,
}
const SYNTH = {
  type: 'object',
  required: ['file', 'summary'],
  properties: {
    file: { type: 'string' }, summary: { type: 'string' },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
  additionalProperties: false,
}

phase('Extract')
const extractPrompt = (b) => `Eres un analista construyendo un agente de IA de WhatsApp para {{BIZ}}. Analizarás conversaciones REALES entre el equipo humano (rol "{{LABEL}}") y clientes (rol "CLIENTE"). El agente deberá imitar el tono y los procedimientos del equipo.

Lee COMPLETO ${DIR}/export/batches/${b}.txt (bloques por conversación; [image]/[file] = multimedia; mensajes largos truncados a 4000 chars).

Escribe EXACTAMENTE UN archivo: ${DIR}/analysis/${b}.json — JSON válido UTF-8 con esta estructura exacta:

{
  "batch": "${b}",
  "conversations_analyzed": <int>,
  "tone": {"greetings": [<=8 VERBATIM], "closings": [<=8], "emojis": [<con contexto>],
           "treatment": "<tú|usted|mixto + evidencia>", "phrases": [<=15 VERBATIM],
           "style_notes": [<=8: largo, formato, puntuación, muletillas>]},
  "flows": [{"name": "...", "steps": [...], "verbatim_example": "...", "frequency": "alta|media|baja"}],
  "edge_cases": [{"case": "...", "how_handled": "...", "verbatim": "..."}],
  "faq": [{"q": "...", "a": "<VERBATIM si es texto estándar>"}],
  "templates": [{"purpose": "...", "text": "<VERBATIM completo>"}],
  "business_facts": [<precios, direcciones, horarios, políticas, formas de pago>],
  "professionals": [{"name": "...", "specialty": "...", "notes": "<horarios, demanda>"}],
  "contacts": [{"conversation": "<id 8 chars>", "name": "", "phone": "",
    "nombre_completo": "", "rut": "", "email": "", "fecha_nacimiento": "", "direccion": "",
    "comuna": "", "isapre_convenio": "", "motivo_consulta": "", "profesional": "",
    "servicio": "", "flags": "<no contactar, deudor, staff/interno, menor, frecuente...>"}],
  "red_flags": [<lo que el bot NO debe replicar: errores, quejas, datos mal manejados>]
}

Reglas: contacts solo con al menos un dato extraído más allá de nombre/teléfono, pero exhaustivo. VERBATIM = copiar texto real. Deduplica dentro del lote; no inventes nada.

Devuelve (StructuredOutput): file, conversations_analyzed, notable (<=5 hallazgos).`

const extracts = await parallel(BATCHES.map((b) => () =>
  agent(extractPrompt(b), { label: `extract:${b}`, phase: 'Extract', model: 'sonnet', effort: 'medium', schema: TINY })))
log(`Extracción: ${extracts.filter(Boolean).length}/${BATCHES.length} lotes OK`)

phase('Synthesize')
const common = `Insumo: lee TODOS los ${DIR}/analysis/batch-*.json (análisis de las conversaciones reales de {{BIZ}} — "{{LABEL}}" = equipo humano cuyo estilo debe imitar el agente). {{CONTEXTO_ENTREVISTA: qué pidió el dueño en el onboarding — las conversaciones reales mandan sobre lo declarado}}. Escribe la salida en español, markdown impecable, citas verbatim como evidencia. Síntesis de consultor senior, no listado; deduplica; cuantifica frecuencia; marca contradicciones. Cuando puedas, RE-VERIFICA los números con grep sobre ${DIR}/export/messages.jsonl (el corpus crudo) en vez de confiar solo en los lotes.`

const synths = await parallel([
  () => agent(`${common}\n\nProduce ${DIR}/analysis/TONO-Y-ESTILO.md: 1) veredicto tú/usted cuantificado; 2) biblioteca de saludos/cierres verbatim; 3) uso real de emojis; 4) frases características y muletillas a evitar; 5) largo/formato de mensajes; 6) cómo suenan al confirmar, cobrar, rechazar, dar malas noticias, ante reclamos; 7) 10-20 reglas de estilo accionables para el system prompt.\n\nDevuelve file + summary + open_questions.`,
    { label: 'synth:tono', phase: 'Synthesize', model: 'opus', schema: SYNTH }),
  () => agent(`${common}\n\nProduce ${DIR}/analysis/FLUJOS-Y-CASOS.md: 1) flujos principales con pasos numerados tal como los ejecuta el equipo + variantes + verbatim; 2) edge cases con manejo real; 3) qué escala a quién (futuros triggers de handoff); 4) qué automatizar vs qué queda en humanos (frecuencia x riesgo); 5) red flags consolidados.\n\nDevuelve file + summary + open_questions.`,
    { label: 'synth:flujos', phase: 'Synthesize', model: 'opus', schema: SYNTH }),
  () => agent(`${common}\n\nProduce ${DIR}/analysis/CONOCIMIENTO-Y-TEMPLATES.md: 1) FAQ consolidada por tema; 2) datos duros contrastados entre lotes CON FECHAS (precios cambian — marca vigencias y contradicciones); 3) directorio de personas/recursos; 4) biblioteca de templates verbatim (el más completo/reciente de cada uno); 5) qué va a la Knowledge Base vs al system prompt.\n\nDevuelve file + summary + open_questions.`,
    { label: 'synth:conocimiento', phase: 'Synthesize', model: 'opus', schema: SYNTH }),
])

return {
  extracted_batches: extracts.filter(Boolean).length,
  extract_notables: extracts.filter(Boolean).flatMap((e) => e.notable).slice(0, 40),
  syntheses: synths.filter(Boolean).map((s) => ({ file: s.file, summary: s.summary, open_questions: s.open_questions || [] })),
}
```

Gotchas that cost time last run:
- Pass the batch list as a literal in the script (a Workflow `args` object failed to reach the script once); no `Date.now()` in workflow scripts.
- Some model responses put JSON in `reasoning` with null `content` — synthesis agents reading batch JSONs is why extractors write files (retryable, inspectable).
- Expect **staff/internal chats mislabeled as customers** in coexistence imports — the extract prompt's `flags` field catches them; they poison tone if not excluded.
