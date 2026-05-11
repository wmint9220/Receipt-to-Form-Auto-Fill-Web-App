import os
import base64
import json
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max upload

# In-memory submissions store
submissions = []

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Receipt Scanner</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #f0f4f8;
      min-height: 100vh;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding: 2rem 1rem;
      color: #1a202c;
    }
    .app {
      width: 100%;
      max-width: 600px;
    }
    .header {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 1.75rem;
    }
    .header-icon {
      width: 52px; height: 52px;
      background: #e6f1fb;
      border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      font-size: 26px;
    }
    .header h1 { font-size: 20px; font-weight: 600; }
    .header p  { font-size: 13px; color: #64748b; margin-top: 2px; }

    /* Steps */
    .steps {
      display: flex;
      align-items: center;
      margin-bottom: 1.75rem;
    }
    .step-item { display: flex; flex-direction: column; align-items: center; gap: 4px; }
    .step-circle {
      width: 28px; height: 28px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 600;
      border: 1.5px solid #cbd5e1;
      background: white; color: #94a3b8;
      transition: all 0.3s;
    }
    .step-circle.active  { background: #185FA5; border-color: #185FA5; color: white; }
    .step-circle.done    { background: #3B6D11; border-color: #3B6D11; color: white; }
    .step-label { font-size: 11px; color: #94a3b8; }
    .step-label.active { color: #1a202c; font-weight: 500; }
    .step-line { flex: 1; height: 1.5px; background: #e2e8f0; margin-bottom: 18px; transition: background 0.3s; }
    .step-line.done { background: #3B6D11; }

    /* Cards */
    .card {
      background: white;
      border-radius: 16px;
      border: 1px solid #e2e8f0;
      padding: 1.25rem;
      margin-bottom: 1rem;
    }

    /* Upload zone */
    .dropzone {
      border: 2px dashed #cbd5e1;
      border-radius: 12px;
      padding: 2.5rem 1.5rem;
      text-align: center;
      cursor: pointer;
      background: #f8fafc;
      transition: all 0.2s;
    }
    .dropzone:hover, .dropzone.drag-over { border-color: #378ADD; background: #e6f1fb; }
    .dropzone.has-image { padding: 1rem; border-color: #3B6D11; }
    .dropzone-icon { font-size: 36px; margin-bottom: 10px; }
    .dropzone h3 { font-size: 15px; font-weight: 500; margin-bottom: 4px; }
    .dropzone p  { font-size: 13px; color: #64748b; }
    #preview-img { max-height: 260px; max-width: 100%; border-radius: 10px; object-fit: contain; }

    /* Buttons */
    .btn {
      display: block; width: 100%;
      padding: 12px; border-radius: 10px;
      font-size: 14px; font-weight: 500;
      cursor: pointer; transition: opacity 0.2s;
      border: none;
    }
    .btn:hover { opacity: 0.88; }
    .btn-primary { background: #185FA5; color: white; margin-top: 1rem; }
    .btn-secondary {
      background: transparent; color: #64748b;
      border: 1px solid #e2e8f0; margin-top: 0.6rem;
    }
    .btn:disabled { background: #e2e8f0; color: #94a3b8; cursor: not-allowed; opacity: 1; }

    /* Form */
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .form-group { display: flex; flex-direction: column; gap: 6px; }
    .form-group.full { grid-column: 1 / -1; }
    label { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; }
    input, select, textarea {
      padding: 9px 12px; border-radius: 8px;
      border: 1px solid #e2e8f0;
      font-size: 14px; color: #1a202c;
      background: white; width: 100%;
      transition: border-color 0.2s;
      font-family: inherit;
    }
    input:focus, select:focus, textarea:focus {
      outline: none; border-color: #378ADD;
      box-shadow: 0 0 0 3px rgba(55,138,221,0.12);
    }
    .amount-wrap { position: relative; }
    .amount-prefix {
      position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
      font-size: 13px; color: #64748b; pointer-events: none;
    }
    .amount-wrap input { padding-left: 52px; }
    textarea { resize: vertical; min-height: 60px; }

    /* Status banners */
    .banner {
      border-radius: 10px; padding: 10px 14px;
      font-size: 13px; margin-bottom: 1rem;
    }
    .banner-success { background: #EAF3DE; border: 1px solid #97C459; color: #27500A; }
    .banner-error   { background: #FCEBEB; border: 1px solid #F09595; color: #501313; }
    .banner-info    { background: #E6F1FB; border: 1px solid #85B7EB; color: #042C53; }

    /* Spinner */
    .spinner-wrap { text-align: center; padding: 2rem; }
    .spinner {
      display: inline-block; width: 28px; height: 28px;
      border: 3px solid #e2e8f0; border-top-color: #185FA5;
      border-radius: 50%; animation: spin 0.9s linear infinite;
      margin-bottom: 12px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Submission log */
    .log-entry {
      display: grid; grid-template-columns: 1fr auto;
      gap: 4px; padding: 12px 14px;
      border: 1px solid #e2e8f0; border-radius: 10px;
      background: white; margin-bottom: 8px;
    }
    .log-merchant { font-size: 14px; font-weight: 500; }
    .log-meta     { font-size: 12px; color: #64748b; }
    .log-amount   { font-size: 15px; font-weight: 600; text-align: right; }
    .log-time     { font-size: 11px; color: #94a3b8; text-align: right; }

    .section-label {
      font-size: 11px; font-weight: 600; color: #94a3b8;
      text-transform: uppercase; letter-spacing: 0.06em;
      margin-bottom: 10px;
    }

    #file-input { display: none; }
  </style>
</head>
<body>
<div class="app">

  <!-- Header -->
  <div class="header">
    <div class="header-icon">🧾</div>
    <div>
      <h1>Receipt scanner</h1>
      <p>Upload a receipt to auto-fill expense fields</p>
    </div>
  </div>

  <!-- Steps -->
  <div class="steps" id="steps">
    <div class="step-item">
      <div class="step-circle active" id="s1">1</div>
      <div class="step-label active" id="sl1">Upload</div>
    </div>
    <div class="step-line" id="line1"></div>
    <div class="step-item">
      <div class="step-circle" id="s2">2</div>
      <div class="step-label" id="sl2">Extract</div>
    </div>
    <div class="step-line" id="line2"></div>
    <div class="step-item">
      <div class="step-circle" id="s3">3</div>
      <div class="step-label" id="sl3">Review</div>
    </div>
    <div class="step-line" id="line3"></div>
    <div class="step-item">
      <div class="step-circle" id="s4">4</div>
      <div class="step-label" id="sl4">Done</div>
    </div>
  </div>

  <!-- Error banner -->
  <div id="error-banner" class="banner banner-error" style="display:none"></div>

  <!-- STAGE 1: Upload -->
  <div id="stage-upload">
    <div class="dropzone" id="dropzone" onclick="document.getElementById('file-input').click()">
      <div class="dropzone-icon">📤</div>
      <h3>Drop your receipt here</h3>
      <p>or click to browse · JPG, PNG, WEBP supported</p>
    </div>
    <input type="file" id="file-input" accept="image/*"/>
    <button class="btn btn-primary" id="extract-btn" disabled onclick="extractData()">Extract receipt data →</button>
  </div>

  <!-- STAGE 2: Extracting -->
  <div id="stage-extracting" style="display:none">
    <div class="card spinner-wrap">
      <div id="preview-thumb" style="margin-bottom:1.25rem"></div>
      <div class="spinner"></div>
      <p id="extract-log" style="font-size:14px;color:#64748b">Sending receipt to Claude AI...</p>
    </div>
  </div>

  <!-- STAGE 3: Review -->
  <div id="stage-review" style="display:none">
    <div class="banner banner-success" style="display:flex;align-items:center;gap:8px">
      <span>✅</span>
      <span><strong>Extraction complete.</strong> Review and edit the fields below before submitting.</span>
    </div>

    <div style="display:flex;gap:12px;margin-bottom:1rem;align-items:flex-start">
      <div id="review-thumb"></div>
      <div class="card" style="flex:1;margin-bottom:0">
        <div class="form-grid">
          <div class="form-group full">
            <label>Merchant name</label>
            <input type="text" id="f-merchant" placeholder="e.g. Starbucks"/>
          </div>
          <div class="form-group">
            <label>Date</label>
            <input type="date" id="f-date"/>
          </div>
          <div class="form-group">
            <label>Currency</label>
            <select id="f-currency">
              <option>USD</option><option>EUR</option><option>GBP</option>
              <option>MYR</option><option>SGD</option><option>AUD</option>
              <option>CAD</option><option>JPY</option><option>CNY</option>
              <option>HKD</option><option>THB</option><option>IDR</option>
              <option>PHP</option><option>INR</option><option>KRW</option>
            </select>
          </div>
          <div class="form-group full">
            <label>Total amount</label>
            <div class="amount-wrap">
              <span class="amount-prefix" id="currency-prefix">USD</span>
              <input type="number" id="f-total" step="0.01" min="0" placeholder="0.00"/>
            </div>
          </div>
          <div class="form-group full">
            <label>Notes</label>
            <textarea id="f-notes" placeholder="Additional details..."></textarea>
          </div>
        </div>
      </div>
    </div>

    <div style="display:flex;gap:10px">
      <button class="btn btn-secondary" style="flex:1" onclick="reset()">← Start over</button>
      <button class="btn btn-primary" style="flex:2;margin-top:0" onclick="submitForm()">Submit expense →</button>
    </div>
  </div>

  <!-- STAGE 4: Submitted -->
  <div id="stage-submitted" style="display:none">
    <div class="card" style="text-align:center;padding:2rem">
      <div style="font-size:44px;margin-bottom:10px">✅</div>
      <h3 style="font-size:18px;font-weight:600;margin-bottom:6px">Expense submitted!</h3>
      <p style="font-size:13px;color:#64748b">Saved to your session log below</p>
    </div>
    <div class="section-label" id="log-title"></div>
    <div id="submission-log"></div>
    <button class="btn btn-secondary" onclick="reset()">+ Scan another receipt</button>
  </div>

</div>

<script>
let selectedFile = null;
const submissions = [];

// --- Drag & drop ---
const dz = document.getElementById('dropzone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) handleFile(f);
});
document.getElementById('file-input').addEventListener('change', e => {
  if (e.target.files[0]) handleFile(e.target.files[0]);
});

function handleFile(file) {
  if (!file.type.startsWith('image/')) { showError('Please upload an image file.'); return; }
  selectedFile = file;
  clearError();
  const url = URL.createObjectURL(file);
  dz.innerHTML = `<img src="${url}" style="max-height:240px;max-width:100%;border-radius:10px;object-fit:contain;"/><p style="margin-top:10px;font-size:13px;color:#64748b">Click to change image</p>`;
  dz.classList.add('has-image');
  document.getElementById('extract-btn').disabled = false;
}

// --- Steps ---
function setStep(n) {
  for (let i = 1; i <= 4; i++) {
    const c = document.getElementById('s'+i);
    const l = document.getElementById('sl'+i);
    c.classList.remove('active','done');
    l.classList.remove('active');
    if (i < n) { c.classList.add('done'); c.textContent = '✓'; }
    else if (i === n) { c.classList.add('active'); l.classList.add('active'); if(i>1) c.textContent=i; }
    else { c.textContent = i; }
  }
  for (let i = 1; i <= 3; i++) {
    const line = document.getElementById('line'+i);
    line.classList.toggle('done', i < n);
  }
}

function showStage(name) {
  ['upload','extracting','review','submitted'].forEach(s => {
    document.getElementById('stage-'+s).style.display = s===name ? 'block' : 'none';
  });
}

// --- Extract ---
async function extractData() {
  if (!selectedFile) return;
  clearError();
  setStep(2); showStage('extracting');

  // Show thumbnail in extracting stage
  const thumbUrl = URL.createObjectURL(selectedFile);
  document.getElementById('preview-thumb').innerHTML =
    `<img src="${thumbUrl}" style="max-height:150px;max-width:100%;border-radius:10px;object-fit:contain;opacity:0.7"/>`;

  const msgs = [
    'Sending receipt to Claude AI...',
    'Analyzing receipt contents...',
    'Parsing extracted data...'
  ];
  let mi = 0;
  const logEl = document.getElementById('extract-log');
  const interval = setInterval(() => { mi = (mi+1)%msgs.length; logEl.textContent = msgs[mi]; }, 1400);

  try {
    const formData = new FormData();
    formData.append('receipt', selectedFile);

    const res = await fetch('/extract', { method: 'POST', body: formData });
    const data = await res.json();
    clearInterval(interval);

    if (!res.ok) throw new Error(data.error || 'Extraction failed');

    // Fill form
    document.getElementById('f-merchant').value = data.merchant || '';
    document.getElementById('f-date').value     = data.date     || '';
    document.getElementById('f-total').value    = data.total    || '';
    document.getElementById('f-notes').value    = data.notes    || '';
    const sel = document.getElementById('f-currency');
    if (data.currency) {
      for (let opt of sel.options) if (opt.value === data.currency) { sel.value = data.currency; break; }
    }
    document.getElementById('currency-prefix').textContent = sel.value;
    sel.addEventListener('change', () => {
      document.getElementById('currency-prefix').textContent = sel.value;
    });

    // Thumbnail in review
    document.getElementById('review-thumb').innerHTML =
      `<img src="${thumbUrl}" style="width:100px;height:130px;object-fit:cover;border-radius:10px;border:1px solid #e2e8f0;flex-shrink:0"/>`;

    setStep(3); showStage('review');

  } catch(err) {
    clearInterval(interval);
    showError(err.message);
    setStep(1); showStage('upload');
  }
}

// --- Submit ---
async function submitForm() {
  const entry = {
    merchant: document.getElementById('f-merchant').value,
    date:     document.getElementById('f-date').value,
    total:    document.getElementById('f-total').value,
    currency: document.getElementById('f-currency').value,
    notes:    document.getElementById('f-notes').value,
  };

  const res = await fetch('/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry)
  });
  const data = await res.json();

  submissions.unshift(data.submission);
  renderLog();
  setStep(4); showStage('submitted');
}

function renderLog() {
  document.getElementById('log-title').textContent = `Session submissions (${submissions.length})`;
  document.getElementById('submission-log').innerHTML = submissions.map((s,i) => `
    <div class="log-entry" style="${i===0?'border-color:#378ADD':''}">
      <div>
        <div class="log-merchant">${s.merchant||'(No merchant)'}</div>
        <div class="log-meta">${s.date||'No date'}${s.notes?' · '+s.notes.slice(0,40):''}</div>
      </div>
      <div>
        <div class="log-amount">${s.currency} ${parseFloat(s.total||0).toFixed(2)}</div>
        <div class="log-time">${s.submitted_at}</div>
      </div>
    </div>
  `).join('');
}

// --- Reset ---
function reset() {
  selectedFile = null;
  document.getElementById('file-input').value = '';
  dz.innerHTML = `<div class="dropzone-icon">📤</div>
    <h3>Drop your receipt here</h3>
    <p>or click to browse · JPG, PNG, WEBP supported</p>`;
  dz.classList.remove('has-image');
  document.getElementById('extract-btn').disabled = true;
  clearError();
  setStep(1); showStage('upload');
}

function showError(msg) {
  const el = document.getElementById('error-banner');
  el.textContent = '⚠️ ' + msg;
  el.style.display = 'block';
}
function clearError() {
  document.getElementById('error-banner').style.display = 'none';
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
    import anthropic

    if "receipt" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["receipt"]
    if not file.content_type.startswith("image/"):
        return jsonify({"error": "File must be an image"}), 400

    image_data = base64.standard_b64encode(file.read()).decode("utf-8")
    media_type = file.content_type

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    system_prompt = (
        "You are a receipt data extractor. Given a receipt image, extract the following fields "
        "and return ONLY a JSON object with no preamble, no markdown backticks, no explanation. "
        'Return exactly this structure: {"merchant":"<name>","date":"<YYYY-MM-DD or empty>",'
        '"total":"<numeric string only, no currency symbol>","currency":"<ISO 4217 code like USD, EUR, MYR, etc>",'
        '"notes":"<any other relevant info, or empty string>"}. '
        "If a field cannot be determined, use an empty string. "
        "Currency should be ISO 4217 code based on symbols or context clues."
    )

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract the receipt information and return only the JSON object.",
                    },
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(raw)
    return jsonify(parsed)


@app.route("/submit", methods=["POST"])
def submit():
    from datetime import datetime

    data = request.get_json()
    entry = {
        "merchant":     data.get("merchant", ""),
        "date":         data.get("date", ""),
        "total":        data.get("total", ""),
        "currency":     data.get("currency", "USD"),
        "notes":        data.get("notes", ""),
        "submitted_at": datetime.now().strftime("%b %d, %Y %I:%M %p"),
    }
    submissions.append(entry)
    return jsonify({"success": True, "submission": entry, "total_count": len(submissions)})


@app.route("/submissions", methods=["GET"])
def get_submissions():
    return jsonify(submissions)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: ANTHROPIC_API_KEY not set. Set it before running.")
    app.run(debug=True, port=5000)
