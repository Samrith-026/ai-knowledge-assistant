const $ = (selector) => document.querySelector(selector);
const ui = {
  docCount: $("#documentCount"), chunkCount: $("#chunkCount"), answerCount: $("#answerCount"),
  libraryCount: $("#libraryCount"), documentList: $("#documentList"), emptyLibrary: $("#emptyLibrary"),
  feedback: $("#uploadFeedback"), uploadTitle: $("#uploadTitle"), uploadHint: $("#uploadHint"),
  fileInput: $("#fileInput"), dropzone: $("#dropzone"), conversation: $("#conversation"),
  questionInput: $("#questionInput"), questionForm: $("#questionForm"), sendButton: $("#sendButton"),
  charCount: $("#characterCount"),
};
let answerCount = 0;
let uploading = false;
let asking = false;

function setServiceStatus(online, label) {
  for (const dot of [$("#sideDot"), $("#mainDot")]) {
    dot.classList.toggle("online", online);
    dot.classList.toggle("offline", !online);
  }
  $("#sideState").textContent = label;
  $("#mainState").textContent = online ? "Online" : "Unavailable";
}

async function requestJson(path, options) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : "The request could not be completed.");
  }
  return data;
}

function renderDocuments(items) {
  ui.documentList.replaceChildren();
  const totalChunks = items.reduce((sum, item) => sum + Number(item.chunks || 0), 0);
  ui.docCount.textContent = String(items.length);
  ui.chunkCount.textContent = String(totalChunks);
  ui.libraryCount.textContent = String(items.length);
  ui.emptyLibrary.hidden = items.length !== 0;
  ui.documentList.hidden = items.length === 0;

  for (const item of items) {
    const row = document.createElement("div");
    row.className = "document-row";
    const icon = document.createElement("span");
    icon.className = "file-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = item.filename.toLowerCase().endsWith(".pdf") ? "▤" : "≡";
    const meta = document.createElement("div");
    meta.className = "document-meta";
    const name = document.createElement("div");
    name.className = "document-name";
    name.title = item.filename;
    name.textContent = item.filename;
    const detail = document.createElement("div");
    detail.className = "document-detail";
    const count = Number(item.chunks || 0);
    detail.textContent = `${count} searchable ${count === 1 ? "passage" : "passages"}`;
    meta.append(name, detail);
    const arrow = document.createElement("span");
    arrow.className = "document-arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "↗";
    row.append(icon, meta, arrow);
    ui.documentList.append(row);
  }
}

async function loadDocuments() {
  ui.documentList.hidden = false;
  ui.emptyLibrary.hidden = true;
  const loading = document.createElement("div");
  loading.className = "loading";
  const spinner = document.createElement("i");
  spinner.className = "spinner";
  loading.append(spinner, document.createTextNode(" Loading your library…"));
  ui.documentList.replaceChildren(loading);
  try {
    const data = await requestJson("/documents");
    renderDocuments(data.documents || []);
    setServiceStatus(true, "Service online");
  } catch (error) {
    ui.documentList.replaceChildren();
    const message = document.createElement("div");
    message.className = "loading";
    message.textContent = `Could not load documents: ${error.message}`;
    ui.documentList.append(message);
    ui.docCount.textContent = "—";
    ui.chunkCount.textContent = "—";
    setServiceStatus(false, "Service unavailable");
  }
}

function uploadMessage(message, isError = false) {
  ui.feedback.textContent = message;
  ui.feedback.classList.toggle("error", isError);
}

async function uploadFile(file) {
  if (uploading || !file) return;
  const extension = file.name.split(".").pop().toLowerCase();
  if (!["pdf", "txt"].includes(extension)) {
    uploadMessage("Choose a PDF or TXT file.", true);
    return;
  }
  uploading = true;
  ui.fileInput.disabled = true;
  ui.uploadTitle.textContent = "Preparing your document…";
  ui.uploadHint.textContent = `${file.name} · ${(file.size / (1024 * 1024)).toFixed(2)} MB`;
  ui.dropzone.classList.add("dragging");
  uploadMessage("Uploading and indexing. Larger documents may take a moment.");
  const form = new FormData();
  form.append("file", file);
  try {
    const result = await requestJson("/documents/upload", { method: "POST", body: form });
    uploadMessage(`${result.filename} added · ${result.chunks_created} passages indexed.`);
    await loadDocuments();
  } catch (error) {
    uploadMessage(error.message || "Upload failed. Check the file and try again.", true);
  } finally {
    uploading = false;
    ui.fileInput.disabled = false;
    ui.uploadTitle.innerHTML = 'Drop a file here, or <em>browse</em>';
    ui.uploadHint.textContent = "PDF or TXT · One file at a time";
    ui.dropzone.classList.remove("dragging");
    ui.fileInput.value = "";
  }
}

function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = role === "user" ? "user-message" : "assistant-message";
  if (role !== "user") {
    const avatar = document.createElement("span");
    avatar.className = "message-avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "✳";
    wrapper.append(avatar);
  }
  const body = document.createElement("div");
  body.className = "message-body";
  const meta = document.createElement("small");
  meta.className = "message-meta";
  meta.textContent = role === "user" ? "YOU · NOW" : "KNOWLEDGE ASSISTANT · NOW";
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  body.append(meta, paragraph);
  wrapper.append(body);
  ui.conversation.append(wrapper);
  ui.conversation.scrollTop = ui.conversation.scrollHeight;
  return { wrapper, body, paragraph };
}

function addSources(message, sources) {
  if (!Array.isArray(sources) || sources.length === 0) return;
  const list = document.createElement("div");
  list.className = "source-list";
  sources.forEach((source, index) => {
    const card = document.createElement("details");
    card.className = "source-card";
    const summary = document.createElement("summary");
    const number = document.createElement("span");
    number.className = "source-number";
    number.textContent = String(index + 1);
    const title = document.createElement("span");
    title.textContent = `${source.document_name} · passage ${Number(source.chunk_index) + 1}`;
    const distance = document.createElement("span");
    distance.className = "source-distance";
    distance.textContent = `distance ${Number(source.distance).toFixed(3)}`;
    summary.append(number, title, distance);
    const excerpt = document.createElement("p");
    excerpt.textContent = source.content;
    card.append(summary, excerpt);
    list.append(card);
  });
  message.body.append(list);
  ui.conversation.scrollTop = ui.conversation.scrollHeight;
}

async function askQuestion(question) {
  const cleaned = question.trim();
  if (asking || cleaned.length < 3) return;
  asking = true;
  ui.sendButton.disabled = true;
  addMessage("user", cleaned);
  const pending = addMessage("assistant", "Searching your documents for relevant passages…");
  try {
    const result = await requestJson("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: cleaned }),
    });
    pending.paragraph.textContent = result.answer;
    addSources(pending, result.sources);
    answerCount += 1;
    ui.answerCount.textContent = String(answerCount);
  } catch (error) {
    pending.paragraph.textContent = error.message || "I couldn’t complete that request. Please try again.";
  } finally {
    asking = false;
    ui.sendButton.disabled = false;
    ui.conversation.scrollTop = ui.conversation.scrollHeight;
  }
}

ui.fileInput.addEventListener("change", (event) => uploadFile(event.target.files[0]));
ui.dropzone.addEventListener("dragover", (event) => { event.preventDefault(); ui.dropzone.classList.add("dragging"); });
ui.dropzone.addEventListener("dragleave", () => ui.dropzone.classList.remove("dragging"));
ui.dropzone.addEventListener("drop", (event) => { event.preventDefault(); ui.dropzone.classList.remove("dragging"); uploadFile(event.dataTransfer.files[0]); });
$("#refreshButton").addEventListener("click", loadDocuments);
ui.questionInput.addEventListener("input", () => {
  ui.charCount.textContent = `${ui.questionInput.value.length} / 2000`;
  ui.questionInput.style.height = "auto";
  ui.questionInput.style.height = `${Math.min(ui.questionInput.scrollHeight, 110)}px`;
});
ui.questionForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = ui.questionInput.value;
  if (question.trim().length < 3) return;
  ui.questionInput.value = "";
  ui.questionInput.dispatchEvent(new Event("input"));
  askQuestion(question);
});
document.querySelectorAll(".suggestion").forEach((button) => button.addEventListener("click", () => askQuestion(button.dataset.question)));
$("#menuButton").addEventListener("click", () => {
  const sidebar = document.querySelector(".sidebar");
  const open = sidebar.classList.toggle("mobile-open");
  $("#menuButton").setAttribute("aria-expanded", String(open));
});
document.querySelectorAll(".nav-item").forEach((link) => link.addEventListener("click", () => {
  document.querySelector(".sidebar").classList.remove("mobile-open");
  $("#menuButton").setAttribute("aria-expanded", "false");
}));
loadDocuments();