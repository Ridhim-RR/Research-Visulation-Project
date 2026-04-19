import "./styles.css";

const DEFAULT_SETTINGS = {
  fs: 512,
  twndw: 1,
  frame_index: 1,
  nj: 8,
  freq_max_hz: 64,
  img_n: 900,
};

const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const statusEl = document.getElementById("status");
const errorEl = document.getElementById("error");
const backendStatusEl = document.getElementById("backendStatus");
const semaniImage = document.getElementById("semaniImage");
const channelsImage = document.getElementById("channelsImage");

function setStatus(message) {
  statusEl.textContent = message;
}

function setBackendStatus(message) {
  backendStatusEl.textContent = message;
}

function setError(message) {
  if (!message) {
    errorEl.hidden = true;
    errorEl.textContent = "";
    return;
  }

  errorEl.hidden = false;
  errorEl.textContent = message;
}

function setImage(imageElement, base64, altText) {
  if (!base64) {
    imageElement.removeAttribute("src");
    imageElement.classList.remove("ready");
    imageElement.alt = altText;
    return;
  }

  imageElement.src = `data:image/png;base64,${base64}`;
  imageElement.alt = altText;
  imageElement.classList.add("ready");
}

function clearResults() {
  setImage(semaniImage, "", "Semani figure output");
  setImage(channelsImage, "", "Channels figure output");
}

function renderResults(payload) {
  const semaniFigure = payload.images?.semaniFigurePngBase64 || "";
  const channelsFigure = payload.images?.channelsFigurePngBase64 || "";

  setImage(semaniImage, semaniFigure, "Semani figure output");
  setImage(channelsImage, channelsFigure, "Channels figure output");
}

async function uploadAndRender(event) {
  event.preventDefault();
  setError("");

  const selectedFile = fileInput.files?.[0];
  if (!selectedFile) {
    setError("Select a MAT file first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("fs", String(DEFAULT_SETTINGS.fs));
  formData.append("twndw", String(DEFAULT_SETTINGS.twndw));
  formData.append("frame_index", String(DEFAULT_SETTINGS.frame_index));
  formData.append("nj", String(DEFAULT_SETTINGS.nj));
  formData.append("freq_max_hz", String(DEFAULT_SETTINGS.freq_max_hz));
  formData.append("img_n", String(DEFAULT_SETTINGS.img_n));

  setBackendStatus("Processing upload...");
  setStatus(`Uploading ${selectedFile.name}...`);
  clearResults();

  try {
    const response = await fetch("/api/eeg/semani/process", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Upload failed.");
    }

    renderResults(payload);
    setBackendStatus("Ready");
    setStatus(`Visualization loaded for ${selectedFile.name}.`);
  } catch (error) {
    setBackendStatus("Error");
    setStatus("Upload failed.");
    setError(error.message || "Unexpected error.");
  }
}

uploadForm.addEventListener("submit", uploadAndRender);
setBackendStatus("Ready");
clearResults();
