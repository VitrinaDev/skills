#!/usr/bin/env node
// Call one Vitrina MCP tool from the shell.
//   VITRINA_MCP_URL=https://api.vitrinadev.com/mcp VITRINA_API_KEY=sk_… \
//   node mcp-call.mjs ai_agents_get '{"id":"…"}'
//   node mcp-call.mjs --list            # tool names visible to this key
import { createRequire } from 'node:module';
import { homedir } from 'node:os';
import { join } from 'node:path';

// Resolve the MCP SDK from (1) this script's own folder / NODE_PATH (`npm i -g @modelcontextprotocol/sdk`),
// (2) a vitrina-app checkout named by VITRINA_APP_DIR (default ~/atribu/vitrina/vitrina-app).
function resolveSdk(sub) {
  const candidates = [
    () => createRequire(import.meta.url).resolve(`@modelcontextprotocol/sdk/${sub}`),
    () => createRequire(join(process.env.VITRINA_APP_DIR ?? join(homedir(), 'atribu/vitrina/vitrina-app'), 'package.json')).resolve(`@modelcontextprotocol/sdk/${sub}`),
  ];
  for (const c of candidates) { try { return c(); } catch { /* next */ } }
  console.error('@modelcontextprotocol/sdk not found: `npm i -g @modelcontextprotocol/sdk` or set VITRINA_APP_DIR');
  process.exit(2);
}
const { Client } = await import(resolveSdk('client/index.js'));
const { StreamableHTTPClientTransport } = await import(resolveSdk('client/streamableHttp.js'));

const url = process.env.VITRINA_MCP_URL ?? 'https://api.vitrinadev.com/mcp';
const token = process.env.VITRINA_API_KEY;
if (!token) { console.error('VITRINA_API_KEY is required'); process.exit(2); }
const [tool, rawArgs = '{}'] = process.argv.slice(2);
if (!tool) { console.error('usage: mcp-call.mjs <tool|--list> [json-args]'); process.exit(2); }

const client = new Client({ name: 'mcp-call', version: '0.0.1' });
try {
  await client.connect(new StreamableHTTPClientTransport(new URL(url), {
    requestInit: { headers: { Authorization: `Bearer ${token}` } },
  }));
} catch (e) {
  console.error(`cannot connect to ${url}: ${e.message}`);
  process.exit(1);
}
try {
  if (tool === '--list') {
    const { tools } = await client.listTools();
    console.log(tools.map((t) => t.name).sort().join('\n'));
    console.error(`${tools.length} tools`);
  } else {
    const r = await client.callTool({ name: tool, arguments: JSON.parse(rawArgs) });
    const text = (r.content ?? []).map((c) => c.text ?? '').join('\n');
    if (r.isError) { console.error(text); process.exit(1); }
    console.log(text);
  }
} finally {
  await client.close();
}
