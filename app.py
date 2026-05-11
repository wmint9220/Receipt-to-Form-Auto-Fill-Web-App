import os
import base64
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB

submissions = []

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Receipt Scanner</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#f0f4f8;--white:#fff;--border:#e2e8f0;
  --blue:#185FA5;--blue-light:#e6f1fb;--blue-mid:#85B7EB;
  --green:#3B6D11;--green-light:#EAF3DE;--green-mid:#97C459;
  --red:#501313;--red-light:#FCEBEB;--red-mid:#F09595;
  --amber:#633806;--amber-light:#FAEEDA;--amber-mid:#FAC775;
  --text:#1a202c;--muted:#64748b;--hint:#94a3b8;
  --radius:12px;--radius-sm:8px;
}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);min-height:100vh;display:flex;align-items:flex-start;justify-content:center;padding:2rem 1rem;color:var(--text)}
.app{width:100%;max-width:640px}

.header{display:flex;align-items:center;gap:14px;margin-bottom:1.75rem}
.header-icon{width:52px;height:52px;background:var(--blue-light);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:26px}
.header h1{font-size:20px;font-weight:600}
.header p{font-size:13px;color:var(--muted);margin-top:2px}

.apikey-bar{background:var(--amber-light);border:1px solid var(--amber-mid);border-radius:var(--radius);padding:12px 16px;margin-bottom:1.25rem;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.apikey-bar span{font-size:13px;color:var(--amber);flex:1;min-width:160px}
.apikey-bar input{flex:2;min-width:180px;padding:7px 10px;border-radius:var(--radius-sm);border:1px solid var(--amber-mid);font-size:13px;font-family:monospace;background:white}
.apikey-bar input:focus{outline:none;border-color:var(--blue)}
.apikey-bar button{padding:7px 14px;border-radius:var(--radius-sm);background:var(--amber);border:none;color:white;font-size:13px;font-weight:500;cursor:pointer;white-space:nowrap}
.apikey-ok{background:var(--green-light);border-color:var(--green-mid)}
.apikey-ok span{color:var(--green)}

.steps{display:flex;align-items:center;margin-bottom:1.75rem}
.step-item{display:flex;flex-direction:column;align-items:center;gap:4px}
.step-circle{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;border:1.5px solid var(--hint);background:white;color:var(--hint);transition:all 0.3s}
.step-circle.active{background:var(--blue);border-color:var(--blue);color:white}
.step-circle.done{background:var(--green);border-color:var(--green);color:white}
.step-label{font-size:11px;color:var(--hint)}
.step-label.active{color:var(--text);font-weight:500}
.step-line{flex:1;height:1.5px;background:var(--border);margin-bottom:18px;transition:background 0.3s}
.step-line.done{background:var(--green)}

.card{background:var(--white);border-radius:var(--radius);border:1px solid var(--border);padding:1.25rem;margin-bottom:1rem}

.dropzone{border:2px dashed var(--hint);border-radius:var(--radius);padding:2.5rem 1.5rem;text-align:center;cursor:pointer;background:#f8fafc;transition:all 0.2s;user-select:none}
.dropzone:hover,.dropzone.drag-over{border-color:var(--blue);background:var(--blue-light)}
.dropzone.has-image{padding:1rem;border-color:var(--green);border-style:solid}
.dropzone-icon{font-size:36px;margin-bottom:10px}
.dropzone h3{font-size:15px;font-weight:500;margin-bottom:4px}
.dropzone p{font-size:13px;color:var(--muted)}

.btn{display:block;width:100%;padding:11px 16px;border-radius:var(--radius-sm);font-size:14px;font-weight:500;cursor:pointer;transition:all 0.18s;border:none;font-family:inherit}
.btn:hover{opacity:.88}
.btn-primary{background:var(--blue);color:white;margin-top:1rem}
.btn-secondary{background:transparent;color:var(--muted);border:1px solid var(--border);margin-top:.6rem}
.btn-danger{background:var(--red-light);color:var(--red);border:1px solid var(--red-mid);margin-top:.6rem}
.btn:disabled{background:var(--border);color:var(--hint);cursor:not-allowed;opacity:1}
.btn-row{display:flex;gap:10px}
.btn-row .btn{margin-top:0}
.action-row{display:flex;gap:8px;margin-top:.75rem}
.action-row .btn{flex:1;padding:9px 12px;font-size:13px;margin-top:0}

.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.form-group{display:flex;flex-direction:column;gap:6px}
.form-group.full{grid-column:1/-1}
label{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
input,select,textarea{padding:9px 12px;border-radius:var(--radius-sm);border:1px solid var(--border);font-size:14px;color:var(--text);background:white;width:100%;transition:border-color .2s,box-shadow .2s;font-family:inherit}
input:focus,select:focus,textarea:focus{outline:none;border-color:var(--blue);box-shadow:0 0 0 3px rgba(55,138,221,.12)}
.field-changed{border-color:var(--amber-mid)!important;background:var(--amber-light)!important}
.amount-wrap{position:relative}
.amount-prefix{position:absolute;left:10px;top:50%;transform:translateY(-50%);font-size:13px;color:var(--muted);pointer-events:none;font-weight:500}
.amount-wrap input{padding-left:54px}
textarea{resize:vertical;min-height:60px}

.banner{border-radius:var(--radius-sm);padding:10px 14px;font-size:13px;margin-bottom:1rem;display:flex;align-items:flex-start;gap:8px}
.banner-icon{flex-shrink:0;font-size:15px}
.banner-success{background:var(--green-light);border:1px solid var(--green-mid);color:var(--green)}
.banner-error{background:var(--red-light);border:1px solid var(--red-mid);color:var(--red)}
.banner-info{background:var(--blue-light);border:1px solid var(--blue-mid);color:var(--blue)}
.banner-body{flex:1}
.banner-body strong{display:block;margin-bottom:2px}
.banner-detail{font-family:monospace;font-size:12px;background:rgba(0,0,0,.06);padding:4px 8px;border-radius:4px;margin-top:6px;word-break:break-all;white-space:pre-wrap}

.spinner-wrap{text-align:center;padding:2rem}
.spinner{display:inline-block;width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--blue);border-radius:50%;animation:spin .9s linear infinite;margin-bottom:14px}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-steps{margin-top:1.25rem;text-align:left}
.loading-step{display:flex;align-items:center;gap:10px;padding:6px 0;font-size:13px;color:var(--hint);transition:color .3s}
.loading-step.active{color:var(--text)}
.loading-step.done{color:var(--green)}
.step-dot{width:8px;height:8px;border-radius:50%;background:var(--border);flex-shrink:0;transition:background .3s}
.loading-step.active .step-dot{background:var(--blue);animation:pulse .9s ease-in-out infinite}
.loading-step.done .step-dot{background:var(--green)}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.4)}}

.confidence{display:inline-flex;align-items:center;gap:4px;font-size:11px;padding:2px 8px;border-radius:20px;font-weight:600;margin-left:4px}
.conf-high{background:var(--green-light);color:var(--green)}
.conf-med{background:var(--amber-light);color:var(--amber)}
.conf-low{background:var(--red-light);color:var(--red)}

.summary-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:1rem}
.summary-item{background:var(--bg);border-radius:var(--radius-sm);padding:10px 12px}
.summary-label{font-size:11px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px}
.summary-value{font-size:15px;font-weight:600;color:var(--text)}

.log-entry{display:grid;grid-template-columns:1fr auto;gap:4px;padding:12px 14px;border:1px solid var(--border);border-radius:10px;background:white;margin-bottom:8px;transition:border-color .2s}
.log-entry:hover{border-color:var(--blue-mid)}
.log-entry.new{border-color:var(--blue)}
.log-merchant{font-size:14px;font-weight:500}
.log-meta{font-size:12px;color:var(--muted)}
.log-amount{font-size:15px;font-weight:600;text-align:right}
.log-time{font-size:11px;color:var(--hint);text-align:right}
.log-delete{background:none;border:none;color:var(--hint);font-size:16px;cursor:pointer;padding:0 4px;line-height:1;transition:color .2s}
.log-delete:hover{color:var(--red)}
.log-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.section-label{font-size:11px;font-weight:600;color:var(--hint);text-transform:uppercase;letter-spacing:.06em}
.export-btn{font-size:12px;padding:4px 10px;border-radius:var(--radius-sm);background:var(--blue-light);color:var(--blue);border:1px solid var(--blue-mid);cursor:pointer;font-weight:500}
.export-btn:hover{background:var(--blue);color:white}

.toast{position:fixed;bottom:24px;right:24px;background:#1a202c;color:white;padding:10px 18px;border-radius:10px;font-size:13px;font-weight:500;opacity:0;transform:translateY(12px);transition:all .25s;pointer-events:none;z-index:999}
.toast.show{opacity:1;transform:translateY(0)}

#file-input{display:none}
</style>
</head>
<body>
<div class="app">

<div class="header">
  <div class="header-icon">🧾</div>
  <div>
    <h1>Receipt scanner</h1>
    <p>Upload a receipt — Claude AI extracts &amp; auto-fills your form</p>
  </div>
</div>

<!-- API Key bar -->
<div class="apikey-bar" id="apikey-bar">
  <span>🔑 Paste your Anthropic API key to get started</span>
  <input type="password" id="apikey-input" placeholder="sk-ant-api03-..." autocomplete="off"/>
  <button onclick="saveKey()">Save key</button>
</div>

<!-- Steps -->
<div class="steps">
  <div class="step-item"><div class="step-circle active" id="s1">1</div><div class="step-label active" id="sl1">Upload</div></div>
  <div class="step-line" id="line1"></div>
  <div class="step-item"><div class="step-circle" id="s2">2</div><div class="step-label" id="sl2">Extract</div></div>
  <div class="step-line" id="line2"></div>
  <div class="step-item"><div class="step-circle" id="s3">3</div><div class="step-label" id="sl3">Review</div></div>
  <div class="step-line" id="line3"></div>
  <div class="step-item"><div class="step-circle" id="s4">4</div><div class="step-label" id="sl4">Done</div></div>
</div>

<!-- Error banner -->
<div id="error-banner" class="banner banner-error" style="display:none">
  <div class="banner-icon">⚠️</div>
  <div class="banner-body">
    <strong id="error-title">Error</strong>
    <div id="error-detail"></div>
  </div>
</div>

<!-- STAGE 1: Upload -->
<div id="stage-upload">
  <div class="dropzone" id="dropzone" onclick="document.getElementById('file-input').click()">
    <div class="dropzone-icon">📤</div>
    <h3>Drop your receipt here</h3>
    <p>or click to browse · JPG, PNG, WEBP supported</p>
  </div>
  <input type="file" id="file-input" accept="image/*"/>
  <div class="action-row" id="upload-actions" style="display:none">
    <button class="btn btn-secondary" onclick="clearImage()">✕ Remove</button>
    <button class="btn btn-primary" id="extract-btn" onclick="extractData()" style="margin-top:0">✨ Extract receipt data</button>
  </div>
</div>

<!-- STAGE 2: Extracting -->
<div id="stage-extracting" style="display:none">
  <div class="card">
    <div class="spinner-wrap">
      <div id="extract-thumb"></div>
      <div class="spinner"></div>
      <p style="font-size:15px;font-weight:500;margin-bottom:4px">Analyzing your receipt…</p>
      <p style="font-size:13px;color:var(--muted)" id="extract-pct">0%</p>
    </div>
    <div class="loading-steps" id="loading-steps">
      <div class="loading-step" id="ls1"><div class="step-dot"></div>Uploading image to server</div>
      <div class="loading-step" id="ls2"><div class="step-dot"></div>Sending to Claude AI for analysis</div>
      <div class="loading-step" id="ls3"><div class="step-dot"></div>Extracting merchant, date, amount…</div>
      <div class="loading-step" id="ls4"><div class="step-dot"></div>Validating and parsing result</div>
    </div>
  </div>
</div>

<!-- STAGE 3: Review -->
<div id="stage-review" style="display:none">
  <div class="banner banner-success">
    <div class="banner-icon">✅</div>
    <div class="banner-body">
      <strong>Extraction complete</strong>
      Fields highlighted in <span style="background:var(--amber-light);color:var(--amber);padding:1px 5px;border-radius:4px;font-size:11px;font-weight:600">yellow</span> were edited by you. Review before submitting.
    </div>
  </div>
  <div style="display:flex;gap:12px;margin-bottom:1rem;align-items:flex-start">
    <div id="review-thumb" style="flex-shrink:0"></div>
    <div class="card" style="flex:1;margin-bottom:0">
      <div class="form-grid">
        <div class="form-group full">
          <label>Merchant name <span id="conf-merchant"></span></label>
          <input type="text" id="f-merchant" placeholder="e.g. Starbucks" oninput="markChanged(this)"/>
        </div>
        <div class="form-group">
          <label>Date <span id="conf-date"></span></label>
          <input type="date" id="f-date" oninput="markChanged(this)"/>
        </div>
        <div class="form-group">
          <label>Currency</label>
          <select id="f-currency" onchange="updatePrefix()">
            <option>USD</option><option>EUR</option><option>GBP</option>
            <option>MYR</option><option>SGD</option><option>AUD</option>
            <option>CAD</option><option>JPY</option><option>CNY</option>
            <option>HKD</option><option>THB</option><option>IDR</option>
            <option>PHP</option><option>INR</option><option>KRW</option>
          </select>
        </div>
        <div class="form-group full">
          <label>Total amount <span id="conf-total"></span></label>
          <div class="amount-wrap">
            <span class="amount-prefix" id="currency-prefix">USD</span>
            <input type="number" id="f-total" step="0.01" min="0" placeholder="0.00" oninput="markChanged(this)"/>
          </div>
        </div>
        <div class="form-group full">
          <label>Notes</label>
          <textarea id="f-notes" placeholder="Additional details…" oninput="markChanged(this)"></textarea>
        </div>
      </div>
    </div>
  </div>
  <div class="btn-row">
    <button class="btn btn-secondary" onclick="reset()">← Start over</button>
    <button class="btn btn-primary" onclick="submitForm()">Submit expense →</button>
  </div>
</div>

<!-- STAGE 4: Done -->
<div id="stage-submitted" style="display:none">
  <div class="card" style="text-align:center;padding:2rem">
    <div style="font-size:48px;margin-bottom:12px">✅</div>
    <h3 style="font-size:19px;font-weight:600;margin-bottom:6px">Expense submitted!</h3>
    <p style="font-size:13px;color:var(--muted)">Saved to your session log below</p>
  </div>
  <div class="summary-grid" id="last-summary"></div>
  <div class="log-header">
    <div class="section-label" id="log-title">Session log</div>
    <button class="export-btn" onclick="exportCSV()">⬇ Export CSV</button>
  </div>
  <div id="submission-log"></div>
  <div class="action-row">
    <button class="btn btn-secondary" onclick="reset()">+ Scan another receipt</button>
    <button class="btn btn-danger" onclick="clearAll()" style="flex:.6">🗑 Clear all</button>
  </div>
</div>

</div><!-- .app -->
<div class="toast" id="toast"></div>

<script>
let selectedFile = null;
let submissions  = JSON.parse(localStorage.getItem('receipt_subs') || '[]');
let apiKey       = localStorage.getItem('receipt_api_key') || '';
let origValues   = {};

window.addEventListener('DOMContentLoaded', () => {
  if (apiKey) showKeyOk();
  else document.getElementById('apikey-input') && (document.getElementById('apikey-input').value = '');
});

// API Key
function saveKey() {
  const val = document.getElementById('apikey-input').value.trim();
  if (!val.startsWith('sk-')) { toast('Key should start with sk-ant-…', 'warn'); return; }
  apiKey = val;
  localStorage.setItem('receipt_api_key', apiKey);
  showKeyOk(); toast('API key saved!');
}
function showKeyOk() {
  const bar = document.getElementById('apikey-bar');
  bar.className = 'apikey-bar apikey-ok';
  bar.innerHTML = '<span>🔑 API key set — ready to scan receipts</span>' +
    '<button onclick="changeKey()" style="padding:5px 12px;border-radius:8px;background:var(--green);border:none;color:white;font-size:12px;cursor:pointer">Change</button>';
}
function changeKey() {
  const bar = document.getElementById('apikey-bar');
  bar.className = 'apikey-bar';
  bar.innerHTML = '<span>🔑 Enter your Anthropic API key</span>' +
    '<input type="password" id="apikey-input" placeholder="sk-ant-api03-…" value="'+apiKey+'" autocomplete="off"/>' +
    '<button onclick="saveKey()">Save key</button>';
}

// File
const dz = document.getElementById('dropzone');
dz.addEventListener('dragover',  e => { e.preventDefault(); dz.classList.add('drag-over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('drag-over');
  const f = e.dataTransfer.files[0]; if (f) handleFile(f);
});
document.getElementById('file-input').addEventListener('change', e => {
  if (e.target.files[0]) handleFile(e.target.files[0]);
});
function handleFile(file) {
  if (!file.type.startsWith('image/')) { showError('Invalid file','Please upload an image (JPG, PNG, WEBP).'); return; }
  selectedFile = file; clearError();
  const url = URL.createObjectURL(file);
  dz.innerHTML = `<img src="${url}" style="max-height:220px;max-width:100%;border-radius:10px;object-fit:contain"/>
    <p style="margin-top:10px;font-size:13px;color:var(--muted)">📎 ${file.name} · ${(file.size/1024).toFixed(0)} KB — click to change</p>`;
  dz.classList.add('has-image');
  document.getElementById('upload-actions').style.display = 'flex';
}
function clearImage() {
  selectedFile = null;
  document.getElementById('file-input').value = '';
  dz.innerHTML = `<div class="dropzone-icon">📤</div><h3>Drop your receipt here</h3><p>or click to browse</p>`;
  dz.classList.remove('has-image');
  document.getElementById('upload-actions').style.display = 'none';
}

// Steps
function setStep(n) {
  for (let i=1;i<=4;i++) {
    const c=document.getElementById('s'+i), l=document.getElementById('sl'+i);
    c.classList.remove('active','done'); l.classList.remove('active');
    if(i<n){c.classList.add('done');c.textContent='✓';}
    else if(i===n){c.classList.add('active');l.classList.add('active');if(i>1)c.textContent=i;}
    else{c.textContent=i;}
  }
  for(let i=1;i<=3;i++) document.getElementById('line'+i).classList.toggle('done',i<n);
}
function showStage(name) {
  ['upload','extracting','review','submitted'].forEach(s =>
    document.getElementById('stage-'+s).style.display = s===name?'block':'none');
}

// Loading animation
function animateLoading() {
  const steps=[{id:'ls1',pct:'20%',delay:0},{id:'ls2',pct:'50%',delay:700},{id:'ls3',pct:'78%',delay:1600},{id:'ls4',pct:'92%',delay:2500}];
  const pctEl=document.getElementById('extract-pct');
  steps.forEach(({id,pct,delay},idx) => {
    setTimeout(()=>{
      if(idx>0) document.getElementById(steps[idx-1].id).className='loading-step done';
      document.getElementById(id).className='loading-step active';
      pctEl.textContent=pct;
    }, delay);
  });
}

// Extract
async function extractData() {
  if (!selectedFile) return;
  if (!apiKey) { toast('Set your API key first!','warn'); return; }
  clearError(); setStep(2); showStage('extracting');
  const thumbUrl = URL.createObjectURL(selectedFile);
  document.getElementById('extract-thumb').innerHTML =
    `<img src="${thumbUrl}" style="max-height:120px;max-width:100%;border-radius:10px;object-fit:contain;opacity:.6;margin-bottom:1rem"/>`;
  animateLoading();
  try {
    const fd = new FormData();
    fd.append('receipt', selectedFile);
    fd.append('api_key', apiKey);
    const res  = await fetch('/extract', {method:'POST', body:fd});
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); }
    catch(_) {
      const m = text.match(/<title>(.*?)<\/title>/i);
      throw new Error('Server returned HTML instead of JSON.\n' +
        (m ? 'Page title: '+m[1] : 'Check your terminal for the Python traceback.'));
    }
    if (!res.ok) throw new Error(data.error || 'HTTP '+res.status);
    ['ls1','ls2','ls3','ls4'].forEach(id => document.getElementById(id).className='loading-step done');
    document.getElementById('extract-pct').textContent='100%';
    fillForm(data, thumbUrl);
    setStep(3); showStage('review');
  } catch(err) {
    showError('Extraction failed', err.message);
    setStep(1); showStage('upload');
  }
}

// Fill form
function fillForm(data, thumbUrl) {
  ['merchant','date','total','notes'].forEach(f => {
    const el = document.getElementById('f-'+f);
    el.value = data[f] || '';
    el.classList.remove('field-changed');
  });
  origValues = {merchant:data.merchant||'',date:data.date||'',total:data.total||'',notes:data.notes||''};
  const sel = document.getElementById('f-currency');
  const currencies = ['USD','EUR','GBP','MYR','SGD','AUD','CAD','JPY','CNY','HKD','THB','IDR','PHP','INR','KRW'];
  if (data.currency && currencies.includes(data.currency)) sel.value = data.currency;
  updatePrefix();
  setConf('merchant', data.merchant?'high':'low');
  setConf('date',     data.date?'high':'med');
  setConf('total',    data.total?'high':'low');
  document.getElementById('review-thumb').innerHTML =
    `<img src="${thumbUrl}" style="width:90px;height:115px;object-fit:cover;border-radius:10px;border:1px solid var(--border)"/>`;
}
function setConf(field, level) {
  const labels={high:'✓ High',med:'~ Medium',low:'? Low'};
  const cls={high:'conf-high',med:'conf-med',low:'conf-low'};
  document.getElementById('conf-'+field).innerHTML =
    `<span class="confidence ${cls[level]}">${labels[level]}</span>`;
}
function markChanged(el) {
  const key = el.id.replace('f-','');
  if (origValues[key]!==undefined && el.value!==origValues[key]) el.classList.add('field-changed');
  else el.classList.remove('field-changed');
}
function updatePrefix() {
  document.getElementById('currency-prefix').textContent = document.getElementById('f-currency').value;
}

// Submit
async function submitForm() {
  const entry = {
    merchant: document.getElementById('f-merchant').value,
    date:     document.getElementById('f-date').value,
    total:    document.getElementById('f-total').value,
    currency: document.getElementById('f-currency').value,
    notes:    document.getElementById('f-notes').value,
  };
  try {
    const res  = await fetch('/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(entry)});
    const data = await res.json();
    if (!res.ok) throw new Error(data.error||'Submit failed');
    submissions.unshift(data.submission);
    localStorage.setItem('receipt_subs', JSON.stringify(submissions));
    renderSummary(data.submission);
    renderLog();
    setStep(4); showStage('submitted');
    toast('Expense saved!');
  } catch(err) { showError('Submit failed', err.message); }
}

function renderSummary(s) {
  document.getElementById('last-summary').innerHTML = `
    <div class="summary-item"><div class="summary-label">Merchant</div><div class="summary-value">${s.merchant||'—'}</div></div>
    <div class="summary-item"><div class="summary-label">Date</div><div class="summary-value">${s.date||'—'}</div></div>
    <div class="summary-item"><div class="summary-label">Amount</div><div class="summary-value">${s.currency} ${parseFloat(s.total||0).toFixed(2)}</div></div>
    <div class="summary-item"><div class="summary-label">Submitted</div><div class="summary-value" style="font-size:13px">${s.submitted_at}</div></div>`;
}
function renderLog() {
  document.getElementById('log-title').textContent = `Session log (${submissions.length})`;
  document.getElementById('submission-log').innerHTML = submissions.map((s,i)=>`
    <div class="log-entry${i===0?' new':''}">
      <div>
        <div class="log-merchant">${s.merchant||'(No merchant)'}</div>
        <div class="log-meta">${s.date||'No date'}${s.notes?' · '+s.notes.slice(0,50):''}</div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <div>
          <div class="log-amount">${s.currency} ${parseFloat(s.total||0).toFixed(2)}</div>
          <div class="log-time">${s.submitted_at}</div>
        </div>
        <button class="log-delete" onclick="deleteEntry(${i})">✕</button>
      </div>
    </div>`).join('');
}
function deleteEntry(i) {
  submissions.splice(i,1);
  localStorage.setItem('receipt_subs',JSON.stringify(submissions));
  renderLog(); toast('Entry removed');
}
function clearAll() {
  if (!confirm('Clear all submissions?')) return;
  submissions=[];
  localStorage.removeItem('receipt_subs');
  renderLog(); toast('All cleared');
}
function exportCSV() {
  if (!submissions.length) { toast('No data to export'); return; }
  const header='Merchant,Date,Total,Currency,Notes,Submitted At';
  const rows=submissions.map(s=>
    [s.merchant,s.date,s.total,s.currency,s.notes,s.submitted_at]
      .map(v=>`"${(v||'').replace(/"/g,'""')}"`)
      .join(','));
  const csv=[header,...rows].join('\\n');
  const blob=new Blob([csv],{type:'text/csv'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='receipts_'+new Date().toISOString().slice(0,10)+'.csv';
  a.click(); toast('CSV exported!');
}

// Reset
function reset() {
  selectedFile=null; origValues={};
  document.getElementById('file-input').value='';
  dz.innerHTML=`<div class="dropzone-icon">📤</div><h3>Drop your receipt here</h3><p>or click to browse · JPG, PNG, WEBP supported</p>`;
  dz.classList.remove('has-image');
  document.getElementById('upload-actions').style.display='none';
  ['ls1','ls2','ls3','ls4'].forEach(id=>document.getElementById(id).className='loading-step');
  clearError(); setStep(1); showStage('upload');
}

// Error / Toast
function showError(title, detail) {
  document.getElementById('error-title').textContent = title;
  const detEl = document.getElementById('error-detail');
  detEl.innerHTML = detail ? `<div class="banner-detail">${detail.replace(/</g,'&lt;')}</div>` : '';
  const banner = document.getElementById('error-banner');
  banner.style.display='flex';
  banner.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function clearError() { document.getElementById('error-banner').style.display='none'; }

let toastTimer;
function toast(msg, type='ok') {
  const el=document.getElementById('toast');
  el.textContent=msg;
  el.style.background=type==='warn'?'#B45309':'#1a202c';
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>el.classList.remove('show'),2400);
}
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/extract", methods=["POST"])
def extract():
    """Always returns JSON — never an HTML error page."""
    try:
        import anthropic

        # API key: prefer from form, fall back to env
        api_key = (request.form.get("api_key") or "").strip()
        if not api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return jsonify({"error": "No API key. Paste your Anthropic key in the field above."}), 400

        if "receipt" not in request.files:
            return jsonify({"error": "No file uploaded."}), 400

        file = request.files["receipt"]
        if not file or not file.content_type.startswith("image/"):
            return jsonify({"error": f"Expected an image, got: {file.content_type}"}), 400

        raw_bytes = file.read()
        if not raw_bytes:
            return jsonify({"error": "Uploaded file is empty."}), 400

        image_data = base64.standard_b64encode(raw_bytes).decode("utf-8")
        media_type = file.content_type

        client = anthropic.Anthropic(api_key=api_key)

        system_prompt = (
            "You are a receipt data extractor. Return ONLY a raw JSON object — "
            "no markdown, no backticks, no explanation. "
            'Schema: {"merchant":"<string>","date":"<YYYY-MM-DD or empty>",'
            '"total":"<digits only e.g. 12.50>","currency":"<ISO-4217 e.g. USD MYR>",'
            '"notes":"<extra info or empty>"}. '
            "Use empty string for unknown fields."
        )

        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text",  "text": "Extract receipt data. Return only the JSON object."},
                ],
            }],
        )

        raw = message.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return jsonify({"error": f"Claude returned non-JSON: {raw[:200]}"}), 500

        return jsonify(parsed)

    except Exception as exc:
        msg = str(exc)
        # Translate common errors into friendly messages
        if "authentication" in msg.lower() or "invalid x-api-key" in msg.lower() or "401" in msg:
            friendly = "Invalid API key. Check your key at console.anthropic.com."
        elif "rate" in msg.lower() or "429" in msg:
            friendly = "Rate limit hit. Wait a moment and try again."
        elif "credit" in msg.lower() or "billing" in msg.lower():
            friendly = "No Anthropic credits. Check billing at console.anthropic.com."
        elif "permission" in msg.lower() or "403" in msg:
            friendly = "Your API key doesn't have permission to use this model."
        else:
            friendly = f"{type(exc).__name__}: {msg}"
        return jsonify({"error": friendly}), 500


@app.route("/submit", methods=["POST"])
def submit():
    try:
        data  = request.get_json(force=True)
        entry = {
            "merchant":     data.get("merchant", ""),
            "date":         data.get("date", ""),
            "total":        data.get("total", ""),
            "currency":     data.get("currency", "USD"),
            "notes":        data.get("notes", ""),
            "submitted_at": datetime.now().strftime("%b %d, %Y %I:%M %p"),
        }
        submissions.append(entry)
        return jsonify({"success": True, "submission": entry, "total": len(submissions)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/submissions", methods=["GET"])
def get_submissions():
    return jsonify(submissions)


if __name__ == "__main__":
    key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
    print("=" * 55)
    print("  🧾  Receipt Scanner — Flask App")
    print("=" * 55)
    if key_set:
        print("  ✅  ANTHROPIC_API_KEY found in environment")
    else:
        print("  ℹ️   No ANTHROPIC_API_KEY env var — paste key in the UI")
    print("  🌐  Open: http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, port=5000)
