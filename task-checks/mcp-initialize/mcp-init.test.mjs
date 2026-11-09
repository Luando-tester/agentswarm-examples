import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { existsSync } from 'node:fs';

assert.ok(process.env.BOUNTY_REPO, 'Set BOUNTY_REPO to your agentswarm-mcp branch checkout.');
const repo = resolve(process.env.BOUNTY_REPO);
assert.ok(existsSync(resolve(repo, 'server/index.js')), 'BOUNTY_REPO must contain server/index.js');
// Supported at target 78c88ff1d36b61aaf01a111cb3a6608394a5844e.
const supportedVersions = ['2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25'];
const valid = { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'fixture', version: '1' } };
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
function initialize(params, id = 'init-request-37') {
  const input = [{ jsonrpc: '2.0', id, method: 'initialize', params }, { jsonrpc: '2.0', id: 82, method: 'ping' }].map(JSON.stringify).join('\n') + '\n';
  const child = spawnSync(process.execPath, [resolve(repo, 'server/index.js')], {
    input, encoding: 'utf8', timeout: 5000,
    // Suppress Node runtime warnings (e.g. MODULE_TYPELESS_PACKAGE_JSON), not application errors.
    env: { ...process.env, NODE_NO_WARNINGS: '1', AGENTSWARM_BASE_URL: 'http://127.0.0.1:1', AGENTSWARM_API_KEY: '', AGENTSWARM_HANDLE: '' },
  });
  assert.equal(child.status, 0, child.stderr || String(child.error));
  assert.equal(child.stderr, '', 'Unexpected application diagnostic');
  const replies = child.stdout.trim().split('\n').map(JSON.parse);
  assert.equal(replies.length, 2);
  const reply = replies[0];
  assert.equal(reply.jsonrpc, '2.0');
  assert.equal(reply.id, id, 'Initialize reply must echo the request id');
  assert.deepEqual(replies[1], { jsonrpc: '2.0', id: 82, result: {} }, 'Process must keep serving ping');
  return reply;
}
function success(params, id) {
  const reply = initialize(params, id);
  assert.equal(Object.hasOwn(reply, 'error'), false);
  assert.ok(object(reply.result), 'Initialize result must be an object');
  assert.ok(object(reply.result.capabilities), 'Initialize result.capabilities must be an object');
  assert.ok(object(reply.result.serverInfo), 'Initialize result.serverInfo must be an object');
  assert.equal(typeof reply.result.serverInfo.name, 'string', 'serverInfo.name must be a string');
  assert.equal(typeof reply.result.serverInfo.version, 'string', 'serverInfo.version must be a string');
  return reply.result;
}
function invalid(params, allowedCodes = [-32602]) {
  const reply = initialize(params);
  assert.ok(allowedCodes.includes(reply.error?.code), `expected ${allowedCodes.join(' or ')}; got ${JSON.stringify(reply)}`);
  assert.equal(typeof reply.error?.message, 'string');
  assert.equal(Object.hasOwn(reply, 'result'), false);
}
for (const value of [null, [], 'bad', 42, false]) {
  test(`initialize rejects malformed capabilities ${JSON.stringify(value)}`, () => invalid({ ...valid, capabilities: value }));
}
for (const value of [null, [], 'bad', 42, false, {}, { name: 'fixture' }, { name: 7, version: '1' }, { name: 'fixture', version: null }]) {
  test(`initialize rejects malformed clientInfo ${JSON.stringify(value)}`, () => invalid({ ...valid, clientInfo: value }));
}
for (const value of [null, [], 'str']) {
  test(`initialize rejects malformed params ${JSON.stringify(value)} and keeps serving`, () => invalid(value, [-32600, -32602]));
}
for (const protocolVersion of supportedVersions) {
  test(`initialize negotiates supported version ${protocolVersion}`, () => {
    assert.equal(success({ ...valid, protocolVersion }).protocolVersion, protocolVersion);
  });
}
test('initialize retains valid metadata, omitted metadata and unknown-version fallback', () => {
  for (const params of [valid, { protocolVersion: '2025-06-18' }, { ...valid, protocolVersion: 'unknown' }]) {
    assert.equal(success(params).protocolVersion, '2025-06-18');
  }
});
for (const id of [37, 'string-request-91']) {
  test(`initialize echoes ${JSON.stringify(id)} with the complete response envelope`, () => {
    assert.equal(success(valid, id).protocolVersion, valid.protocolVersion);
  });
}
test('initialize accepts empty clientInfo strings as permitted by the contract', () => {
  assert.equal(success({ ...valid, clientInfo: { name: '', version: '' } }).protocolVersion, valid.protocolVersion);
});
