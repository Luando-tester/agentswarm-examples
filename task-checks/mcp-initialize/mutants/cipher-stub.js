// Deliberately broken, written by us from the defects reported by cipher on The Colony.
import { createInterface } from 'node:readline';
for await (const line of createInterface({ input: process.stdin })) {
  const { id, method, params } = JSON.parse(line);
  if (method === 'ping') { console.log(JSON.stringify({ jsonrpc: '2.0', id, result: {} })); continue; }
  // Deliberately crashes on null and accepts empty clientInfo strings.
  const bad = (value) => value === null || typeof value !== 'object' || Array.isArray(value);
  const invalid = ('capabilities' in params && bad(params.capabilities)) ||
    ('clientInfo' in params && (bad(params.clientInfo) || typeof params.clientInfo.name !== 'string' || typeof params.clientInfo.version !== 'string'));
  const reply = invalid ? { error: { code: -32602, message: 'invalid' } } :
    { result: { protocolVersion: ['2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25'].includes(params.protocolVersion) ? params.protocolVersion : '2025-06-18' } };
  console.log(JSON.stringify({ jsonrpc: '2.0', id: 1, ...reply }));
}
