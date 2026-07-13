INDEX = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ますびと商店 データ作成</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">

<div class="bg-white rounded-2xl shadow-lg w-full max-w-xl p-8">
  <h1 class="text-2xl font-bold text-gray-800 mb-1">ますびと商店</h1>
  <p class="text-gray-500 text-sm mb-6">データ作成ツール</p>

  <!-- Mode tabs -->
  <div id="tabs" class="flex gap-1 border-b border-gray-200 mb-6">
    <button data-mode="shukka"
            class="tab px-5 py-2.5 text-sm font-semibold border-b-2 -mb-px transition-colors">
      出荷
    </button>
    <button data-mode="hasso"
            class="tab px-5 py-2.5 text-sm font-semibold border-b-2 -mb-px transition-colors">
      発送
    </button>
  </div>

  <!-- 出荷 panel -->
  <div id="panel-shukka" class="panel">
    <div id="dropzone"
         class="border-2 border-dashed border-blue-300 rounded-xl p-10 text-center cursor-pointer
                hover:border-blue-500 hover:bg-blue-50 transition-colors"
         onclick="document.getElementById('fileInput').click()">
      <svg class="mx-auto mb-3 w-12 h-12 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
      </svg>
      <p class="text-blue-600 font-medium">CSVファイルをドロップ</p>
      <p class="text-gray-400 text-sm mt-1">またはクリックしてファイルを選択</p>
      <input id="fileInput" type="file" accept=".csv" class="hidden">
    </div>
    <p class="text-gray-400 text-xs mt-3">
      棚番で高知／堺に振り分け、注文データ・トータルピック表・ピッキングリストをZIPで出力します。
    </p>
  </div>

  <!-- 発送 panel -->
  <div id="panel-hasso" class="panel hidden">
    <div class="space-y-2">
      <div id="row-nouhin" class="hasso-row flex items-center gap-3 border border-gray-200 rounded-xl px-4 py-3">
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-gray-700">
            ① 納品データ <span class="text-gray-400 font-normal text-xs ml-1">任意</span>
          </p>
          <p id="name-nouhin" class="text-xs text-gray-400 truncate mt-0.5">納品データ_YYYYMMDD_HHMM.csv</p>
        </div>
        <button class="choose shrink-0 text-sm text-gray-600 border border-gray-300 rounded-lg px-3 py-1.5
                       hover:bg-gray-50 transition-colors" data-key="nouhin">選択</button>
        <input id="file-nouhin" type="file" accept=".csv" class="hidden">
      </div>

      <div id="row-sagawa" class="hasso-row flex items-center gap-3 border border-gray-200 rounded-xl px-4 py-3">
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-gray-700">
            ② 出荷履歴（佐川） <span class="text-gray-400 font-normal text-xs ml-1">任意</span>
          </p>
          <p id="name-sagawa" class="text-xs text-gray-400 truncate mt-0.5">shukka_rireki_YYYYMMDD*.csv</p>
        </div>
        <button class="choose shrink-0 text-sm text-gray-600 border border-gray-300 rounded-lg px-3 py-1.5
                       hover:bg-gray-50 transition-colors" data-key="sagawa">選択</button>
        <input id="file-sagawa" type="file" accept=".csv" class="hidden">
      </div>

      <div id="row-hikkyu" class="hasso-row flex items-center gap-3 border border-gray-200 rounded-xl px-4 py-3">
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-gray-700">
            ③ 飛脚ゆうパケット取込明細 <span class="text-gray-400 font-normal text-xs ml-1">任意</span>
          </p>
          <p id="name-hikkyu" class="text-xs text-gray-400 truncate mt-0.5">飛脚ゆうパケット便ラベル発行システム_取込明細_*.csv</p>
        </div>
        <button class="choose shrink-0 text-sm text-gray-600 border border-gray-300 rounded-lg px-3 py-1.5
                       hover:bg-gray-50 transition-colors" data-key="hikkyu">選択</button>
        <input id="file-hikkyu" type="file" accept=".csv" class="hidden">
      </div>
    </div>

    <button id="hassoRun" disabled
            class="w-full mt-4 py-3 rounded-xl font-semibold text-white bg-blue-600 hover:bg-blue-700
                   disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-default transition-colors">
      変換してダウンロード
    </button>
    <p class="text-gray-400 text-xs mt-3">
      1つ以上選択してください。キャリア別の注文伝票csv連携をZIPで出力します。
    </p>
  </div>

  <!-- Progress section (shared) -->
  <div id="progressSection" class="hidden mt-6">
    <div class="flex justify-between text-sm text-gray-600 mb-1">
      <span id="statusMsg">処理中...</span>
      <span id="pctLabel">0%</span>
    </div>
    <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
      <div id="progressBar"
           class="bg-blue-500 h-3 rounded-full transition-all duration-300"
           style="width:0%"></div>
    </div>
    <div id="stepBadges" class="flex flex-wrap gap-2 mt-3"></div>
  </div>

  <!-- Download section (shared; auto-download is triggered) -->
  <div id="downloadSection" class="hidden mt-6 text-center">
    <p class="text-green-700 font-semibold mb-3">✓ ダウンロードが開始されました</p>
    <div id="resultList" class="text-left text-xs text-gray-600 bg-green-50 rounded-xl p-4 mb-4 hidden"></div>
    <button onclick="doDownload()"
            class="inline-block bg-green-600 hover:bg-green-700 text-white font-semibold
                   px-8 py-3 rounded-xl transition-colors shadow">
      再ダウンロード
    </button>
    <button onclick="reset()"
            class="ml-4 text-sm text-gray-400 hover:text-gray-600 underline">
      別のファイルを処理する
    </button>
  </div>

  <!-- Error section (shared) -->
  <div id="errorSection" class="hidden mt-6 bg-red-50 border border-red-200 rounded-xl p-4">
    <p class="text-red-700 font-medium text-sm">エラーが発生しました</p>
    <p id="errorMsg" class="text-red-600 text-sm mt-1"></p>
    <button onclick="reset()"
            class="mt-3 text-sm text-red-500 hover:text-red-700 underline">
      やり直す
    </button>
  </div>
</div>

<script>
const MODES = {
  shukka: {
    endpoint: "/api/upload/shukka",
    steps: {
      parsing:        "CSV読み込み",
      kouchi:         "高知",
      sakai_main:     "堺メイン",
      sakai_cooler:   "堺クーラー",
      sakai_yupacket: "堺ゆうパケット",
      total_pick:     "ピック表",
      picking_list:   "ピッキングリスト",
      zipping:        "ZIP",
    },
  },
  hasso: {
    endpoint: "/api/upload/hasso",
    steps: {
      parsing: "CSV読み込み",
      yamato:  "ヤマト",
      sagawa:  "佐川",
      hikkyu:  "飛脚ゆうパケット",
      zipping: "ZIP",
    },
  },
};

const HASSO_KEYS = ["nouhin", "sagawa", "hikkyu"];
const HASSO_PLACEHOLDERS = {
  nouhin: "納品データ_YYYYMMDD_HHMM.csv",
  sagawa: "shukka_rireki_YYYYMMDD*.csv",
  hikkyu: "飛脚ゆうパケット便ラベル発行システム_取込明細_*.csv",
};

const TAB_ON  = "border-blue-500 text-blue-600";
const TAB_OFF = "border-transparent text-gray-400 hover:text-gray-600";
const ROW_BASE = "hasso-row flex items-center gap-3 border rounded-xl px-4 py-3 transition-colors ";

let currentMode = "shukka";
let busy        = false;

const dropzone    = document.getElementById("dropzone");
const fileInput   = document.getElementById("fileInput");
const progressSec = document.getElementById("progressSection");
const downloadSec = document.getElementById("downloadSection");
const errorSec    = document.getElementById("errorSection");
const progressBar = document.getElementById("progressBar");
const statusMsg   = document.getElementById("statusMsg");
const pctLabel    = document.getElementById("pctLabel");
const stepBadges  = document.getElementById("stepBadges");
const errorMsg    = document.getElementById("errorMsg");
const resultList  = document.getElementById("resultList");
const hassoRun    = document.getElementById("hassoRun");
const tabs        = [...document.querySelectorAll(".tab")];
const chooseBtns  = [...document.querySelectorAll(".choose")];

let lastBlobUrl  = null;
let lastFilename = null;

/* ---------- tabs ---------- */

tabs.forEach(tab => {
  tab.addEventListener("click", () => {
    if (busy) return;
    switchMode(tab.dataset.mode);
  });
});

function switchMode(mode) {
  currentMode = mode;
  tabs.forEach(t => {
    const on = t.dataset.mode === mode;
    t.className = "tab px-5 py-2.5 text-sm font-semibold border-b-2 -mb-px transition-colors "
                + (on ? TAB_ON : TAB_OFF);
  });
  for (const m of Object.keys(MODES)) {
    document.getElementById("panel-" + m).classList.toggle("hidden", m !== mode);
  }
  resetShared();
}

function setBusy(v) {
  busy = v;
  tabs.forEach(t => {
    t.classList.toggle("opacity-40", v);
    t.classList.toggle("cursor-not-allowed", v);
  });
  chooseBtns.forEach(b => { b.disabled = v; b.classList.toggle("opacity-40", v); });
  dropzone.classList.toggle("opacity-50", v);
  dropzone.classList.toggle("pointer-events-none", v);
  updateHassoButton();
}

/* ---------- 出荷: single CSV, starts on select ---------- */

dropzone.addEventListener("dragover", e => { e.preventDefault(); dropzone.classList.add("border-blue-500","bg-blue-50"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("border-blue-500","bg-blue-50"));
dropzone.addEventListener("drop", e => {
  e.preventDefault();
  dropzone.classList.remove("border-blue-500","bg-blue-50");
  const file = e.dataTransfer.files[0];
  if (file) startShukka(file);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) startShukka(fileInput.files[0]);
});

function startShukka(file) {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    showError("CSVファイルを選択してください");
    return;
  }
  const fd = new FormData();
  fd.append("file", file);
  startJob(fd);
}

/* ---------- 発送: up to 3 CSVs, starts on button ---------- */

chooseBtns.forEach(btn => {
  const key = btn.dataset.key;
  btn.addEventListener("click", () => document.getElementById("file-" + key).click());
  document.getElementById("file-" + key).addEventListener("change", () => onHassoPick(key));
});

function onHassoPick(key) {
  const file = document.getElementById("file-" + key).files[0];
  const nameEl = document.getElementById("name-" + key);
  const rowEl  = document.getElementById("row-" + key);
  if (file) {
    nameEl.textContent = file.name;
    nameEl.className = "text-xs text-blue-600 truncate mt-0.5";
    rowEl.className = ROW_BASE + "border-blue-400 bg-blue-50";
  } else {
    nameEl.textContent = HASSO_PLACEHOLDERS[key];
    nameEl.className = "text-xs text-gray-400 truncate mt-0.5";
    rowEl.className = ROW_BASE + "border-gray-200";
  }
  updateHassoButton();
}

function pickedHassoFiles() {
  const out = {};
  for (const key of HASSO_KEYS) {
    const f = document.getElementById("file-" + key).files[0];
    if (f) out[key] = f;
  }
  return out;
}

function updateHassoButton() {
  hassoRun.disabled = busy || Object.keys(pickedHassoFiles()).length === 0;
}

hassoRun.addEventListener("click", () => {
  const picked = pickedHassoFiles();
  const bad = Object.values(picked).find(f => !f.name.toLowerCase().endsWith(".csv"));
  if (bad) {
    showError("CSVファイルを選択してください: " + bad.name);
    return;
  }
  const fd = new FormData();
  for (const [key, file] of Object.entries(picked)) fd.append(key, file);
  startJob(fd);
});

/* ---------- shared job runner ---------- */

async function startJob(fd) {
  showProgress();

  let res;
  try {
    res = await fetch(MODES[currentMode].endpoint, { method: "POST", body: fd });
  } catch (e) {
    showError("アップロードに失敗しました: " + e.message);
    return;
  }

  if (!res.ok) {
    const txt = await res.text().catch(() => res.statusText);
    showError("アップロードエラー: " + txt);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\\n");
      buffer = parts.pop();
      for (const line of parts) {
        if (line.startsWith("data: ")) {
          try { handleEvent(JSON.parse(line.slice(6))); } catch (_) {}
        }
      }
    }
  } catch (e) {
    showError("ストリーム読み取りエラー: " + e.message);
  } finally {
    setBusy(false);
  }
}

function handleEvent(data) {
  updateProgress(data);
  if (data.step === "done") {
    triggerDownload(data.data, data.filename);
    showResults(data.results);
    downloadSec.classList.remove("hidden");
  }
  if (data.step === "error") {
    showError(data.message || "不明なエラー");
  }
}

function showResults(results) {
  if (!results || !results.length) {
    resultList.classList.add("hidden");
    return;
  }
  resultList.innerHTML = results
    .map(r => `<div class="py-0.5">✅ ${r.name}（${r.count}件）</div>`)
    .join("");
  resultList.classList.remove("hidden");
}

function triggerDownload(b64, filename) {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const blob = new Blob([bytes], { type: "application/zip" });
  if (lastBlobUrl) URL.revokeObjectURL(lastBlobUrl);
  lastBlobUrl = URL.createObjectURL(blob);
  lastFilename = filename;
  doDownload();
}

function doDownload() {
  if (!lastBlobUrl) return;
  const a = document.createElement("a");
  a.href = lastBlobUrl;
  a.download = lastFilename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function updateProgress(data) {
  const pct = data.pct || 0;
  progressBar.style.width = pct + "%";
  pctLabel.textContent = pct + "%";
  statusMsg.textContent = data.message || "";

  const label = MODES[currentMode].steps[data.step];
  if (label) addBadge(label);
}

function addBadge(label) {
  for (const b of stepBadges.children) {
    if (b.textContent === label) return;
  }
  const span = document.createElement("span");
  span.textContent = label;
  span.className = "text-xs bg-blue-100 text-blue-700 rounded-full px-2 py-0.5";
  stepBadges.appendChild(span);
}

function showProgress() {
  setBusy(true);
  progressSec.classList.remove("hidden");
  downloadSec.classList.add("hidden");
  errorSec.classList.add("hidden");
  resultList.classList.add("hidden");
  stepBadges.innerHTML = "";
  progressBar.style.width = "0%";
  pctLabel.textContent = "0%";
  statusMsg.textContent = "準備中...";
}

function showError(msg) {
  setBusy(false);
  errorMsg.textContent = msg;
  errorSec.classList.remove("hidden");
  progressSec.classList.add("hidden");
}

function resetShared() {
  setBusy(false);
  if (lastBlobUrl) { URL.revokeObjectURL(lastBlobUrl); lastBlobUrl = null; lastFilename = null; }
  progressSec.classList.add("hidden");
  downloadSec.classList.add("hidden");
  errorSec.classList.add("hidden");
  resultList.classList.add("hidden");
  stepBadges.innerHTML = "";
}

function reset() {
  resetShared();
  fileInput.value = "";
  for (const key of HASSO_KEYS) {
    document.getElementById("file-" + key).value = "";
    onHassoPick(key);
  }
}

switchMode("shukka");
for (const key of HASSO_KEYS) onHassoPick(key);
</script>
</body>
</html>
"""
