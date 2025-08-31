// Main UI behaviors for the upload/analysis page.
// Intentionally compact and readable — favors clarity over cleverness.
const dropArea = document.getElementById("dropArea");
const fileInput = document.getElementById("fileInput");
const form = document.getElementById("uploadForm");
const loading = document.getElementById("loading");
const fileList = document.getElementById("fileList");
const submitBtn = document.getElementById("submitBtn");
const clearBtn = document.getElementById("clearFiles");

const allowedExt = new Set(["pdf", "png", "jpg", "jpeg"]);
let dt = new DataTransfer();

function fmtBytes(bytes) {
  const sizes = ["B", "KB", "MB", "GB"]; let i = 0; let v = bytes;
  while (v >= 1024 && i < sizes.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(i === 0 ? 0 : 1)} ${sizes[i]}`;
}

function renderFileList() {
  if (!fileList) return;
  fileList.innerHTML = "";
  Array.from(dt.files).forEach((f, idx) => {
    const li = document.createElement("li");
    li.className = "file-item d-flex align-items-center justify-content-between py-1 px-2 border rounded mb-1";
    li.innerHTML = `
      <span class="text-truncate me-2" style="max-width: 75%">${f.name} <span class="text-muted">(${fmtBytes(f.size)})</span></span>
      <button type="button" class="btn btn-sm btn-outline-danger remove-file" data-index="${idx}">Remove</button>
    `;
    fileList.appendChild(li);
  });
  if (submitBtn) submitBtn.disabled = dt.files.length === 0;
}

function addFiles(files) {
  if (!files) return;
  const existing = new Set(Array.from(dt.files).map(f => `${f.name}-${f.size}`));
  let skippedInvalid = 0, skippedDup = 0, added = 0;
  Array.from(files).forEach((f) => {
    const ext = f.name.split(".").pop().toLowerCase();
    if (!allowedExt.has(ext)) { skippedInvalid++; return; }
    const key = `${f.name}-${f.size}`;
    if (existing.has(key)) { skippedDup++; return; }
    dt.items.add(f);
    added++;
  });
  fileInput.files = dt.files;
  renderFileList();
  if (added > 0) showToast(`${added} file(s) added.`, "success");
  if (skippedDup > 0) showToast(`${skippedDup} duplicate file(s) skipped.`, "warning");
  if (skippedInvalid > 0) showToast(`${skippedInvalid} unsupported file(s) skipped.`, "danger");
}

if (dropArea && fileInput) {
  dropArea.addEventListener("click", () => fileInput.click());
  dropArea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });
  dropArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropArea.classList.add("dragover");
  });
  dropArea.addEventListener("dragleave", () => dropArea.classList.remove("dragover"));
  dropArea.addEventListener("drop", (e) => {
    e.preventDefault();
    dropArea.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length) {
      addFiles(e.dataTransfer.files);
    }
  });
}

if (fileInput) {
  fileInput.addEventListener("change", (e) => addFiles(e.target.files));
}

if (fileList) {
  fileList.addEventListener("click", (e) => {
    const btn = e.target.closest(".remove-file");
    if (!btn) return;
    const idx = Number(btn.getAttribute("data-index"));
    const newDT = new DataTransfer();
    Array.from(dt.files).forEach((f, i) => { if (i !== idx) newDT.items.add(f); });
    dt = newDT;
    fileInput.files = dt.files;
    renderFileList();
  });
}

if (clearBtn) {
  clearBtn.addEventListener("click", () => {
    dt = new DataTransfer();
    fileInput.value = "";
    fileInput.files = dt.files;
    renderFileList();
  });
}

function showCopied(btn) {
  const orig = btn.textContent;
  btn.textContent = "Copied!";
  btn.disabled = true;
  setTimeout(() => { btn.textContent = orig; btn.disabled = false; }, 1200);
}

document.addEventListener("click", async (e) => {
  const copyBtn = e.target.closest(".copy-btn");
  if (!copyBtn) return;
  try {
    if (copyBtn.dataset.copyTarget) {
      const el = document.getElementById(copyBtn.dataset.copyTarget);
      if (el) {
        await navigator.clipboard.writeText(el.innerText.trim());
        showCopied(copyBtn);
        showToast("Copied to clipboard", "primary");
      }
    } else if (copyBtn.dataset.copyText) {
      await navigator.clipboard.writeText(copyBtn.dataset.copyText);
      showCopied(copyBtn);
      showToast("Copied to clipboard", "primary");
    }
  } catch (_) {}
});

const copyHashtagsBtn = document.getElementById("copyHashtags");
if (copyHashtagsBtn) {
  copyHashtagsBtn.addEventListener("click", async () => {
    const tags = copyHashtagsBtn.getAttribute("data-tags") || "";
    try {
      await navigator.clipboard.writeText(tags.trim());
      showCopied(copyHashtagsBtn);
      showToast("Hashtags copied", "primary");
    } catch (_) {}
  });
}

if (form) {
  form.addEventListener("submit", () => {
    if (loading) loading.classList.remove("d-none");
    if (submitBtn) submitBtn.disabled = true;
    if (clearBtn) clearBtn.disabled = true;
  });
}

// Theme toggle (persisted)
const themeToggle = document.getElementById("themeToggle");
function applyTheme(mode) {
  const isDark = mode === "dark";
  document.body.classList.toggle("theme-dark", isDark);
  if (themeToggle) {
    themeToggle.setAttribute("aria-pressed", String(isDark));
    themeToggle.textContent = isDark ? "Light" : "Dark";
  }
}

// Toast helper using Bootstrap
function showToast(message, variant = "primary") {
  const container = document.getElementById("toastContainer");
  if (!container || !window.bootstrap) return;
  const wrapper = document.createElement("div");
  wrapper.className = `toast align-items-center text-bg-${variant} border-0`;
  wrapper.setAttribute("role", "status");
  wrapper.setAttribute("aria-live", "polite");
  wrapper.setAttribute("aria-atomic", "true");
  wrapper.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>`;
  container.appendChild(wrapper);
  const t = new bootstrap.Toast(wrapper, { delay: 1600 });
  t.show();
  wrapper.addEventListener("hidden.bs.toast", () => wrapper.remove());
}

// Show More/Less for combined extracted text
const combinedText = document.getElementById("combinedText");
const toggleCombinedBtn = document.getElementById("toggleCombined");
if (combinedText && toggleCombinedBtn) {
  function updateToggleLabel() {
    const expanded = combinedText.classList.contains("expanded-scroll");
    toggleCombinedBtn.textContent = expanded ? "Show Less" : "Show More";
  }
  toggleCombinedBtn.addEventListener("click", () => {
    combinedText.classList.toggle("expanded-scroll");
    updateToggleLabel();
  });
  // Only show the toggle if content is long
  if (combinedText.scrollHeight <= combinedText.clientHeight + 10) {
    toggleCombinedBtn.classList.add("d-none");
  }
}

// Save Result as JSON
const saveBtn = document.getElementById("saveResult");
if (saveBtn) {
  saveBtn.addEventListener("click", () => {
    try {
      const script = document.getElementById("analysisData");
      if (!script) return;
      const data = JSON.parse(script.textContent || "{}");
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      a.href = URL.createObjectURL(blob);
      a.download = `analysis-${ts}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast("Result saved", "success");
    } catch (_) { showToast("Could not save result", "danger"); }
  });
}

// Clear All (reset page to initial state)
const clearAllBtn = document.getElementById("clearAll");
if (clearAllBtn) {
  clearAllBtn.addEventListener("click", () => {
    window.location.href = "/";
  });
}

// Copy all engagement tips
const copyEngBtn = document.getElementById("copyEngagement");
if (copyEngBtn) {
  copyEngBtn.addEventListener("click", async () => {
    const list = document.getElementById("engagementList");
    if (!list) return;
    const text = Array.from(list.querySelectorAll("li")).map(li => li.innerText.trim()).join("\n");
    try {
      await navigator.clipboard.writeText(text);
      showToast("Engagement tips copied", "primary");
    } catch (_) {}
  });
}
const savedTheme = localStorage.getItem("theme") || "light";
applyTheme(savedTheme);
if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const cur = document.body.classList.contains("theme-dark") ? "dark" : "light";
    const next = cur === "dark" ? "light" : "dark";
    localStorage.setItem("theme", next);
    applyTheme(next);
  });
}
