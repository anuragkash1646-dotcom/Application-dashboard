/**
 * Application Layer Activity & Protocol Visualizer
 * Vanilla ES6 JavaScript Controller & WebSocket Client
 */

class ProtocolVisualizerApp {
  constructor() {
    this.ws = null;
    this.state = {
      activity_type: "web",
      is_playing: false,
      current_step: 1,
      total_steps: 0,
      events: [],
      playback_speed: 1.0,
      hls_buffer_sec: 0.0,
      activity_log: []
    };
    this.reconnectTimeout = null;

    this.initElements();
    this.bindEvents();
    this.connectWebSocket();
  }

  initElements() {
    // Header
    this.connectionStatus = document.getElementById("connection-status");
    this.connectionLabel = document.getElementById("connection-label");
    this.currentActivityBadge = document.getElementById("current-activity-badge");
    this.stepCounterText = document.getElementById("step-counter-text");

    // Tabs & Forms
    this.tabButtons = document.querySelectorAll(".tab-btn");
    this.activityForms = document.querySelectorAll(".activity-form");
    this.formWeb = document.getElementById("form-web");
    this.formSmtp = document.getElementById("form-smtp");
    this.formHls = document.getElementById("form-hls");

    // Inputs
    this.webUrlInput = document.getElementById("web-url");
    this.presetTags = document.querySelectorAll(".preset-tag");
    this.smtpSender = document.getElementById("smtp-sender");
    this.smtpRecipient = document.getElementById("smtp-recipient");
    this.smtpSubject = document.getElementById("smtp-subject");
    this.smtpBody = document.getElementById("smtp-body");
    this.hlsStream = document.getElementById("hls-stream");
    this.hlsBitrate = document.getElementById("hls-bitrate");

    // Video Mock & Buffer Meter
    this.videoScreen = document.getElementById("video-screen");
    this.videoResDisplay = document.getElementById("video-res-display");
    this.videoSegmentLabel = document.getElementById("video-segment-label");
    this.videoCenterIcon = document.getElementById("video-center-icon");
    this.bufferMeterFill = document.getElementById("buffer-meter-fill");
    this.bufferValText = document.getElementById("buffer-val-text");

    // Activity Log
    this.activityLogList = document.getElementById("activity-log-list");
    this.btnClearLog = document.getElementById("btn-clear-log");

    // Flow Stage
    this.clientNode = document.getElementById("client-node");
    this.serverNode = document.getElementById("server-node");
    this.serverNameText = document.getElementById("server-name-text");
    this.serverRoleText = document.getElementById("server-role-text");
    this.serverEndpointText = document.getElementById("server-endpoint-text");
    this.clientEndpointText = document.getElementById("client-endpoint-text");
    this.flowProtoBadge = document.getElementById("flow-proto-badge");
    this.flowDirBadge = document.getElementById("flow-dir-badge");
    this.flowStateBadge = document.getElementById("flow-state-badge");
    this.animatedPacket = document.getElementById("animated-packet");
    this.packetArrow = document.getElementById("packet-arrow");
    this.packetLabel = document.getElementById("packet-label");
    this.wirePortLabel = document.getElementById("wire-port-label");
    this.eventSummaryText = document.getElementById("event-summary-text");

    // Inspector
    this.inspectorTabs = document.querySelectorAll(".inspector-tab");
    this.inspectorViews = document.querySelectorAll(".inspector-view");
    this.wireDataPre = document.getElementById("wire-data-pre");
    this.metadataTbody = document.getElementById("metadata-tbody");
    this.payloadPreviewContent = document.getElementById("payload-preview-content");
    this.btnCopyWire = document.getElementById("btn-copy-wire");

    // Timeline Controls
    this.btnPrev = document.getElementById("btn-prev");
    this.btnPlayPause = document.getElementById("btn-play-pause");
    this.playPauseIcon = document.getElementById("play-pause-icon");
    this.playPauseText = document.getElementById("play-pause-text");
    this.btnNext = document.getElementById("btn-next");
    this.btnReplay = document.getElementById("btn-replay");
    this.speedSelect = document.getElementById("speed-select");
    this.timelineNodesContainer = document.getElementById("timeline-nodes-container");
  }

  bindEvents() {
    // Activity Tab Switching
    this.tabButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        this.tabButtons.forEach(b => b.classList.remove("active"));
        this.activityForms.forEach(f => f.classList.remove("active"));
        btn.classList.add("active");
        const targetId = btn.dataset.target;
        const targetForm = document.getElementById(targetId);
        if (targetForm) targetForm.classList.add("active");
      });
    });

    // Preset URL clicks
    this.presetTags.forEach(tag => {
      tag.addEventListener("click", () => {
        this.webUrlInput.value = tag.dataset.val;
      });
    });

    // Form 1: Web Browsing Visit
    this.formWeb.addEventListener("submit", (e) => {
      e.preventDefault();
      const url = this.webUrlInput.value.trim();
      if (url) {
        this.sendAction({ action: "start_web", url });
      }
    });

    // Form 2: SMTP Email Send
    this.formSmtp.addEventListener("submit", (e) => {
      e.preventDefault();
      this.sendAction({
        action: "start_smtp",
        sender: this.smtpSender.value.trim(),
        recipient: this.smtpRecipient.value.trim(),
        subject: this.smtpSubject.value.trim(),
        body: this.smtpBody.value
      });
    });

    // Form 3: HLS Stream Start
    this.formHls.addEventListener("submit", (e) => {
      e.preventDefault();
      this.sendAction({
        action: "start_hls",
        stream: this.hlsStream.value,
        bitrate: this.hlsBitrate.value
      });
    });

    // Bitrate selection update on mock screen
    this.hlsBitrate.addEventListener("change", () => {
      this.videoResDisplay.textContent = this.hlsBitrate.value.toUpperCase() + " HD";
    });

    // Clear Activity Log
    this.btnClearLog.addEventListener("click", () => {
      this.activityLogList.innerHTML = "";
    });

    // Inspector Tab Switching
    this.inspectorTabs.forEach(tab => {
      tab.addEventListener("click", () => {
        this.inspectorTabs.forEach(t => t.classList.remove("active"));
        this.inspectorViews.forEach(v => v.classList.remove("active"));
        tab.classList.add("active");
        const viewId = tab.dataset.view;
        const view = document.getElementById(viewId);
        if (view) view.classList.add("active");
      });
    });

    // Copy Wire Data
    this.btnCopyWire.addEventListener("click", () => {
      const text = this.wireDataPre.textContent;
      navigator.clipboard.writeText(text).then(() => {
        const originalText = this.btnCopyWire.textContent;
        this.btnCopyWire.textContent = "✓ Copied!";
        setTimeout(() => { this.btnCopyWire.textContent = originalText; }, 1500);
      });
    });

    // Timeline Controls
    this.btnPlayPause.addEventListener("click", () => {
      if (this.state.is_playing) {
        this.sendAction({ action: "pause" });
      } else {
        this.sendAction({ action: "resume" });
      }
    });

    this.btnPrev.addEventListener("click", () => {
      this.sendAction({ action: "step_prev" });
    });

    this.btnNext.addEventListener("click", () => {
      this.sendAction({ action: "step_next" });
    });

    this.btnReplay.addEventListener("click", () => {
      this.sendAction({ action: "replay" });
    });

    this.speedSelect.addEventListener("change", () => {
      const speed = parseFloat(this.speedSelect.value);
      this.sendAction({ action: "set_speed", speed });
    });

    // Keyboard Shortcuts
    window.addEventListener("keydown", (e) => {
      if (["input", "textarea", "select"].includes(document.activeElement.tagName.toLowerCase())) {
        return;
      }
      if (e.code === "Space") {
        e.preventDefault();
        this.btnPlayPause.click();
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        this.btnPrev.click();
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        this.btnNext.click();
      } else if (e.code === "KeyR") {
        e.preventDefault();
        this.btnReplay.click();
      }
    });
  }

  // ================= WEBSOCKET MANAGEMENT =================

  connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    this.updateConnectionStatus(false, "Connecting WebSocket...");
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.updateConnectionStatus(true, "Synchronized (Live)");
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "state_update" && payload.state) {
          this.state = payload.state;
          this.render();
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    this.ws.onclose = () => {
      this.updateConnectionStatus(false, "Reconnecting...");
      this.reconnectTimeout = setTimeout(() => this.connectWebSocket(), 2000);
    };

    this.ws.onerror = (err) => {
      console.error("WebSocket encountered error:", err);
      this.ws.close();
    };
  }

  sendAction(actionObj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(actionObj));
    } else {
      console.warn("WebSocket not connected. Unable to send action:", actionObj);
    }
  }

  updateConnectionStatus(isConnected, label) {
    const dot = this.connectionStatus.querySelector(".status-dot");
    if (isConnected) {
      dot.classList.add("connected");
    } else {
      dot.classList.remove("connected");
    }
    this.connectionLabel.textContent = label;
  }

  // ================= UI RENDERING =================

  render() {
    const { activity_type, is_playing, current_step, total_steps, events, playback_speed, hls_buffer_sec, activity_log } = this.state;

    // 1. Header Badges
    this.currentActivityBadge.textContent = activity_type.toUpperCase();
    this.stepCounterText.textContent = `${current_step} / ${total_steps}`;

    // Synchronize tab visibility with server activity_type if user didn't manually focus another tab
    const activeTab = document.querySelector(`.tab-btn[id="tab-${activity_type}"]`);
    if (activeTab && !document.querySelector(".activity-form:focus-within")) {
      this.tabButtons.forEach(b => b.classList.remove("active"));
      this.activityForms.forEach(f => f.classList.remove("active"));
      activeTab.classList.add("active");
      const targetForm = document.getElementById(`form-${activity_type}`);
      if (targetForm) targetForm.classList.add("active");
    }

    // 2. Play / Pause Control Button
    if (is_playing) {
      this.playPauseIcon.textContent = "⏸";
      this.playPauseText.textContent = "Pause";
      this.flowStateBadge.textContent = "PLAYING";
      this.flowStateBadge.style.color = "#10b981";
    } else {
      this.playPauseIcon.textContent = "▶";
      this.playPauseText.textContent = "Resume";
      this.flowStateBadge.textContent = current_step >= total_steps && total_steps > 0 ? "DONE" : "PAUSED";
      this.flowStateBadge.style.color = "#94a3b8";
    }

    // Prev / Next button enablement
    this.btnPrev.disabled = current_step <= 1;
    this.btnNext.disabled = current_step >= total_steps;

    // Speed selector
    if (this.speedSelect.value !== String(playback_speed)) {
      this.speedSelect.value = String(playback_speed);
    }

    // 3. Render Timeline Nodes
    this.renderTimeline(current_step, total_steps, events);

    // 4. Render Active Event
    const currentEvent = events && events.length >= current_step && current_step > 0 ? events[current_step - 1] : null;
    if (currentEvent) {
      this.renderActiveEvent(currentEvent);
    }

    // 5. Render HLS Buffer Meter & Video Mock
    this.renderHlsPlayer(hls_buffer_sec, currentEvent);

    // 6. Render Activity Log
    this.renderActivityLog(activity_log);
  }

  renderTimeline(currentStep, totalSteps, events) {
    this.timelineNodesContainer.innerHTML = "";
    for (let i = 1; i <= totalSteps; i++) {
      const node = document.createElement("button");
      node.type = "button";
      node.className = "timeline-node";
      node.textContent = i;
      node.title = `Jump to Packet ${i}`;

      const evt = events[i - 1];
      if (evt) {
        node.title = `Packet ${i} [${evt.protocol}]: ${evt.summary}`;
      }

      if (i < currentStep) {
        node.classList.add("completed");
      } else if (i === currentStep) {
        node.classList.add("active");
      }

      // Add small protocol tag below node
      if (evt) {
        const tag = document.createElement("span");
        tag.className = "node-proto-tag";
        tag.textContent = evt.protocol;
        node.appendChild(tag);
      }

      node.addEventListener("click", () => {
        this.sendAction({ action: "jump_to_step", step: i });
      });

      this.timelineNodesContainer.appendChild(node);
    }
  }

  renderActiveEvent(event) {
    const { protocol, direction, source, destination, summary, wire_data, metadata } = event;

    // Flow Badges
    this.flowProtoBadge.textContent = protocol;
    this.flowProtoBadge.className = `proto-tag ${protocol}`;

    const isC2S = direction === "client_to_server";
    this.flowDirBadge.textContent = isC2S ? "Client ➔ Server (Request)" : "Server ➔ Client (Response)";
    this.flowDirBadge.className = `direction-tag ${isC2S ? "client-to-server" : "server-to-client"}`;

    // Summary Text
    this.eventSummaryText.textContent = summary;

    // Node Highlighting
    if (isC2S) {
      this.clientNode.classList.add("active-node");
      this.serverNode.classList.remove("active-node");
    } else {
      this.serverNode.classList.add("active-node");
      this.clientNode.classList.remove("active-node");
    }

    // Packet flight animation
    this.animatedPacket.className = `animated-packet-bubble ${isC2S ? "fly-c2s" : "fly-s2c"}`;
    this.packetArrow.textContent = isC2S ? "➔" : "⬅";
    this.packetLabel.textContent = protocol;

    // Endpoints & Roles
    const clientEndpoint = isC2S ? source : destination;
    const serverEndpoint = isC2S ? destination : source;
    this.clientEndpointText.textContent = clientEndpoint;
    this.serverEndpointText.textContent = serverEndpoint;

    // Dynamic Server Identity based on protocol
    if (protocol === "DNS") {
      this.serverNameText.textContent = "DNS Resolver";
      this.serverRoleText.textContent = "Recursive DNS Authority (UDP 53)";
      this.wirePortLabel.textContent = "UDP :53";
      this.animatedPacket.style.backgroundColor = "var(--color-dns)";
      this.animatedPacket.style.boxShadow = "0 0 16px var(--color-dns)";
    } else if (protocol === "TCP") {
      this.serverNameText.textContent = "Web Host";
      this.serverRoleText.textContent = "TCP Socket Listener (Port 80)";
      this.wirePortLabel.textContent = "TCP :80";
      this.animatedPacket.style.backgroundColor = "var(--color-tcp)";
      this.animatedPacket.style.boxShadow = "0 0 16px var(--color-tcp)";
    } else if (protocol === "HTTP") {
      this.serverNameText.textContent = "HTTP Web Server";
      this.serverRoleText.textContent = "Origin Server (TCP 80 / HTTP/1.1)";
      this.wirePortLabel.textContent = "TCP :80";
      this.animatedPacket.style.backgroundColor = "var(--color-http)";
      this.animatedPacket.style.boxShadow = "0 0 16px var(--color-http)";
    } else if (protocol === "SMTP") {
      this.serverNameText.textContent = "SMTP Mail Server";
      this.serverRoleText.textContent = "Postfix MTA Gateway (TCP 25)";
      this.wirePortLabel.textContent = "TCP :25";
      this.animatedPacket.style.backgroundColor = "var(--color-smtp)";
      this.animatedPacket.style.boxShadow = "0 0 16px var(--color-smtp)";
    } else if (protocol === "HLS") {
      this.serverNameText.textContent = "Video CDN Edge";
      this.serverRoleText.textContent = "HLS Stream Distributor (HTTP/MPEG-TS)";
      this.wirePortLabel.textContent = "HTTP :80";
      this.animatedPacket.style.backgroundColor = "var(--color-hls)";
      this.animatedPacket.style.boxShadow = "0 0 16px var(--color-hls)";
    }

    // 1. Wire ASCII View
    this.wireDataPre.textContent = wire_data;

    // 2. Metadata Key-Value Table
    this.metadataTbody.innerHTML = "";
    const metaEntries = Object.entries(metadata || {});
    if (metaEntries.length === 0) {
      this.metadataTbody.innerHTML = `<tr><td colspan="2" class="empty-hint">No parsed metadata for this event.</td></tr>`;
    } else {
      metaEntries.forEach(([key, val]) => {
        if (typeof val === "object" && val !== null) {
          Object.entries(val).forEach(([subKey, subVal]) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${key}.${subKey}</td><td>${this.escapeHtml(String(subVal))}</td>`;
            this.metadataTbody.appendChild(tr);
          });
        } else {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>${key}</td><td>${this.escapeHtml(String(val))}</td>`;
          this.metadataTbody.appendChild(tr);
        }
      });
    }

    // 3. Payload Preview
    if (metadata && metadata.body) {
      if (metadata.body.trim().startsWith("<!DOCTYPE") || metadata.body.trim().startsWith("<html")) {
        this.payloadPreviewContent.innerHTML = `
          <div class="payload-html-render">
            ${metadata.body}
          </div>
        `;
      } else {
        this.payloadPreviewContent.innerHTML = `
          <pre class="monospace-wire-display" style="background:#111827; border-radius:6px; color:#e2e8f0;">${this.escapeHtml(metadata.body)}</pre>
        `;
      }
    } else if (metadata && metadata.segments) {
      this.payloadPreviewContent.innerHTML = `
        <div style="padding: 1rem; color: #a5b4fc;">
          <h4 style="margin-bottom:0.5rem;">HLS Target Segments (${metadata.target_duration}s per chunk):</h4>
          <ul style="padding-left: 1.25rem;">
            ${metadata.segments.map(s => `<li><code>${s}</code></li>`).join("")}
          </ul>
        </div>
      `;
    } else {
      this.payloadPreviewContent.innerHTML = `<div class="empty-hint">No body payload present in current packet.</div>`;
    }
  }

  renderHlsPlayer(bufferSec, currentEvent) {
    const maxBuffer = 16.0;
    const clampedBuffer = Math.min(maxBuffer, Math.max(0, bufferSec));
    const pct = (clampedBuffer / maxBuffer) * 100;
    this.bufferMeterFill.style.width = `${pct}%`;
    this.bufferValText.textContent = `${clampedBuffer.toFixed(1)}s / ${maxBuffer.toFixed(1)}s`;

    if (currentEvent && currentEvent.protocol === "HLS" && currentEvent.metadata) {
      if (currentEvent.metadata.segment) {
        this.videoSegmentLabel.textContent = `Streaming: ${currentEvent.metadata.segment} (${currentEvent.metadata.bitrate})`;
      } else if (currentEvent.metadata.variants) {
        this.videoSegmentLabel.textContent = `Manifest Parsed: ${currentEvent.metadata.variants.join(", ")}`;
      }
    }

    if (clampedBuffer > 0) {
      this.videoCenterIcon.textContent = "▶";
      this.videoScreen.classList.remove("buffering");
    } else if (this.state.is_playing && this.state.activity_type === "hls") {
      this.videoCenterIcon.textContent = "⏳";
      this.videoScreen.classList.add("buffering");
    } else {
      this.videoCenterIcon.textContent = "▶";
      this.videoScreen.classList.remove("buffering");
    }
  }

  renderActivityLog(logs) {
    if (!logs) return;
    this.activityLogList.innerHTML = "";
    logs.forEach(log => {
      const item = document.createElement("div");
      item.className = "log-item";
      item.innerHTML = `
        <span class="log-time">${log.timestamp}</span>
        <span class="log-badge ${log.type}">${log.type}</span>
        <span class="log-text">${this.escapeHtml(log.text)}</span>
      `;
      this.activityLogList.appendChild(item);
    });
    this.activityLogList.scrollTop = this.activityLogList.scrollHeight;
  }

  escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  window.app = new ProtocolVisualizerApp();
});
