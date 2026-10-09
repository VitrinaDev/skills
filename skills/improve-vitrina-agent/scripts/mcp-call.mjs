#!/usr/bin/env node
// Call one Vitrina MCP tool from the shell.
//   VITRINA_MCP_URL=https://api.vitrinadev.com/mcp VITRINA_API_KEY=sk_… \
//   node mcp-call.mjs ai_agents_get '{"id":"…"}'
//   node mcp-call.mjs --list            # tool names visible to this key
import { execSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';

// Resolve the MCP SDK from a normal install, in order: next to this script or on NODE_PATH
// (`npm i @modelcontextprotocol/sdk` here), then the global modules of the running node
// (`npm i -g @modelcontextprotocol/sdk`, nvm included), then `npm root -g` (a custom npm prefix).
function globalRoots() {
  const prefix = dirname(dirname(process.execPath));
  const roots = [join(prefix, 'lib', 'node_modules'), join(dirname(process.execPath), 'node_modules')];
  try {
    roots.push(execSync('npm root -g', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim());
  } catch { /* npm not on PATH */ }
  return roots;
}
function resolveSdk(sub) {
  const spec = `@modelcontextprotocol/sdk/${sub}`;
  try { return createRequire(import.meta.url).resolve(spec); } catch { /* next */ }
  for (const root of globalRoots()) {
    try { return createRequire(join(root, 'noop.js')).resolve(spec); } catch { /* next */ }
  }
  console.error('@modelcontextprotocol/sdk not found: run `npm i -g @modelcontextprotocol/sdk` once, then retry');
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
