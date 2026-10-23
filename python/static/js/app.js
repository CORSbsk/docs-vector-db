// ---------- Utilidades ----------

const $ = (selector) => document.querySelector(selector);

const els = {
  chat: $("#chat"),
  messages: $("#messages"),
  form: $("#chat-form"),
  input: $("#query"),
  sendBtn: $("#send-btn"),
  fileInput: $("#file-input"),
  uploadLabel: $("#upload-label"),
  uploadText: $("#upload-text"),
  docList: $("#doc-list"),
  docCount: $("#doc-count"),
  toasts: $("#toasts"),
  themeToggle: $("#theme-toggle"),
};

// Crea un elemento. El texto se asigna con textContent (nunca innerHTML):
// el contenido de los PDFs no es de confianza y no debe interpretarse como HTML.
function el(tag, className = "", text = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const data = await res.json();
      if (data.detail) {
        detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch (_) { /* la respuesta no era JSON */ }
    throw new Error(detail);
  }
  return res.json();
}

function toast(message, type = "info") {
  const alert = el("div", `alert alert-${type} shadow`);
  alert.appendChild(el("span", "", message));
  els.toasts.appendChild(alert);
  setTimeout(() => alert.remove(), 4500);
}

function scrollDown() {
  els.chat.scrollTo({ top: els.chat.scrollHeight, behavior: "smooth" });
}

// ---------- Tema claro / oscuro ----------

els.themeToggle.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("theme", next); } catch (_) {}
});

// ---------- Documentos ----------

async function loadDocuments() {
  try {
    renderDocuments(await api("/api/documents"));
  } catch (err) {
    toast(`No se pudo cargar la lista: ${err.message}`, "error");
  }
}

function renderDocuments(docs) {
  els.docList.replaceChildren();
  els.docCount.textContent = docs.length;

  if (!docs.length) {
    els.docList.appendChild(
      el("li", "text-sm opacity-60 p-2", "Aún no hay documentos. Sube un PDF para empezar.")
    );
    return;
  }

  for (const doc of docs) {
    const li = el("li", "flex items-center gap-2 p-2 rounded-lg bg-base-100");

    const info = el("div", "flex-1 min-w-0");
    info.appendChild(el("p", "truncate text-sm font-medium", doc.filename));
    info.appendChild(el("p", "text-xs opacity-60", `${doc.chunks} fragmentos`));

    const del = el("button", "btn btn-ghost btn-xs", "✕");
    del.type = "button";
    del.title = "Eliminar documento";
    del.addEventListener("click", () => deleteDocument(doc));

    li.append(info, del);
    els.docList.appendChild(li);
  }
}

async function deleteDocument(doc) {
  if (!confirm(`¿Eliminar "${doc.filename}" y todos sus fragmentos?`)) return;
  try {
    await api(`/api/documents/${doc.id}`, { method: "DELETE" });
    toast(`${doc.filename} eliminado`, "success");
    loadDocuments();
  } catch (err) {
    toast(`No se pudo eliminar: ${err.message}`, "error");
  }
}

// ---------- Subida de PDFs ----------

function setUploading(on) {
  els.uploadLabel.classList.toggle("btn-disabled", on);
  els.fileInput.disabled = on;
  els.uploadText.textContent = on ? "Procesando..." : "Subir PDF";
}

els.fileInput.addEventListener("change", async () => {
  const files = [...els.fileInput.files];
  els.fileInput.value = ""; // permite volver a elegir el mismo archivo
  if (!files.length) return;

  setUploading(true);
  for (const file of files) {
    const body = new FormData();
    body.append("file", file);
    try {
      const r = await api("/api/upload", { method: "POST", body });
      if (r.status === "ok") {
        toast(`${r.filename}: ${r.chunks} fragmentos guardados`, "success");
      } else if (r.status === "duplicate") {
        toast(`${r.filename} ya estaba cargado`, "warning");
      } else {
        toast(`${r.filename}: no se pudo extraer texto (¿PDF escaneado?)`, "warning");
      }
    } catch (err) {
      toast(`${file.name}: ${err.message}`, "error");
    }
  }
  setUploading(false);
  loadDocuments();
});

// ---------- Chat ----------

function addUserMessage(text) {
  const row = el("div", "chat chat-end");
  row.appendChild(el("div", "chat-bubble chat-bubble-primary whitespace-pre-wrap", text));
  els.messages.appendChild(row);
}

function addAssistantMessage() {
  const wrap = el("div", "space-y-3");
  const row = el("div", "chat chat-start");
  const bubble = el("div", "chat-bubble");
  row.appendChild(bubble);
  const results = el("div", "space-y-3 sm:pl-12");
  wrap.append(row, results);
  els.messages.appendChild(wrap);
  return { bubble, results };
}

function pagesLabel(r) {
  if (r.page_start == null) return null;
  return r.page_start === r.page_end
    ? `Pág. ${r.page_start}`
    : `Págs. ${r.page_start}–${r.page_end}`;
}

function similarityBadge(sim) {
  const color = sim >= 0.6 ? "badge-success" : sim >= 0.4 ? "badge-warning" : "badge-ghost";
  return el("span", `badge ${color}`, `${Math.round(sim * 100)}% similar`);
}

function renderResult(r) {
  const card = el("div", "card bg-base-200 border border-base-300");
  const body = el("div", "card-body p-4 gap-2");

  const header = el("div", "flex flex-wrap items-center gap-2");
  header.appendChild(el("span", "badge badge-primary", r.filename));
  const pages = pagesLabel(r);
  if (pages) header.appendChild(el("span", "badge badge-ghost", pages));
  header.appendChild(similarityBadge(r.similarity));
  body.appendChild(header);

  const long = r.content.length > 300;
  const text = el("p", "text-sm whitespace-pre-wrap" + (long ? " line-clamp-4" : ""), r.content);
  body.appendChild(text);

  if (long) {
    const more = el("button", "btn btn-link btn-xs self-start px-0", "Ver más");
    more.type = "button";
    more.addEventListener("click", () => {
      const collapsed = text.classList.toggle("line-clamp-4");
      more.textContent = collapsed ? "Ver más" : "Ver menos";
    });
    body.appendChild(more);
  }

  card.appendChild(body);
  return card;
}

function setSearching(on) {
  els.input.disabled = on;
  els.sendBtn.disabled = on;
}

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = els.input.value.trim();
  if (!query) return;

  els.input.value = "";
  setSearching(true);
  addUserMessage(query);
  const { bubble, results } = addAssistantMessage();
  bubble.appendChild(el("span", "loading loading-dots loading-sm"));
  scrollDown();

  try {
    const data = await api("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, k: 5 }),
    });

    bubble.replaceChildren();
    if (!data.results.length) {
      bubble.textContent = "No encontré nada relevante en los documentos.";
    } else {
      const n = data.results.length;
      bubble.textContent = `Encontré ${n} ${n === 1 ? "fragmento relevante" : "fragmentos relevantes"}:`;
      data.results.forEach((r) => results.appendChild(renderResult(r)));
    }
  } catch (err) {
    bubble.replaceChildren();
    bubble.classList.add("chat-bubble-error");
    bubble.textContent = `Ocurrió un error: ${err.message}`;
  } finally {
    setSearching(false);
    scrollDown();
    els.input.focus();
  }
});

// ---------- Inicio ----------

loadDocuments();
els.input.focus();