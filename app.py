import os
import base64
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB

submissions = []

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>AI Receipt Auto-Fill</title>

<style>
*,*::before,*::after{
  box-sizing:border-box;
  margin:0;
  padding:0;
}

:root{
  --bg:#f3f6fb;
  --card:#ffffff;
  --border:#dbe4f0;
  --primary:#2563eb;
  --primary-light:#e8f0ff;
  --text:#1e293b;
  --muted:#64748b;
  --success:#16a34a;
  --danger:#dc2626;
  --radius:14px;
}

body{
  font-family:Segoe UI, sans-serif;
  background:var(--bg);
  color:var(--text);
  min-height:100vh;
  display:flex;
  justify-content:center;
  padding:2rem 1rem;
}

.container{
  width:100%;
  max-width:700px;
}

.header{
  margin-bottom:1.5rem;
}

.header h1{
  font-size:28px;
  margin-bottom:6px;
}

.header p{
  color:var(--muted);
  font-size:14px;
}

.card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:var(--radius);
  padding:1.5rem;
  margin-bottom:1rem;
}

.dropzone{
  border:2px dashed #94a3b8;
  border-radius:var(--radius);
  padding:2rem;
  text-align:center;
  cursor:pointer;
  transition:0.2s;
  background:#fafcff;
}

.dropzone:hover{
  border-color:var(--primary);
  background:var(--primary-light);
}

.dropzone img{
  max-width:100%;
  max-height:250px;
  border-radius:10px;
}

.dropzone h3{
  margin-top:12px;
  margin-bottom:5px;
}

.dropzone p{
  color:var(--muted);
  font-size:13px;
}

#file-input{
  display:none;
}

.btn{
  width:100%;
  border:none;
  border-radius:10px;
  padding:12px;
  font-size:14px;
  font-weight:600;
  cursor:pointer;
  transition:0.2s;
}

.btn-primary{
  background:var(--primary);
  color:white;
}

.btn-primary:hover{
  opacity:0.9;
}

.btn-secondary{
  background:#eef2f7;
  color:var(--text);
}

.actions{
  display:flex;
  gap:10px;
  margin-top:1rem;
}

.form-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:1rem;
}

.form-group{
  display:flex;
  flex-direction:column;
  gap:6px;
}

.form-group.full{
  grid-column:1/-1;
}

label{
  font-size:12px;
  color:var(--muted);
  font-weight:600;
  text-transform:uppercase;
}

input,select,textarea{
  padding:11px;
  border-radius:10px;
  border:1px solid var(--border);
  font-size:14px;
}

input:focus,select:focus,textarea:focus{
  outline:none;
  border-color:var(--primary);
}

textarea{
  resize:vertical;
  min-height:80px;
}

.loading{
  text-align:center;
  padding:2rem;
}

.spinner{
  width:40px;
  height:40px;
  border:4px solid #dbe4f0;
  border-top-color:var(--primary);
  border-radius:50%;
  margin:0 auto 1rem;
  animation:spin 1s linear infinite;
}

@keyframes spin{
  to{
    transform:rotate(360deg);
  }
}

.banner{
  padding:12px 14px;
  border-radius:10px;
  margin-bottom:1rem;
  font-size:14px;
}

.success{
  background:#ecfdf3;
  color:#166534;
}

.error{
  background:#fef2f2;
  color:#991b1b;
}

.log-item{
  border:1px solid var(--border);
  border-radius:12px;
  padding:12px;
  margin-bottom:10px;
}

.log-top{
  display:flex;
  justify-content:space-between;
  margin-bottom:4px;
}

.log-merchant{
  font-weight:600;
}

.log-amount{
  font-weight:700;
}

.log-meta{
  color:var(--muted);
  font-size:13px;
}

@media(max-width:640px){
  .form-grid{
    grid-template-columns:1fr;
  }
}
</style>
</head>

<body>

<div class="container">

<div class="header">
  <h1>🧾 AI Receipt Auto-Fill</h1>
  <p>Upload a receipt and GPT-4 Vision extracts the information automatically</p>
</div>

<div id="error-box" class="banner error" style="display:none"></div>

<div id="upload-section" class="card">

<div class="dropzone" id="dropzone" onclick="document.getElementById('file-input').click()">
  <div id="dropzone-content">
    <div style="font-size:42px">📤</div>
    <h3>Upload Receipt</h3>
    <p>Click or drag & drop image</p>
  </div>
</div>

<input type="file" id="file-input" accept="image/*"/>

<div class="actions">
  <button class="btn btn-secondary" onclick="clearImage()">Clear</button>
  <button class="btn btn-primary" onclick="extractData()">Extract Receipt Data</button>
</div>

</div>

<div id="loading-section" class="card" style="display:none">
  <div class="loading">
    <div class="spinner"></div>
    <h3>Analyzing receipt...</h3>
    <p style="margin-top:8px;color:var(--muted)">
      GPT-4 Vision is extracting receipt information
    </p>
  </div>
</div>

<div id="form-section" class="card" style="display:none">

<div class="banner success">
  Receipt data extracted successfully
</div>

<div class="form-grid">

<div class="form-group full">
  <label>Merchant Name</label>
  <input type="text" id="merchant"/>
</div>

<div class="form-group">
  <label>Date</label>
  <input type="date" id="date"/>
</div>

<div class="form-group">
  <label>Currency</label>
  <select id="currency">
    <option>MYR</option>
    <option>USD</option>
    <option>SGD</option>
    <option>EUR</option>
    <option>GBP</option>
    <option>JPY</option>
  </select>
</div>

<div class="form-group full">
  <label>Total Amount</label>
  <input type="number" id="total" step="0.01"/>
</div>

<div class="form-group full">
  <label>Notes</label>
  <textarea id="notes"></textarea>
</div>

</div>

<div class="actions">
  <button class="btn btn-secondary" onclick="resetApp()">Scan Another</button>
  <button class="btn btn-primary" onclick="submitForm()">Submit</button>
</div>

</div>

<div class="card">
  <h3 style="margin-bottom:1rem">Submission Log</h3>
  <div id="submission-log"></div>
</div>

</div>

<script>

let selectedFile = null;
let submissions = JSON.parse(localStorage.getItem("receipt_submissions") || "[]");

renderLog();

const dropzone = document.getElementById("dropzone");

dropzone.addEventListener("dragover", e => {
  e.preventDefault();
});

dropzone.addEventListener("drop", e => {
  e.preventDefault();

  const file = e.dataTransfer.files[0];

  if(file){
    handleFile(file);
  }
});

document.getElementById("file-input").addEventListener("change", e => {
  if(e.target.files[0]){
    handleFile(e.target.files[0]);
  }
});

function handleFile(file){

  if(!file.type.startsWith("image/")){
    showError("Please upload an image.");
    return;
  }

  selectedFile = file;

  const url = URL.createObjectURL(file);

  document.getElementById("dropzone-content").innerHTML = `
    <img src="${url}">
    <p style="margin-top:10px">
      ${file.name}
    </p>
  `;
}

function clearImage(){
  selectedFile = null;

  document.getElementById("file-input").value = "";

  document.getElementById("dropzone-content").innerHTML = `
    <div style="font-size:42px">📤</div>
    <h3>Upload Receipt</h3>
    <p>Click or drag & drop image</p>
  `;
}

async function extractData(){

  if(!selectedFile){
    showError("Please upload a receipt image.");
    return;
  }

  clearError();

  document.getElementById("loading-section").style.display = "block";

  try{

    const fd = new FormData();
    fd.append("receipt", selectedFile);

    const res = await fetch("/extract", {
      method:"POST",
      body:fd
    });

    const data = await res.json();

    if(!res.ok){
      throw new Error(data.error || "Extraction failed");
    }

    document.getElementById("merchant").value = data.merchant || "";
    document.getElementById("date").value = data.date || "";
    document.getElementById("total").value = data.total || "";
    document.getElementById("currency").value = data.currency || "MYR";
    document.getElementById("notes").value = data.notes || "";

    document.getElementById("form-section").style.display = "block";

  }catch(err){
    showError(err.message);
  }

  document.getElementById("loading-section").style.display = "none";
}

async function submitForm(){

  const payload = {
    merchant: document.getElementById("merchant").value,
    date: document.getElementById("date").value,
    total: document.getElementById("total").value,
    currency: document.getElementById("currency").value,
    notes: document.getElementById("notes").value
  };

  try{

    const res = await fetch("/submit", {
      method:"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body:JSON.stringify(payload)
    });

    const data = await res.json();

    if(!res.ok){
      throw new Error(data.error);
    }

    submissions.unshift(data.submission);

    localStorage.setItem(
      "receipt_submissions",
      JSON.stringify(submissions)
    );

    renderLog();

    alert("Receipt submitted successfully!");

    resetApp();

  }catch(err){
    showError(err.message);
  }
}

function renderLog(){

  const log = document.getElementById("submission-log");

  if(!submissions.length){
    log.innerHTML = "<p style='color:#64748b'>No submissions yet.</p>";
    return;
  }

  log.innerHTML = submissions.map(item => `
    <div class="log-item">

      <div class="log-top">
        <div class="log-merchant">
          ${item.merchant}
        </div>

        <div class="log-amount">
          ${item.currency} ${item.total}
        </div>
      </div>

      <div class="log-meta">
        ${item.date}
      </div>

      <div class="log-meta" style="margin-top:4px">
        ${item.submitted_at}
      </div>

    </div>
  `).join("");
}

function resetApp(){

  clearImage();

  document.getElementById("form-section").style.display = "none";

  document.getElementById("merchant").value = "";
  document.getElementById("date").value = "";
  document.getElementById("total").value = "";
  document.getElementById("notes").value = "";
}

function showError(msg){

  const box = document.getElementById("error-box");

  box.style.display = "block";
  box.textContent = msg;
}

function clearError(){

  document.getElementById("error-box").style.display = "none";
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

    try:

        api_key = os.environ.get("OPENAI_API_KEY", "")

        if not api_key:
            return jsonify({
                "error":"OPENAI_API_KEY not found in .env"
            }), 400

        if "receipt" not in request.files:
            return jsonify({
                "error":"No receipt uploaded"
            }), 400

        file = request.files["receipt"]

        if not file.content_type.startswith("image/"):
            return jsonify({
                "error":"Please upload an image file"
            }), 400

        raw_bytes = file.read()

        base64_image = base64.b64encode(raw_bytes).decode("utf-8")

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {
                    "role":"system",
                    "content":"You extract receipt information and return JSON only."
                },
                {
                    "role":"user",
                    "content":[
                        {
                            "type":"text",
                            "text":"""
Extract these fields from the receipt:

- merchant
- date
- total
- currency
- notes

Rules:
- date must be YYYY-MM-DD
- currency must be ISO code
- total numbers only

Return ONLY JSON.
"""
                        },
                        {
                            "type":"image_url",
                            "image_url":{
                                "url":f"data:{file.content_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )

        raw = response.choices[0].message.content.strip()

        parsed = json.loads(raw)

        return jsonify(parsed)

    except json.JSONDecodeError:
        return jsonify({
            "error":"AI returned invalid JSON"
        }), 500

    except Exception as exc:
        return jsonify({
            "error":str(exc)
        }), 500

@app.route("/submit", methods=["POST"])
def submit():

    try:

        data = request.get_json(force=True)

        entry = {
            "merchant": data.get("merchant",""),
            "date": data.get("date",""),
            "total": data.get("total",""),
            "currency": data.get("currency","MYR"),
            "notes": data.get("notes",""),
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        submissions.append(entry)

        return jsonify({
            "success":True,
            "submission":entry
        })

    except Exception as exc:
        return jsonify({
            "error":str(exc)
        }), 500

@app.route("/submissions")
def get_submissions():
    return jsonify(submissions)

if __name__ == "__main__":

    print("=" * 50)
    print("🧾 AI Receipt Auto-Fill")
    print("=" * 50)
    print("Open: http://localhost:5000")
    print("=" * 50)

    app.run(debug=True, port=5000)
