'use strict';
const $ = id => document.getElementById(id);
let lastBlock = '', lastText = '';
document.querySelectorAll('nav button').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.panel').forEach(panel => { panel.hidden = panel.id !== button.dataset.panel; });
  document.querySelectorAll('nav button').forEach(item => { const selected = item === button; item.classList.toggle('active', selected); item.setAttribute('aria-pressed', String(selected)); });
  $('status').textContent = '';
}));
async function request(payload, form) {
  const buttons = [...form.querySelectorAll('button')];
  buttons.forEach(b => { b.disabled = true; });
  $('status').className = ''; $('status').textContent = '正在计算…';
  try {
    const response = await fetch('/api', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '运算失败');
    $('status').textContent = '计算完成'; return data;
  } catch (error) {
    $('status').className = 'error'; $('status').textContent = error.message; return null;
  } finally { buttons.forEach(b => { b.disabled = false; }); }
}
$('block-form').addEventListener('submit', async event => {
  event.preventDefault(); const mode = event.submitter?.value || 'encrypt';
  const data = await request({action:mode, block:$('block-input').value, key:$('block-key').value}, event.currentTarget);
  if (!data) return;
  lastBlock = data.output; $('block-output').textContent = data.output;
  $('block-result-label').textContent = mode === 'encrypt' ? '加密结果 / CIPHERTEXT' : '解密结果 / PLAINTEXT';
  $('block-meta').textContent = `HEX ${data.hex} · 输入 ${data.input} · ${mode === 'encrypt' ? 'K1 → K2' : 'K2 → K1'}`;
  $('keys').replaceChildren();
  [['K1',data.K1],['K2',data.K2]].forEach(([name,value]) => { const box = document.createElement('div'); const label = document.createElement('span'); label.textContent = name; box.append(label,document.createTextNode(value)); $('keys').append(box); });
  $('trace').replaceChildren();
  [['IP',data.IP],['第一轮',data.round_one.output],['SW',data.SW],['第二轮',data.round_two.output],['IP⁻¹',data.output]].forEach(([name,value]) => { const box = document.createElement('div'); box.className = 'step'; const label = document.createElement('b'); label.textContent = name; box.append(label,document.createTextNode(value)); $('trace').append(box); });
  $('rounds').textContent = JSON.stringify({round_keys:data.round_keys, round_one:data.round_one, round_two:data.round_two}, null, 2);
});
$('reuse').addEventListener('click', () => { if(lastBlock) $('block-input').value = lastBlock; });
$('text-form').addEventListener('submit', async event => {
  event.preventDefault(); const mode = event.submitter?.value || 'encode';
  const data = await request({action:mode, text:$('text-input').value, key:$('text-key').value, encoding:$('encoding').value},event.currentTarget);
  if(!data) return;
  lastText = mode === 'encode' ? data.hex : data.text;
  $('text-output').textContent = mode === 'encode' ? `HEX  ${data.hex}\n\n二进制  ${data.binary}\n\n转义字节串  ${data.escaped}\n\n字节数  ${data.bytes}` : `还原文本  ${data.text}\n\n明文 HEX  ${data.hex}\n字节数  ${data.bytes}`;
});
$('reuse-text').addEventListener('click', () => { $('text-input').value = lastText; });
$('crack-form').addEventListener('submit', async event => {
  event.preventDefault(); $('progress-fill').style.width = '0';
  const data = await request({action:'crack',pairs:$('pairs').value},event.currentTarget);
  if(!data) return;
  $('progress-fill').style.width = '100%';
  $('search-summary').textContent = `已检查 ${data.checked} / 1024 · ${data.candidates.length} 个候选 · ${data.elapsed_ms.toFixed(3)} ms`;
  $('search-output').textContent = `开始（UTC） ${data.started_utc}\n结束（UTC） ${data.finished_utc}\n\n${data.candidates.length ? data.candidates.join('\n') : '无匹配密钥，请核对已知对。'}`;
  $('timeline').textContent = data.timeline.map(item => `${String(item.checked).padStart(4)} / 1024  ${item.elapsed_ms.toFixed(3)} ms  候选 ${item.candidates.length}`).join('\n');
});
$('collision-form').addEventListener('submit', async event => {
  event.preventDefault(); const data = await request({action:'collisions',block:$('collision-input').value},event.currentTarget); if(!data) return;
  $('collision-summary').replaceChildren();
  [[data.distinct_ciphertexts,'不同密文'],[data.collision_buckets,'碰撞桶'],[data.max_bucket,'最大候选数'],[data.unique_buckets,'单候选桶']].forEach(([value,label]) => { const box = document.createElement('div'); box.className = 'metric'; const strong = document.createElement('strong'); strong.textContent = value; const caption = document.createElement('span'); caption.textContent = label; box.append(strong,caption); $('collision-summary').append(box); });
  $('collision-rows').replaceChildren(); data.collisions.forEach(item => { const row = document.createElement('tr'); [item.cipher,item.count,item.keys.join('  ')].forEach(value => { const cell = document.createElement('td'); cell.textContent = value; row.append(cell); }); $('collision-rows').append(row); });
});
