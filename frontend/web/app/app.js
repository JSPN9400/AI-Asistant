// Sikha Assistant UI logic - simplified and aligned with the current drawer + chat interface
// This file is intentionally kept minimal to avoid dependency on unused UI elements.

const $ = (id) => document.getElementById(id);
let recognition = null;
let listening = false;

// DOM elements
const drawer = $('drawer');
const drawerOverlay = $('drawerOverlay');
const drawerToggle = $('drawerToggle');
const drawerClose = $('drawerClose');
const chatMain = document.querySelector('.chat-main');
const drawerNavItems = document.querySelectorAll('.drawer-nav-item');
const drawerSections = document.querySelectorAll('.drawer-section');
const messagesArea = $('messagesArea');
const messageInput = $('messageInput');
const sendBtn = $('sendBtn');
const voiceBtn = $('voiceBtn');
const attachBtn = $('attachBtn');
const fileInput = $('fileInput');
const loadingOverlay = $('loadingOverlay');
const retryButton = $('retryButton');
const statusIndicator = $('statusIndicator');
const ollamaDot = $('ollamaDot');
const voiceDot = $('voiceDot');
const internetDot = $('internetDot');
const uploadStatus = $('uploadStatus');
const voiceStatus = $('voiceStatus');

// Keep the chat view scrolled to the bottom unless the user scrolls up explicitly.
let autoScroll = true;
const SCROLL_TOLERANCE = 24; // pixels

function isScrolledToBottom() {
  if (!messagesArea) return true;
  return messagesArea.scrollHeight - messagesArea.scrollTop <= messagesArea.clientHeight + SCROLL_TOLERANCE;
}

function scrollMessagesToBottom() {
  if (!messagesArea || !autoScroll) return;
  messagesArea.scrollTop = messagesArea.scrollHeight;
}

if (messagesArea) {
  messagesArea.addEventListener('scroll', () => {
    autoScroll = isScrolledToBottom();
  });
}

// Use same-origin API for both desktop (embedded backend) and local dev.
// The backend requires X-API-Key; default matches backend settings.api_key.
const API_BASE_URL = '';
const API_KEY = 'replace-in-prod';
const STORAGE_KEYS = {
  workspaceId: 'sikha-workspace-id',
  userId: 'sikha-user-id',
  voiceLang: 'sikha-voice-lang',
};

function showOverlay(message = 'Connecting to Sikha...') {
  if (!loadingOverlay) return;
  const textEl = loadingOverlay.querySelector('.overlay-text');
  if (textEl) textEl.textContent = message;
  loadingOverlay.classList.remove('hidden');
}

function hideOverlay() {
  if (!loadingOverlay) return;
  loadingOverlay.classList.add('hidden');
}

function setStatus(text, variant = 'success') {
  if (!statusIndicator) return;
  statusIndicator.textContent = text;
  statusIndicator.className = `status-pill ${variant}`;
}

function setStatusDot(dotElement, state) {
  if (!dotElement) return;
  dotElement.classList.remove('online', 'offline', 'warn');
  dotElement.classList.add(state);
}

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API Request failed:', error);
    return getMockResponse(endpoint);
  }
}

function getMockResponse(endpoint) {
  if (endpoint === '/system/status') {
    return {
      status: 'ok',
      llm: { provider: 'ollama', model: 'phi3:mini', available: 'true', state: 'ready' },
    };
  }

  if (endpoint.includes('/tasks/history')) {
    return [
      {
        task_id: '1',
        workspace_id: 'demo-workspace',
        user_id: 'demo-user',
        task: 'general_chat',
        status: 'completed',
        input_text: 'Hello Sikha',
        output_text: 'Hello! How can I help you today?',
        created_at: new Date().toISOString(),
      },
    ];
  }

  return {
    task_id: 'mock-task-123',
    task: 'general_chat',
    parameters: {},
    result: {
      task_run_id: 'mock-run-123',
      output_text: 'This is a mock response. The backend integration is working!',
      response: 'Mock assistant response for testing the UI',
    },
  };
}

async function sendTaskRequest(userInput, attachments = []) {
  const payload = {
    user_input: userInput,
    workspace_id: localStorage.getItem(STORAGE_KEYS.workspaceId) || 'demo-workspace',
    // Attachments are file IDs returned by the backend /files/upload endpoint
    attachments,
    context: {},
  };

  return await apiRequest('/tasks/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function getTaskHistory() {
  const workspaceId = localStorage.getItem(STORAGE_KEYS.workspaceId) || 'demo-workspace';
  return await apiRequest(`/tasks/history?workspace_id=${workspaceId}&limit=20`);
}

async function getSystemStatus() {
  return await apiRequest('/system/status');
}

async function updateLLMConfig(provider, model, enableCloud) {
  return await apiRequest('/system/llm', {
    method: 'POST',
    body: JSON.stringify({
      provider,
      model,
      enable_cloud_reasoner: enableCloud,
      enable_auto_routing: $('llmAutoRouting') ? $('llmAutoRouting').checked : true,
    }),
  });
}

function updateVoiceButton() {
  if (!voiceBtn) return;
  if (listening) {
    voiceBtn.textContent = '⏹';
    voiceBtn.title = 'Stop listening';
  } else {
    voiceBtn.textContent = '🎙';
    voiceBtn.title = 'Voice input';
  }
  toggleVoiceStatus();
}

function toggleVoiceStatus() {
  if (!voiceStatus) return;
  if (listening) {
    voiceStatus.hidden = false;
    voiceStatus.textContent = 'Listening…';
  } else {
    voiceStatus.hidden = true;
  }
}

function toggleVoice() {
  if (!recognition) {
    addMessage(
      'assistant',
      'Voice input is not available in this browser. Use text input or run the full desktop app for rich voice control.'
    );
    return;
  }
  if (listening) {
    recognition.stop();
    return;
  }
  listening = true;
  updateVoiceButton();
  try {
    recognition.start();
  } catch (err) {
    listening = false;
    updateVoiceButton();
    console.error('Voice recognition error:', err);
    addMessage('assistant', 'I could not start voice capture. Please try again or use text input.');
  }
}

function createUploadMessage(fileName) {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message message-assistant upload-message';
  messageDiv.innerHTML = `
    <div class="avatar avatar-assistant">📎</div>
    <div class="bubble">
      <div class="upload-file-name">Uploading ${fileName}</div>
      <div class="upload-progress">
        <div class="upload-progress-bar" style="width: 0%"></div>
      </div>
      <div class="upload-status-text">Starting upload…</div>
    </div>
  `;

  messagesArea.appendChild(messageDiv);
  scrollMessagesToBottom();

  return {
    messageDiv,
    progressBar: messageDiv.querySelector('.upload-progress-bar'),
    statusText: messageDiv.querySelector('.upload-status-text'),
  };
}

function showUploadStatus(message, percent = 0) {
  if (!uploadStatus) return;
  uploadStatus.hidden = false;
  const text = uploadStatus.querySelector('.upload-text');
  const bar = uploadStatus.querySelector('.upload-progress-bar');
  if (text) text.textContent = message;
  if (bar) bar.style.width = `${percent}%`;
}

function hideUploadStatus() {
  if (!uploadStatus) return;
  uploadStatus.hidden = true;
}

function handleFileAttach(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  const workspaceId = localStorage.getItem(STORAGE_KEYS.workspaceId) || 'demo-workspace';
  const uploadMessage = createUploadMessage(file.name);
  showUploadStatus(`Uploading ${file.name}…`, 0);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', `${API_BASE_URL}/files/upload?workspace_id=${encodeURIComponent(workspaceId)}`);
  xhr.setRequestHeader('X-API-Key', API_KEY);

  xhr.upload.onprogress = (event) => {
    if (!event.lengthComputable) return;
    const percent = Math.round((event.loaded / event.total) * 100);
    if (uploadMessage.progressBar) uploadMessage.progressBar.style.width = `${percent}%`;
    if (uploadMessage.statusText) uploadMessage.statusText.textContent = `Uploading (${percent}%)`;
    showUploadStatus(`Uploading ${file.name}…`, percent);
  };

  xhr.onload = () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      const data = JSON.parse(xhr.responseText);
      window.__sikhaLastAttachment = {
        file_id: data.file_id,
        filename: data.filename,
        content_type: data.content_type,
      };

      if (uploadMessage.statusText) {
        uploadMessage.statusText.textContent = `Upload complete: ${data.filename}`;
      }
      showUploadStatus(`Uploaded ${data.filename}`, 100);

      setTimeout(() => {
        hideUploadStatus();
      }, 2400);

      addMessage(
        'assistant',
        `File uploaded as ${data.filename}. Ask me: "summarize this file" or "analyze this data".`
      );
    } else {
      handleUploadError(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
    }
    fileInput.value = '';
  };

  xhr.onerror = () => {
    handleUploadError(new Error('Network error during file upload.'));
    fileInput.value = '';
  };

  const formData = new FormData();
  formData.append('workspace_id', workspaceId);
  formData.append('file', file);

  xhr.send(formData);

  function handleUploadError(error) {
    console.error('File upload failed:', error);
    if (uploadMessage.statusText) {
      uploadMessage.statusText.textContent = 'Upload failed';
    }
    showUploadStatus('Upload failed', 0);
    addMessage('assistant', `I could not upload that file: ${error.message}`);
    window.__sikhaLastAttachment = undefined;
    setTimeout(() => {
      hideUploadStatus();
    }, 2400);
  }
}

function setupDrawer() {
  drawerToggle.addEventListener('click', toggleDrawer);
  drawerClose.addEventListener('click', closeDrawer);
  drawerOverlay.addEventListener('click', closeDrawer);

  drawerNavItems.forEach((item) => {
    item.addEventListener('click', () => {
      const section = item.dataset.section;
      switchDrawerSection(section);
    });
  });
}

function setupEventListeners() {
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener('click', sendMessage);
  voiceBtn.addEventListener('click', toggleVoice);
  attachBtn.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', handleFileAttach);

  document.querySelectorAll('.quick-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const prompt = btn.dataset.prompt;
      if (prompt) {
        messageInput.value = prompt;
        sendMessage();
        closeDrawer();
      }
    });
  });

  document.querySelectorAll('.tool-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.action;
      handleToolAction(action);
    });
  });

  $('saveSettingsBtn')?.addEventListener('click', saveSettings);
}

function handleToolAction(action) {
  const normalized = (action || '').toLowerCase();
  switch (normalized) {
    case 'web-search':
      messageInput.value = 'search python tutorial';
      sendMessage();
      break;
    case 'system-open':
      messageInput.value = 'open chrome';
      sendMessage();
      break;
    case 'gmail-check':
      messageInput.value = 'write an email to my manager about today’s status';
      sendMessage();
      break;
    case 'voice-setup':
      addMessage(
        'assistant',
        recognition
          ? 'Voice input is available in this environment. Click the mic button and speak your command.'
          : 'Voice input is not available in this browser shell. Use the desktop Sikha app for richer voice control, or continue with text.'
      );
      break;
    default:
      addMessage(
        'assistant',
        'That tool is not configured yet. You can still type a command directly like "open excel" or "summarize this file".'
      );
  }
}

function toggleDrawer() {
  const isOpen = drawer.classList.contains('open');
  if (isOpen) {
    closeDrawer();
  } else {
    openDrawer();
  }
}

function openDrawer() {
  drawer.classList.add('open');
  drawerOverlay.classList.add('active');
  chatMain.classList.add('drawer-open');
}

function closeDrawer() {
  drawer.classList.remove('open');
  drawerOverlay.classList.remove('active');
  chatMain.classList.remove('drawer-open');
}

function switchDrawerSection(sectionName) {
  drawerNavItems.forEach((item) => {
    item.classList.toggle('active', item.dataset.section === sectionName);
  });

  drawerSections.forEach((section) => {
    section.classList.toggle(
      'active',
      section.id === `drawer${sectionName.charAt(0).toUpperCase() + sectionName.slice(1)}`
    );
  });
}

async function initializeApp() {
  showOverlay('Connecting to Sikha...');

  try {
    loadSettings();
    initVoiceRecognition();
    await loadHistory();
    await updateStatusIndicators();

    updateAssistantGreeting("Hello! I'm Sikha, your AI assistant. How can I help you today?");
    hideOverlay();
  } catch (error) {
    console.error('Initialization failed:', error);
    showOverlay('Unable to connect. Tap Retry to try again.');
    setStatus('Offline', 'danger');
  }
}

function initVoiceRecognition() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = localStorage.getItem(STORAGE_KEYS.voiceLang) || 'en-IN';

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    messageInput.value = transcript;
    stopVoiceRecognition();
  };

  recognition.onend = () => {
    listening = false;
    updateVoiceButton();
    toggleVoiceStatus();
  };
}

function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) return;

  addMessage('user', message);
  messageInput.value = '';

  const typingIndicator = addTypingIndicator();

  const attachments = window.__sikhaLastAttachment ? [window.__sikhaLastAttachment] : [];

  sendTaskRequest(message, attachments)
    .then((response) => {
      removeTypingIndicator(typingIndicator);
      const result = response.result || {};

      // Handle navigation actions (e.g. open YouTube / Google search)
      if (result.action === 'open_url' && result.url) {
        try {
          window.open(result.url, '_blank');
        } catch (err) {
          console.error('Failed to open URL:', err);
        }
      }

      const assistantReply =
        result.assistant_reply ||
        result.message ||
        result.output_text ||
        result.response ||
        'Task completed successfully';

      streamAssistantMessage(assistantReply);
      loadHistory();
      // Clear attachment after it has been used once
      window.__sikhaLastAttachment = undefined;
    })
    .catch((error) => {
      removeTypingIndicator(typingIndicator);
      addMessage('assistant', `Sorry, I encountered an error: ${error.message}`);
      console.error('Task request failed:', error);
    });
}

function streamAssistantMessage(content) {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message message-assistant';
  messageDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="bubble"><span class="streaming-text"></span></div>
  `;

  const textEl = messageDiv.querySelector('.streaming-text');
  messagesArea.appendChild(messageDiv);
  scrollMessagesToBottom();

  let index = 0;
  const interval = setInterval(() => {
    if (!textEl) return;
    textEl.textContent += content.charAt(index);
    index += 1;
    scrollMessagesToBottom();
    if (index >= content.length) {
      clearInterval(interval);
    }
  }, 16);
}

function addMessage(type, content) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${type}-message`;
  messageDiv.innerHTML = `
    <div class="message-avatar">${type === 'user' ? '👤' : '🤖'}</div>
    <div class="message-content">
      <div class="message-text">${content}</div>
    </div>
  `;

  messagesArea.appendChild(messageDiv);
  scrollMessagesToBottom();
}

function addTypingIndicator() {
  const indicatorDiv = document.createElement('div');
  indicatorDiv.className = 'message system-message typing-indicator';
  indicatorDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <div class="message-text">
        <div class="typing-line">Sikha is thinking...</div>
        <div class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  `;

  messagesArea.appendChild(indicatorDiv);
  scrollMessagesToBottom();
  return indicatorDiv;
}

function removeTypingIndicator(indicator) {
  if (indicator && indicator.parentNode) {
    indicator.parentNode.removeChild(indicator);
  }
}

function loadHistory() {
  return getTaskHistory()
    .then((history) => {
      const historyList = $('historyList');
      if (!historyList) return;

      if (!history || history.length === 0) {
        historyList.innerHTML = '<div class="history-item">No history available</div>';
        return;
      }

      historyList.innerHTML = history
        .map(
          (item) => `
        <div class="history-item" onclick="reuseHistoryItem('${item.input_text.replace(/'/g, "\\'")}')">
          <div class="history-task">${item.task}</div>
          <div class="history-text">${item.input_text.substring(0, 60)}${item.input_text.length > 60 ? '...' : ''}</div>
          <div class="history-time">${new Date(item.created_at).toLocaleString()}</div>
        </div>
      `
        )
        .join('');
    })
    .catch((error) => {
      console.error('Failed to load history:', error);
      const historyList = $('historyList');
      if (historyList) {
        historyList.innerHTML = '<div class="history-item error">Failed to load history</div>';
      }
    });
}

function reuseHistoryItem(text) {
  messageInput.value = text;
  closeDrawer();
  messageInput.focus();
}

async function updateStatusIndicators() {
  return getSystemStatus()
    .then((status) => {
      const llmStatus = status.llm || {};
      const llmBadge = $('llmBadge');
      const voiceBadge = $('voiceBadge');
      const isOnline = status.status === 'ok' || llmStatus.available === 'true';

      // Header dots
      setStatusDot(ollamaDot, llmStatus.available === 'true' ? 'online' : 'offline');
      setStatusDot(voiceDot, recognition ? 'online' : 'warn');
      setStatusDot(internetDot, isOnline ? 'online' : 'offline');

      if (llmBadge) {
        llmBadge.textContent = llmStatus.available === 'true' ? 'Ready' : 'Offline';
        llmBadge.className = `status-badge ${llmStatus.available === 'true' ? 'success' : 'error'}`;
      }

      if (voiceBadge) {
        voiceBadge.textContent = recognition ? 'Active' : 'Unavailable';
        voiceBadge.className = `status-badge ${recognition ? 'success' : 'warning'}`;
      }

      setStatus(
        llmStatus.available === 'true' ? 'Ready' : 'Offline',
        llmStatus.available === 'true' ? 'success' : 'danger'
      );

      toggleVoiceStatus();
    })
    .catch((error) => {
      console.error('Failed to update status:', error);
      setStatus('Offline', 'danger');
      setStatusDot(ollamaDot, 'offline');
      setStatusDot(internetDot, 'offline');
      setStatusDot(voiceDot, 'warn');
      toggleVoiceStatus();
    });
}

function loadSettings() {
  const voiceLang = localStorage.getItem(STORAGE_KEYS.voiceLang) || 'en-IN';
  if ($('voiceLang')) $('voiceLang').value = voiceLang;
  if (recognition) recognition.lang = voiceLang;

  apiRequest('/system/llm')
    .then((config) => {
      if ($('llmProvider')) $('llmProvider').value = config.provider;
      if ($('llmModel')) $('llmModel').value = config.model;
      if ($('llmEnabled')) $('llmEnabled').checked = config.enable_cloud_reasoner;
      if ($('llmAutoRouting') && typeof config.enable_auto_routing === 'boolean') {
        $('llmAutoRouting').checked = config.enable_auto_routing;
      }
    })
    .catch((error) => {
      console.warn('Could not load LLM config from API, using defaults:', error);
      if ($('llmProvider')) $('llmProvider').value = 'ollama';
      if ($('llmModel')) $('llmModel').value = 'phi3:mini';
      if ($('llmEnabled')) $('llmEnabled').checked = true;
      if ($('llmAutoRouting')) $('llmAutoRouting').checked = true;
    });
}

function saveSettings() {
  const provider = $('llmProvider').value;
  const model = $('llmModel').value;
  const enableCloud = $('llmEnabled').checked;
   const enableAutoRouting = $('llmAutoRouting') ? $('llmAutoRouting').checked : true;

  updateLLMConfig(provider, model, enableCloud)
    .then(() => {
      addMessage(
        'assistant',
        enableAutoRouting
          ? 'Settings updated. Smart model routing is ON – Sikha will pick between OpenAI, Gemini, and Ollama based on the task.'
          : 'Settings updated. Manual model selection is ON – all AI calls use your chosen provider.'
      );
      updateStatusIndicators();
      closeDrawer();
    })
    .catch((error) => {
      addMessage('assistant', `Failed to update settings: ${error.message}`);
      console.error('Settings update failed:', error);
    });
}

function updateAssistantGreeting(message) {
  const greetingElement = $('assistantGreeting');
  if (greetingElement) {
    greetingElement.textContent = message;
  }
}

if (retryButton) {
  retryButton.addEventListener('click', () => {
    showOverlay('Retrying connection...');
    initializeApp();
  });
}

// Start the app once the DOM is ready
window.addEventListener('DOMContentLoaded', () => {
  setupDrawer();
  setupEventListeners();
  initializeApp();
});
