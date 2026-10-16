import assert from 'node:assert/strict';
import test from 'node:test';
import {isTarget,capture} from './ui_playwright_capture.mjs';
test('localhost only, no arbitrary external URLs',()=>{
  assert.equal(isTarget('http://127.0.0.1:4111/test'),false);
  assert.equal(isTarget('http://localhost:4111/test'),false);
  assert.equal(isTarget('data:text/html,%3Chtml%3Eok%3C%2Fhtml%3E'),true);
  assert.throws(()=>isTarget('https://example.com'),/only local HTTP/);
  assert.throws(()=>isTarget('http://192.168.0.1/'),/only local HTTP/);
  assert.throws(()=>isTarget('file:///C:/secret.txt'),/only local HTTP/);
  assert.throws(()=>isTarget('http://user:pass@localhost:5000'),/only local HTTP/);
  assert.throws(()=>isTarget('data:text/html;base64,YWJj'),/bounded HTML fixture/);
});
test('a config outside evidence root is not accepted',async()=>{
  await assert.rejects(capture('C:/Windows/win.ini'),/outside evidence directory/);
});
