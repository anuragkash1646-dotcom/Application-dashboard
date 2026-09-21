"""
PDF Generator for Application Layer Activity & Protocol Visualizer Documentation
Creates a publication-quality PDF with clickable links, architecture tables,
protocol flow explanations, step-by-step run instructions, and deployment guide.
"""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and display total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(
                36, letter[1] - 28,
                "Layer-7 Protocol Visualizer — Comprehensive System & Execution Guide"
            )
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(36, letter[1] - 32, letter[0] - 36, letter[1] - 32)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, 36, letter[0] - 36, 36)

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 36, 24, page_str)
        self.drawString(36, 24, "Live App: application-dashboard-production.up.railway.app")
        self.restoreState()


def build_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    style_subtitle = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=12
    )
    style_h1 = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    style_h2 = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    style_body = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=5
    )
    style_body_bold = ParagraphStyle(
        'Body_Custom_Bold',
        parent=style_body,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0f172a')
    )
    style_code = ParagraphStyle(
        'CodeBlock',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor('#0f172a')
    )
    style_bullet = ParagraphStyle(
        'Bullet_Custom',
        parent=style_body,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    story = []

    # ==================== BANNER & METADATA ====================
    story.append(Paragraph("Application Layer Activity & Protocol Visualizer", style_title))
    story.append(Paragraph("Comprehensive Technical Documentation, Protocol RFC Models, Local Setup & Cloud Deployment Guide", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10))

    # Key project links table with CLICKABLE links
    meta_data = [
        [
            Paragraph("<b>Project Repository:</b>", style_body),
            Paragraph('<a href="https://github.com/anuragkash1646-dotcom/Application-dashboard" color="#0284c7"><u>https://github.com/anuragkash1646-dotcom/Application-dashboard</u></a>', style_body)
        ],
        [
            Paragraph("<b>Live Cloud Deployment:</b>", style_body),
            Paragraph('<a href="https://application-dashboard-production.up.railway.app" color="#0284c7"><u>https://application-dashboard-production.up.railway.app</u></a>', style_body)
        ],
        [
            Paragraph("<b>Healthcheck Endpoint:</b>", style_body),
            Paragraph('<a href="https://application-dashboard-production.up.railway.app/health" color="#0284c7"><u>https://application-dashboard-production.up.railway.app/health</u></a>', style_body)
        ],
        [
            Paragraph("<b>Technology Stack:</b>", style_body),
            Paragraph("Python 3.10+, FastAPI, Uvicorn, WebSockets, Pydantic, Vanilla ES6 JavaScript, HTML5/CSS3", style_body)
        ],
    ]
    meta_table = Table(meta_data, colWidths=[1.8 * inch, 5.7 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ==================== 1. EXECUTIVE SUMMARY & CORE GOAL ====================
    story.append(Paragraph("1. Project Overview & Core Goals", style_h1))
    story.append(Paragraph(
        "The <b>Application Layer Activity & Protocol Visualizer</b> is an interactive educational Computer Networks Layer-7 "
        "protocol simulation suite. It bridges the conceptual gap between everyday user actions (such as browsing a website, "
        "sending an email, or streaming a video) and the exact RFC-defined protocol dialogues that execute beneath the surface.",
        style_body
    ))
    story.append(Paragraph(
        "Unlike abstract flowcharts or mock interfaces, this system operates a <b>deterministic RFC packet engine</b> coupled with a "
        "<b>real-time WebSocket synchronization layer</b>. Any state change—whether triggering a web visit, pausing the transmission, "
        "stepping forward, or jumping across packet timelines—is broadcast in real time to all connected browser clients.",
        style_body
    ))
    story.append(Spacer(1, 6))

    # ==================== 2. ARCHITECTURE ====================
    story.append(Paragraph("2. System Architecture & File Structure", style_h1))
    story.append(Paragraph(
        "The application is structured into decoupled components following clean software engineering principles:",
        style_body
    ))

    arch_rows = [
        [Paragraph("<b>Component</b>", style_body_bold), Paragraph("<b>File Location</b>", style_body_bold), Paragraph("<b>Functional Responsibility</b>", style_body_bold)],
        [
            Paragraph("<b>FastAPI Server</b>", style_body),
            Paragraph("<font name='Courier'>app/main.py</font>", style_body),
            Paragraph("Mounts static dashboard SPA, hosts <code>/health</code> healthcheck, and handles WebSocket handshakes at <code>/ws</code>.", style_body)
        ],
        [
            Paragraph("<b>WebSocket Manager</b>", style_body),
            Paragraph("<font name='Courier'>app/websocket_manager.py</font>", style_body),
            Paragraph("Manages active client pool, broadcast messaging, shared simulation state, and an asynchronous timer loop for automated playback.", style_body)
        ],
        [
            Paragraph("<b>Protocol Simulator</b>", style_body),
            Paragraph("<font name='Courier'>app/protocol_simulator.py</font>", style_body),
            Paragraph("Deterministic packet generation for DNS (RFC 1035), HTTP/1.1 (RFC 2616/7230), SMTP (RFC 5321), and HLS (RFC 8216).", style_body)
        ],
        [
            Paragraph("<b>Web Dashboard</b>", style_body),
            Paragraph("<font name='Courier'>app/static/index.html</font>", style_body),
            Paragraph("Dual-panel interface: Left panel (Activity forms, logs); Right panel (Client ↔ Server nodes, wire inspector); Bottom timeline.", style_body)
        ],
        [
            Paragraph("<b>Dashboard Styling</b>", style_body),
            Paragraph("<font name='Courier'>app/static/style.css</font>", style_body),
            Paragraph("Modern dark cybersecurity aesthetic, flying packet keyframe animations (C2S/S2C), glowing nodes, and responsive layout.", style_body)
        ],
        [
            Paragraph("<b>Frontend Controller</b>", style_body),
            Paragraph("<font name='Courier'>app/static/app.js</font>", style_body),
            Paragraph("Vanilla ES6 WebSocket client: handles auto-reconnect, packet visualization, tab switching, and keyboard shortcuts.", style_body)
        ],
        [
            Paragraph("<b>Test Suite</b>", style_body),
            Paragraph("<font name='Courier'>tests/test_protocol_simulator.py</font>", style_body),
            Paragraph("7 automated pytest cases covering health, DNS, HTTP, SMTP state machine, HLS manifest/segments, and WebSockets.", style_body)
        ],
        [
            Paragraph("<b>Deployment Config</b>", style_body),
            Paragraph("<font name='Courier'>Procfile &amp; railway.json</font>", style_body),
            Paragraph("Zero-config Nixpacks build declaration, startup command, and automated healthcheck for Railway cloud deployment.", style_body)
        ],
    ]
    arch_table = Table(arch_rows, colWidths=[1.5 * inch, 2.0 * inch, 4.0 * inch])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 10))

    # ==================== 3. PROTOCOL SIMULATIONS ====================
    story.append(Paragraph("3. Detailed Protocol Simulation Specifications", style_h1))

    # 3.1 Web Browsing
    story.append(Paragraph("3.1 Web Browsing Simulation (DNS + TCP + HTTP/1.1)", style_h2))
    story.append(Paragraph(
        "Entering a URL (e.g. <code>https://example.com/index.html</code>) triggers a multi-tier resolution and fetch sequence:",
        style_body
    ))
    story.append(Paragraph("• <b>DNS Query (UDP Port 53):</b> Standard query with Transaction ID, A-record lookup, and Recursion Desired (RD) flag set to <code>0x0100</code>.", style_bullet))
    story.append(Paragraph("• <b>DNS Response (UDP Port 53):</b> Server returns resolved IP address (e.g. <code>93.184.216.34</code>) and TTL 300 seconds with <code>NOERROR</code>.", style_bullet))
    story.append(Paragraph("• <b>TCP 3-Way Handshake (Port 80):</b> Client initiates <code>SYN</code>, server responds with <code>SYN, ACK</code>, and client confirms with <code>ACK</code>.", style_bullet))
    story.append(Paragraph("• <b>HTTP/1.1 GET Request:</b> Transmits <code>GET /path HTTP/1.1</code> with headers: <code>Host</code>, <code>User-Agent</code>, <code>Accept</code>, and <code>Connection: keep-alive</code>.", style_bullet))
    story.append(Paragraph("• <b>HTTP 200 OK Response:</b> Delivers server timestamp, <code>Content-Type: text/html</code>, <code>Content-Length</code>, and rendered HTML payload.", style_bullet))

    # 3.2 SMTP Email
    story.append(Paragraph("3.2 SMTP Email Dispatch Simulation (RFC 5321)", style_h2))
    story.append(Paragraph(
        "Simulates an email dispatch over TCP Port 25 following the full SMTP state machine:",
        style_body
    ))
    smtp_flow_text = (
        "1. <b>220 Service Ready:</b> Server welcomes client (Postfix ESMTP ready).<br/>"
        "2. <b>EHLO client.fqdn:</b> Client identifies its fully qualified domain name.<br/>"
        "3. <b>250 ESMTP:</b> Server advertises capabilities (<code>PIPELINING</code>, <code>SIZE 10485760</code>, <code>8BITMIME</code>).<br/>"
        "4. <b>MAIL FROM:&lt;sender&gt;:</b> Specifies envelope sender address.<br/>"
        "5. <b>250 2.1.0 Ok:</b> Server accepts sender address.<br/>"
        "6. <b>RCPT TO:&lt;recipient&gt;:</b> Specifies mailbox recipient address.<br/>"
        "7. <b>250 2.1.5 Ok:</b> Server accepts recipient.<br/>"
        "8. <b>DATA:</b> Client requests permission to transmit body.<br/>"
        "9. <b>354 Start Input:</b> Server responds to begin input, ending with <code>&lt;CRLF&gt;.&lt;CRLF&gt;</code>.<br/>"
        "10. <b>MIME Payload:</b> Transmits RFC headers (<code>From</code>, <code>To</code>, <code>Date</code>, <code>Subject</code>, <code>Message-ID</code>) and body.<br/>"
        "11. <b>250 2.0.0 Ok queued:</b> Server assigns queue ID for dispatch.<br/>"
        "12. <b>QUIT:</b> Client initiates session teardown.<br/>"
        "13. <b>221 Bye:</b> Server closes transmission channel."
    )
    story.append(Paragraph(smtp_flow_text, style_body))

    # 3.3 HLS Video Streaming
    story.append(Paragraph("3.3 HLS Adaptive Video Streaming Simulation (RFC 8216)", style_h2))
    story.append(Paragraph(
        "Simulates chunk-based HTTP Live Streaming with dynamic client buffer telemetry:",
        style_body
    ))
    story.append(Paragraph("• <b>CDN Hostname Resolution:</b> UDP 53 DNS resolution for CDN edge host (<code>cdn.videoedge.net</code>).", style_bullet))
    story.append(Paragraph("• <b>Master Playlist Request (<code>master.m3u8</code>):</b> Delivers available bitrate variants (1080p @ 5 Mbps, 720p @ 2.5 Mbps, 360p @ 800 Kbps).", style_bullet))
    story.append(Paragraph("• <b>Variant Playlist Request (<code>720p/playlist.m3u8</code>):</b> Delivers target duration (4 seconds) and segment list.", style_bullet))
    story.append(Paragraph("• <b>Progressive 4-Second MPEG-TS Chunk Requests:</b> Progressively requests <code>segment_000.ts</code> through <code>segment_003.ts</code>.", style_bullet))
    story.append(Paragraph("• <b>Dynamic Buffer Health Telemetry:</b> Client buffer increases with each segment received (0.0s ➔ 4.0s ➔ 8.0s ➔ 12.0s ➔ 16.0s), visualised on the dashboard buffer meter.", style_bullet))

    story.append(Spacer(1, 10))

    # ==================== 4. STEP-BY-STEP RUN INSTRUCTIONS ====================
    story.append(Paragraph("4. Step-by-Step Instructions to Run Locally", style_h1))

    story.append(Paragraph("<b>Step 4.1: Prerequisites</b>", style_h2))
    story.append(Paragraph("Ensure <b>Python 3.10 or higher</b> and <b>Git</b> are installed on your system.", style_body))

    story.append(Paragraph("<b>Step 4.2: Clone the Repository</b>", style_h2))
    cmd_clone = (
        "git clone https://github.com/anuragkash1646-dotcom/Application-dashboard.git<br/>"
        "cd Application-dashboard"
    )
    story.append(Paragraph(f"<font name='Courier'>{cmd_clone}</font>", style_code))

    story.append(Paragraph("<b>Step 4.3: Install Dependencies</b>", style_h2))
    story.append(Paragraph("Install the required Python libraries using pip:", style_body))
    story.append(Paragraph("<font name='Courier'>pip install -r requirements.txt</font>", style_code))

    story.append(Paragraph("<b>Step 4.4: Launch the Visualizer Server</b>", style_h2))
    story.append(Paragraph("Start the FastAPI application using Uvicorn:", style_body))
    story.append(Paragraph("<font name='Courier'>uvicorn app.main:app --reload --host 127.0.0.1 --port 8000</font>", style_code))

    story.append(Paragraph("<b>Step 4.5: Open Dashboard &amp; Verify Endpoints</b>", style_h2))
    story.append(Paragraph("• <b>Interactive Dashboard:</b> Open <a href='http://127.0.0.1:8000/' color='#0284c7'><u>http://127.0.0.1:8000/</u></a> in your web browser.<br/>"
                           "• <b>API Healthcheck:</b> Open <a href='http://127.0.0.1:8000/health' color='#0284c7'><u>http://127.0.0.1:8000/health</u></a> (returns <code>{\"status\":\"ok\"}</code>).", style_body))

    story.append(Spacer(1, 10))

    # ==================== 5. USER CONTROLS & SHORTCUTS ====================
    story.append(Paragraph("5. Dashboard Controls & Keyboard Navigation", style_h1))
    ctrl_rows = [
        [Paragraph("<b>Action / Control</b>", style_body_bold), Paragraph("<b>Keyboard Shortcut</b>", style_body_bold), Paragraph("<b>Behavior &amp; WebSocket Event</b>", style_body_bold)],
        [
            Paragraph("<b>Play / Pause Toggle</b>", style_body),
            Paragraph("<font name='Courier'>Spacebar</font>", style_body),
            Paragraph("Freezes or resumes automatic packet playback ticker.", style_body)
        ],
        [
            Paragraph("<b>Step Next</b>", style_body),
            Paragraph("<font name='Courier'>Right Arrow (➔)</font>", style_body),
            Paragraph("Advances simulation exactly one packet forward and updates wire inspector.", style_body)
        ],
        [
            Paragraph("<b>Step Previous</b>", style_body),
            Paragraph("<font name='Courier'>Left Arrow (⬅)</font>", style_body),
            Paragraph("Steps back exactly one packet in the historical transaction.", style_body)
        ],
        [
            Paragraph("<b>Replay</b>", style_body),
            Paragraph("<font name='Courier'>R key</font>", style_body),
            Paragraph("Resets simulation to packet 1 and restarts automatic playback.", style_body)
        ],
        [
            Paragraph("<b>Timeline Jump</b>", style_body),
            Paragraph("Click circular node", style_body),
            Paragraph("Directly jumps to any numbered event node (1..N).", style_body)
        ],
        [
            Paragraph("<b>Playback Speed</b>", style_body),
            Paragraph("Dropdown (0.5x – 2.0x)", style_body),
            Paragraph("Dynamically adjusts delay interval between automatic packet steps.", style_body)
        ],
    ]
    ctrl_table = Table(ctrl_rows, colWidths=[1.8 * inch, 1.8 * inch, 3.9 * inch])
    ctrl_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(ctrl_table)
    story.append(Spacer(1, 10))

    # ==================== 6. AUTOMATED TESTING ====================
    story.append(Paragraph("6. Automated Testing Suite", style_h1))
    story.append(Paragraph(
        "The project includes a comprehensive pytest suite verifying all protocol generation logic, "
        "state transitions, and WebSocket lifecycles.",
        style_body
    ))
    story.append(Paragraph("Execute the test suite with verbose output:", style_body))
    story.append(Paragraph("<font name='Courier'>pytest tests/ -v</font>", style_code))

    test_rows = [
        [Paragraph("<b>Test Case Name</b>", style_body_bold), Paragraph("<b>Verification Scope</b>", style_body_bold), Paragraph("<b>Status</b>", style_body_bold)],
        [Paragraph("<code>test_health_endpoint</code>", style_body), Paragraph("Verifies <code>GET /health</code> returns HTTP 200 with <code>{\"status\":\"ok\"}</code>", style_body), Paragraph("<font color='#16a34a'><b>PASSED</b></font>", style_body)],
        [Paragraph("<code>test_index_dashboard_serves_html</code>", style_body), Paragraph("Verifies root URL <code>/</code> successfully serves HTML dashboard", style_body), Paragraph("<font color='#16a34a'><b>PASSED</b></font>", style_body)],
        [Paragraph("<code>test_dns_event_generation</code>", style_body), Paragraph("Validates UDP 53, A-record query, RD flag <code>0x0100</code>, resolved IP, and TTL 300", style_body), Paragraph("<font color='#16a34a'><b>PASSED</b></font>", style_body)],
        [Paragraph("<code>test_http_transaction</code>", style_body), Paragraph("Validates HTTP/1.1 GET request headers, Port 80, 200 OK, Content-Type, and HTML body", style_body), Paragraph("<font color='#16a34a'><b>PASSED</b></font>", style_body)],
        [Paragraph("<code>test_smtp_state_machine</code>", style_body), Paragraph("Validates complete RFC 5321 conversation (220 ➔ EHLO ➔ DATA ➔ QUIT ➔ 221)", style_body), Paragraph("<font color='#16a34a'><b>PASSED</b></font>", style_body)],
        [Paragraph("<code>test_hls_manifest_and_segments</code>", style_body), Paragraph("Validates master/variant manifests and progressive buffer health (4s ➔ 8s ➔ 12s ➔ 16s)", style_body), Paragraph("<font color='#16a34a'><b>PASSED</b></font>", style_body)],
        [Paragraph("<code>test_websocket_lifecycle_and_actions</code>", style_body), Paragraph("Validates WebSocket connection, initial snapshot, pause, next, prev, jump, and replay", style_body), Paragraph("<font color='#16a34a'><b>PASSED</b></font>", style_body)],
    ]
    test_table = Table(test_rows, colWidths=[2.6 * inch, 4.0 * inch, 0.9 * inch])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 10))

    # ==================== 7. RAILWAY DEPLOYMENT ====================
    story.append(Paragraph("7. Cloud Deployment Guide (Railway)", style_h1))
    story.append(Paragraph(
        "The repository is configured for zero-configuration, continuous deployment on Railway using Nixpacks.",
        style_body
    ))
    story.append(Paragraph("1. <b>Login:</b> Sign in to <a href='https://railway.app' color='#0284c7'><u>https://railway.app</u></a> using your GitHub account.", style_bullet))
    story.append(Paragraph("2. <b>New Project:</b> Click <b>'+ New Project'</b> ➔ <b>'Deploy from GitHub repo'</b>.", style_bullet))
    story.append(Paragraph("3. <b>Select Repository:</b> Choose <b><code>anuragkash1646-dotcom/Application-dashboard</code></b>.", style_bullet))
    story.append(Paragraph("4. <b>Automatic Build:</b> Railway reads <code>railway.json</code> and installs packages from <code>requirements.txt</code>.", style_bullet))
    story.append(Paragraph("5. <b>Public Domain:</b> Under Service Settings ➔ Networking, generate a public domain to obtain your live deployment URL.", style_bullet))

    story.append(Spacer(1, 12))

    # ==================== 8. SUMMARY & DIRECT ACCESS LINKS ====================
    story.append(Paragraph("8. Direct Access Links Reference", style_h1))

    links_data = [
        [
            Paragraph("<b>Resource</b>", style_body_bold),
            Paragraph("<b>URL (Clickable Link)</b>", style_body_bold),
            Paragraph("<b>Notes</b>", style_body_bold)
        ],
        [
            Paragraph("<b>Live Application</b>", style_body),
            Paragraph('<a href="https://application-dashboard-production.up.railway.app" color="#0284c7"><b>https://application-dashboard-production.up.railway.app</b></a>', style_body),
            Paragraph("Production deployment running on Railway", style_body)
        ],
        [
            Paragraph("<b>GitHub Repository</b>", style_body),
            Paragraph('<a href="https://github.com/anuragkash1646-dotcom/Application-dashboard" color="#0284c7"><b>https://github.com/anuragkash1646-dotcom/Application-dashboard</b></a>', style_body),
            Paragraph("Source code, commits, and issue tracking", style_body)
        ],
        [
            Paragraph("<b>Live Healthcheck</b>", style_body),
            Paragraph('<a href="https://application-dashboard-production.up.railway.app/health" color="#0284c7"><b>https://application-dashboard-production.up.railway.app/health</b></a>', style_body),
            Paragraph("Healthcheck returning status: ok", style_body)
        ],
    ]
    links_table = Table(links_data, colWidths=[1.8 * inch, 3.8 * inch, 1.9 * inch])
    links_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f9ff'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(links_table)

    # Build PDF with dynamic header/footer
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Documentation PDF generated successfully at: {os.path.abspath(filename)}")


if __name__ == "__main__":
    out_file = "Application_Layer_Protocol_Visualizer_Documentation.pdf"
    build_pdf(out_file)
