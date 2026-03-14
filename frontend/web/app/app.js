const $ = (id) => document.getElementById(id);
let bearerToken = "";
let recognition = null;
let listening = false;
let currentMode = "chat";
const MODEL_PRESETS = {
  ollama: "phi3:mini",
  openai: "gpt-4.1-mini",
  gemini: "gemini-2.0-flash",
};

const MODES = {
  chat: {
    headline: "Chat naturally with Sikha for general questions and quick help",
    description: "Use Chat Mode for open-ended conversation, knowledge questions, and normal assistant interactions.",
    title: "Chat Mode",
    badge: "General assistant",
    hint: "Ask normal questions, clarify ideas, or talk naturally with the assistant.",
    focusTitle: "Chat Focus",
    focusBadge: "Conversation",
    composerTitle: "Chat Composer",
    composerLabel: "Ask Sikha",
    composerBadge: "Conversational AI",
    composerButton: "Send",
    placeholder: "Who is the prime minister of India?",
    uploadVisible: false,
    uploadTitle: "Reference Files",
    attachmentsVisible: false,
    resultTitle: "Assistant Reply",
    historyTitle: "Chat History",
    signalTitle: "Chat signals",
    focusItems: [
      "Handles natural questions, ideas, clarifications, and follow-up discussion.",
      "Best when the user expects a direct answer, not a formal office document.",
      "Uses the LLM as a general assistant before forcing a workflow plugin.",
    ],
    signals: [
      "Preferred input: plain-language question",
      "Typical output: answer, explanation, recommendation",
      "Voice use: optional",
    ],
    prompts: [
      "Who is the prime minister of India?",
      "What can you do?",
      "Explain FMCG distribution in simple words.",
    ],
  },
  live: {
    headline: "Use live mode for fast voice prompts and real-time actions",
    description: "Use Live Mode when you want quick voice-first assistance, instant web actions, and short command-style prompts.",
    title: "Live Mode",
    badge: "Voice and action flow",
    hint: "Best for spoken commands, quick web opens, and live responses.",
    focusTitle: "Live Focus",
    focusBadge: "Realtime",
    composerTitle: "Live Prompt",
    composerLabel: "Say or type a live command",
    composerBadge: "Real-time assistant",
    composerButton: "Run Live",
    placeholder: "open youtube",
    uploadVisible: false,
    uploadTitle: "Reference Files",
    attachmentsVisible: false,
    resultTitle: "Live Result",
    historyTitle: "Recent Live Actions",
    signalTitle: "Live signals",
    focusItems: [
      "Optimized for short spoken commands and instant action-style prompts.",
      "Keeps the voice button primary so the app feels like a live assistant.",
      "Useful for search, open, play, and quick hands-free requests.",
    ],
    signals: [
      "Preferred input: voice or short command",
      "Typical output: quick reply, link, or action suggestion",
      "Voice use: primary",
    ],
    prompts: [
      "open youtube",
      "google pe python tutorial search karo",
      "play on youtube lofi music",
    ],
  },
  office: {
    headline: "Office mode focuses on reports, summaries, drafts, and work files",
    description: "Use Office Mode for productivity tasks across sales, operations, admin, and support workflows.",
    title: "Office Mode",
    badge: "Work automation",
    hint: "Best for reports, meeting notes, email drafting, and spreadsheet analysis.",
    focusTitle: "Office Focus",
    focusBadge: "Productivity",
    composerTitle: "Office Task",
    composerLabel: "Office request",
    composerBadge: "Productivity mode",
    composerButton: "Run Task",
    placeholder: "Create a weekly sales report from this data.",
    uploadVisible: true,
    uploadTitle: "Workspace Files",
    attachmentsVisible: true,
    resultTitle: "Work Output",
    historyTitle: "Task History",
    signalTitle: "Office signals",
    focusItems: [
      "Routes into report, summary, drafting, analysis, and workplace plugins.",
      "Keeps file upload and attachment flow visible for data-backed tasks.",
      "Best for workers in sales, FMCG, operations, and office support roles.",
    ],
    signals: [
      "Preferred input: structured work request",
      "Typical output: report, summary, draft, action items",
      "Voice use: optional",
    ],
    prompts: [
      "Create a weekly sales report from this data.",
      "Summarize these meeting notes and extract action items.",
      "Draft a client response for delayed dispatch.",
    ],
  },
};

function getConfig() {
  const enteredApiBaseUrl = $("apiBaseUrl").value.trim().replace(/\/$/, "");
  return {
    apiBaseUrl: enteredApiBaseUrl || window.location.origin.replace(/\/$/, ""),
    apiKey: $("apiKey").value.trim(),
    userId: $("userId").value.trim(),
    workspaceId: $("workspaceId").value.trim(),
  };
}

function authHeaders(includeJson = true) {
  const config = getConfig();
  return {
    ...(includeJson ? { "Content-Type": "application/json" } : {}),
    ...(bearerToken
      ? { Authorization: `Bearer ${bearerToken}` }
      : {
          "x-api-key": config.apiKey,
          "x-user-id": config.userId,
          "x-workspace-id": config.workspaceId,
        }),
  };
}

function setText(id, value) {
  $(id).textContent = value;
}

function setValue(id, value) {
  $(id).value = value;
}

function setBadge(id, variant, text) {
  const element = $(id);
  element.className = `badge ${variant}`;
  element.textContent = text;
}

function badgeVariantForLLMState(state, available) {
  if (state === "ready") {
    return "badge-success";
  }
  if (state === "exhausted" || state === "missing_key" || available === "false") {
    return "badge-warning";
  }
  if (state === "offline" || state === "package_missing") {
    return "badge-danger";
  }
  return "badge-muted";
}

function syncLLMControls(llm) {
  if (!llm) {
    return;
  }
  setValue("llmProvider", llm.provider || "ollama");
  setValue("llmModel", llm.model || MODEL_PRESETS[llm.provider] || MODEL_PRESETS.ollama);
  $("llmEnabled").checked = llm.state !== "disabled";
}

function applyLLMStatus(llm) {
  if (!llm) {
    return;
  }

  const providerLabel = `${llm.provider}:${llm.model}`;
  const stateLabel = (llm.state || "unknown").replace(/_/g, " ").toUpperCase();
  const stateVariant = badgeVariantForLLMState(llm.state, llm.available);

  setBadge("llmStateBadge", stateVariant, stateLabel);
  if (llm.state === "ready") {
    setBadge("llmBadge", "badge-success", providerLabel);
    updateModelStatus(`Connected to ${llm.provider} / ${llm.model}.`);
  } else if (llm.state === "disabled") {
    setBadge("llmBadge", "badge-muted", providerLabel);
    updateModelStatus(llm.message || "Cloud reasoner is disabled.");
  } else {
    setBadge("llmBadge", stateVariant, providerLabel);
    updateModelStatus(llm.message || `Model unavailable for ${llm.provider}.`);
  }

  setText("statusText", llm.message || "LLM status updated.");
  syncLLMControls(llm);
}

function updateGreeting(text) {
  $("assistantGreeting").textContent = text;
}

function updateModelStatus(text) {
  $("modelStatus").textContent = text;
}

function renderModePrompts(mode) {
  $("modeQuickGrid").innerHTML = MODES[mode].prompts
    .map(
      (prompt) => `
        <button class="quick-prompt" data-mode-prompt="${prompt.replace(/"/g, "&quot;")}">${prompt}</button>
      `
    )
    .join("");

  document.querySelectorAll("[data-mode-prompt]").forEach((button) => {
    button.addEventListener("click", () => runTask(button.dataset.modePrompt));
  });
}

function renderModeDetails(mode) {
  const config = MODES[mode];
  $("modeFocusTitle").textContent = config.focusTitle;
  $("modeFocusBadge").textContent = config.focusBadge;
  $("modeFocusList").innerHTML = config.focusItems
    .map((item) => `<div class="focus-item">${item}</div>`)
    .join("");

  $("modeSignalList").innerHTML = config.signals
    .map(
      (item) => `
        <div class="signal-item">
          <strong>${config.signalTitle}</strong>
          <span>${item}</span>
        </div>
      `
    )
    .join("");
}

function applyMode(mode) {
  currentMode = mode;
  const config = MODES[mode];

  $("modeHeadline").textContent = config.headline;
  $("modeDescription").textContent = config.description;
  $("modeTitle").textContent = config.title;
  $("modeBadge").textContent = config.badge;
  $("modeHint").textContent = config.hint;
  $("composerTitle").textContent = config.composerTitle;
  $("composerLabel").childNodes[0].textContent = config.composerLabel;
  $("composerBadge").textContent = config.composerBadge;
  $("runTaskBtn").textContent = config.composerButton;
  $("taskInput").placeholder = config.placeholder;
  $("uploadCard").style.display = config.uploadVisible ? "block" : "none";
  $("attachmentsLabel").style.display = config.attachmentsVisible ? "block" : "none";
  $("uploadTitle").textContent = config.uploadTitle;
  $("resultTitle").textContent = config.resultTitle;
  $("historyTitle").textContent = config.historyTitle;
  $("voiceBtn").classList.toggle("voice-primary", mode === "live");
  $("runTaskBtn").classList.toggle("ghost", mode === "live");

  document.querySelectorAll(".mode-chip").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.mode === mode);
  });

  renderModePrompts(mode);
  renderModeDetails(mode);
  updateGreeting(`Switched to ${config.title}. ${config.hint}`);
}

function parseAttachments() {
  return $("attachmentsInput").value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function updateMetrics({ historyCount = null, pluginCount = null } = {}) {
  $("metricWorkspace").textContent = getConfig().workspaceId || "demo";
  if (historyCount !== null) {
    $("metricTaskCount").textContent = String(historyCount);
  }
  if (pluginCount !== null) {
    $("metricPluginCount").textContent = String(pluginCount);
  }
}

function renderStructuredResult(data) {
  const container = $("resultStructured");
  $("actionPanel").innerHTML = "";
  const result = data.result || {};
  const cards = [];

  cards.push(`
    <div class="structured-card">
      <strong>Routed Task</strong>
      <div>${data.task || "unknown"}</div>
      <code>${JSON.stringify(data.parameters || {})}</code>
    </div>
  `);

  if (result.highlights?.length) {
    cards.push(`
      <div class="structured-card">
        <strong>Highlights</strong>
        <div>${result.highlights.join(" | ")}</div>
      </div>
    `);
  }

  if (result.action_items?.length || result.recommended_actions?.length) {
    const actions = result.action_items || result.recommended_actions;
    cards.push(`
      <div class="structured-card">
        <strong>Actions</strong>
        <div>${actions.join(" | ")}</div>
      </div>
    `);
  }

  if (result.insights?.length) {
    cards.push(`
      <div class="structured-card">
        <strong>Insights</strong>
        <div>${result.insights.join(" | ")}</div>
      </div>
    `);
  }

  if (result.url) {
    cards.push(`
      <div class="structured-card">
        <strong>Action URL</strong>
        <div>${result.url}</div>
      </div>
    `);
    $("actionPanel").innerHTML = `
      <a class="action-link" href="${result.url}" target="_blank" rel="noopener">Open Result Link</a>
    `;
  }

  container.innerHTML = cards.join("");
}

function summarizeForSpeech(data) {
  const result = data.result || {};
  return (
    result.assistant_reply ||
    result.message ||
    result.report ||
    (result.summary && result.summary.join(". ")) ||
    (result.insights && result.insights.join(". ")) ||
    `Task ${data.task} completed.`
  );
}

function summarizeForDisplay(data) {
  const result = data.result || {};
  if (result.assistant_reply) {
    return result.assistant_reply;
  }
  if (result.message) {
    return result.message;
  }
  if (result.report) {
    return "Report generated successfully.";
  }
  if (result.summary?.length) {
    return result.summary.join(" ");
  }
  if (result.insights?.length) {
    return result.insights.join(" ");
  }
  return `Handled ${data.task}.`;
}

function speakText(text) {
  const synth = window.speechSynthesis;
  if (!synth || !text) {
    return;
  }
  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  synth.speak(utterance);
}

function executeClientAction(data) {
  const result = data.result || {};
  if (result.action === "open_url" && result.url) {
    const newWindow = window.open(result.url, "_blank", "noopener");
    if (!newWindow) {
      updateGreeting("Popup blocked. Use the Open Result Link button.");
    }
  }
}

async function refreshStatus() {
  const { apiBaseUrl } = getConfig();
  try {
    const healthResponse = await fetch(`${apiBaseUrl}/health`);
    const health = await healthResponse.json();
    if (!healthResponse.ok) {
      throw new Error(health.detail || "Healthcheck failed");
    }

    const systemResponse = await fetch(`${apiBaseUrl}/system/status`);
    const system = await systemResponse.json();
    if (!systemResponse.ok) {
      throw new Error(system.detail || "System status failed");
    }

    setBadge("apiBadge", "badge-success", health.status.toUpperCase());
    setBadge("authBadge", bearerToken ? "badge-success" : "badge-warning", bearerToken ? "Bearer" : "API key");
    applyLLMStatus(system.llm || {});
  } catch (error) {
    setBadge("apiBadge", "badge-danger", "OFFLINE");
    setBadge("llmBadge", "badge-danger", "UNKNOWN");
    setBadge("llmStateBadge", "badge-danger", "OFFLINE");
    updateModelStatus("Model status unavailable because the server is offline.");
    setText("statusText", `Server unavailable: ${error.message}`);
  }
}

async function loadLLMConfiguration() {
  const config = getConfig();
  try {
    const response = await fetch(`${config.apiBaseUrl}/system/llm`, {
      headers: authHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Could not load LLM configuration");
    }
    syncLLMControls(data.status);
    applyLLMStatus(data.status);
  } catch (error) {
    setText("statusText", `LLM configuration load failed: ${error.message}`);
  }
}

async function saveLLMConfiguration() {
  const config = getConfig();
  const provider = $("llmProvider").value;
  const model = $("llmModel").value.trim() || MODEL_PRESETS[provider] || MODEL_PRESETS.ollama;
  const enableCloudReasoner = $("llmEnabled").checked;

  try {
    const response = await fetch(`${config.apiBaseUrl}/system/llm`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        provider,
        model,
        enable_cloud_reasoner: enableCloudReasoner,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Could not update LLM configuration");
    }
    syncLLMControls(data.status);
    applyLLMStatus(data.status);
    updateGreeting(`LLM switched to ${data.provider} / ${data.model}.`);
  } catch (error) {
    setText("statusText", `LLM update failed: ${error.message}`);
  }
}

async function checkLLMConfiguration() {
  const config = getConfig();
  setText("statusText", "Running a tiny LLM health check...");
  try {
    const response = await fetch(`${config.apiBaseUrl}/system/llm/check`, {
      method: "POST",
      headers: authHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Could not check LLM configuration");
    }
    applyLLMStatus(data);
  } catch (error) {
    setText("statusText", `LLM health check failed: ${error.message}`);
  }
}

async function login() {
  const config = getConfig();
  const email = $("loginEmail").value.trim();
  const password = $("loginPassword").value;
  if (!email || !password || !config.workspaceId) {
    setText("statusText", "Provide email, password, and workspace ID.");
    return;
  }

  try {
    const response = await fetch(`${config.apiBaseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        workspace_id: config.workspaceId,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Login failed");
    }

    bearerToken = data.access_token;
    $("userId").value = data.user_id;
    $("workspaceId").value = data.workspace_id;
    setBadge("authBadge", "badge-success", `Bearer:${data.role}`);
    setText("statusText", `Signed in as ${data.user_id} in ${data.workspace_id}.`);
    await Promise.all([refreshStatus(), loadPlugins(), loadHistory(), loadLLMConfiguration()]);
  } catch (error) {
    bearerToken = "";
    setBadge("authBadge", "badge-danger", "Login failed");
    setText("statusText", `Login failed: ${error.message}`);
  }
}

async function runTask(promptText) {
  const config = getConfig();
  const userInput = promptText || $("taskInput").value.trim();
  if (!userInput) {
    setText("resultSummary", "Enter a task request first.");
    return;
  }

  $("taskInput").value = userInput;
  setBadge("taskBadge", "badge-warning", "RUNNING");
  setText("resultSummary", "Routing task through the assistant...");
  setText("taskResult", "Running task...");
  $("resultStructured").innerHTML = "";

  try {
    const response = await fetch(`${config.apiBaseUrl}/tasks/`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        user_input: userInput,
        workspace_id: config.workspaceId,
        attachments: parseAttachments(),
        context: {
          ui_mode: currentMode,
          mode_title: MODES[currentMode].title,
        },
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Task request failed");
    }

    setBadge("taskBadge", "badge-success", "COMPLETED");
    setText("resultSummary", summarizeForDisplay(data));
    updateGreeting(summarizeForDisplay(data));
    renderStructuredResult(data);
    setText("taskResult", JSON.stringify(data, null, 2));
    executeClientAction(data);
    speakText(summarizeForSpeech(data));
    await loadHistory();
  } catch (error) {
    setBadge("taskBadge", "badge-danger", "FAILED");
    setText("resultSummary", `Task failed: ${error.message}`);
    setText("taskResult", `Task failed: ${error.message}`);
  }
}

async function loadPlugins() {
  const config = getConfig();
  const container = $("pluginList");
  container.innerHTML = "Loading plugins...";
  try {
    const response = await fetch(`${config.apiBaseUrl}/plugins/`, {
      headers: authHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Could not load plugins");
    }

    updateMetrics({ pluginCount: data.length });
    container.innerHTML = data
      .map(
        (plugin) => `
          <div class="plugin-item">
            <strong>${plugin.name}</strong>
            <div>${plugin.description}</div>
            <div class="muted">Actions: ${plugin.supported_actions.join(", ")}</div>
            <div class="muted">Inputs: ${(plugin.input_fields || []).join(", ") || "none"}</div>
          </div>
        `
      )
      .join("");
  } catch (error) {
    container.textContent = `Plugin load failed: ${error.message}`;
  }
}

async function loadHistory() {
  const config = getConfig();
  const container = $("historyList");
  container.innerHTML = "Loading history...";
  try {
    const response = await fetch(
      `${config.apiBaseUrl}/tasks/history?workspace_id=${encodeURIComponent(config.workspaceId)}&limit=12`,
      { headers: authHeaders() }
    );
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Could not load history");
    }

    updateMetrics({ historyCount: data.length });
    if (!data.length) {
      container.textContent = "No task history yet.";
      return;
    }

    container.innerHTML = data
      .map(
        (item) => `
          <div class="history-item">
            <strong>${item.task}</strong>
            <div>${item.input_text}</div>
            <div class="muted">${item.created_at} | ${item.status}</div>
          </div>
        `
      )
      .join("");
  } catch (error) {
    container.textContent = `History load failed: ${error.message}`;
  }
}

async function uploadFile() {
  const config = getConfig();
  const file = $("fileInput").files[0];
  if (!file) {
    setText("uploadResult", "Choose a file first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  setText("uploadResult", "Uploading...");

  try {
    const response = await fetch(
      `${config.apiBaseUrl}/files/upload?workspace_id=${encodeURIComponent(config.workspaceId)}`,
      {
        method: "POST",
        headers: authHeaders(false),
        body: formData,
      }
    );
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Upload failed");
    }

    $("attachmentsInput").value = data.file_id;
    setText("uploadResult", `Uploaded ${data.filename}. Attachment ID: ${data.file_id}`);
  } catch (error) {
    setText("uploadResult", `Upload failed: ${error.message}`);
  }
}

function setupVoiceRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    $("voiceBtn").disabled = true;
    $("voiceBtn").textContent = "Voice Unavailable";
    updateGreeting("Voice input is unavailable in this browser. Use Chrome or Edge.");
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = $("voiceLang").value || "en-IN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    listening = true;
    $("voiceBtn").textContent = "Listening...";
    setBadge("taskBadge", "badge-active", "VOICE");
    updateGreeting("Listening for your command.");
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript.trim();
    $("taskInput").value = transcript;
    updateGreeting(`Heard: ${transcript}`);
    runTask(transcript);
  };

  recognition.onerror = (event) => {
    updateGreeting(`Voice input failed: ${event.error}`);
  };

  recognition.onend = () => {
    listening = false;
    $("voiceBtn").textContent = "Start Voice";
    if ($("taskBadge").textContent === "VOICE") {
      setBadge("taskBadge", "badge-muted", "IDLE");
    }
  };

  $("voiceLang").addEventListener("change", () => {
    if (recognition && !listening) {
      recognition.lang = $("voiceLang").value || "en-IN";
    }
  });
}

function toggleVoiceRecognition() {
  if (!recognition) {
    return;
  }
  if (listening) {
    recognition.stop();
    return;
  }
  recognition.start();
}

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => runTask(button.dataset.prompt));
});

document.querySelectorAll(".mode-chip").forEach((button) => {
  button.addEventListener("click", () => applyMode(button.dataset.mode));
});

$("refreshStatusBtn").addEventListener("click", refreshStatus);
$("loginBtn").addEventListener("click", login);
$("runTaskBtn").addEventListener("click", () => runTask());
$("voiceBtn").addEventListener("click", toggleVoiceRecognition);
$("loadPluginsBtn").addEventListener("click", loadPlugins);
$("loadHistoryBtn").addEventListener("click", loadHistory);
$("uploadBtn").addEventListener("click", uploadFile);
$("saveLlmBtn").addEventListener("click", saveLLMConfiguration);
$("checkLlmBtn").addEventListener("click", checkLLMConfiguration);
$("llmProvider").addEventListener("change", () => {
  const provider = $("llmProvider").value;
  if (!$("llmModel").value.trim() || $("llmModel").value === MODEL_PRESETS.openai || $("llmModel").value === MODEL_PRESETS.ollama || $("llmModel").value === MODEL_PRESETS.gemini) {
    setValue("llmModel", MODEL_PRESETS[provider] || MODEL_PRESETS.ollama);
  }
});

updateMetrics();
setupVoiceRecognition();
applyMode(currentMode);
updateGreeting("Hello. I am ready for typed or voice commands.");
speakText("Hello. I am ready.");
refreshStatus();
loadLLMConfiguration();
loadPlugins();
loadHistory();






