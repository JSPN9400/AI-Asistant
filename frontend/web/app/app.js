const $ = (id) => document.getElementById(id);
let bearerToken = "";

function getConfig() {
  return {
    apiBaseUrl: $("apiBaseUrl").value.trim().replace(/\/$/, ""),
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

function setBadge(id, variant, text) {
  const element = $(id);
  element.className = `badge ${variant}`;
  element.textContent = text;
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

  container.innerHTML = cards.join("");
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

    const llm = system.llm || {};
    if (llm.available === "true") {
      setBadge("llmBadge", "badge-success", `${llm.provider}:${llm.model}`);
    } else {
      setBadge("llmBadge", "badge-warning", `${llm.provider}:fallback`);
    }

    setText("statusText", llm.message || `Connected to ${apiBaseUrl}`);
  } catch (error) {
    setBadge("apiBadge", "badge-danger", "OFFLINE");
    setBadge("llmBadge", "badge-danger", "UNKNOWN");
    setText("statusText", `Server unavailable: ${error.message}`);
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
    await Promise.all([refreshStatus(), loadPlugins(), loadHistory()]);
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
        context: {},
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Task request failed");
    }

    setBadge("taskBadge", "badge-success", "COMPLETED");
    setText(
      "resultSummary",
      `Task routed to ${data.task}. Output stored under task run ${data.task_id}.`
    );
    renderStructuredResult(data);
    setText("taskResult", JSON.stringify(data, null, 2));
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

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => runTask(button.dataset.prompt));
});

$("refreshStatusBtn").addEventListener("click", refreshStatus);
$("loginBtn").addEventListener("click", login);
$("runTaskBtn").addEventListener("click", () => runTask());
$("loadPluginsBtn").addEventListener("click", loadPlugins);
$("loadHistoryBtn").addEventListener("click", loadHistory);
$("uploadBtn").addEventListener("click", uploadFile);

updateMetrics();
refreshStatus();
loadPlugins();
loadHistory();
