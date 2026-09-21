"""
Automated Test Suite for Application Layer Activity & Protocol Visualizer
Covers:
1. Health endpoint (/health)
2. DNS query/response generation (UDP 53, A-record, RD 0x0100, TTL 300)
3. HTTP transaction (GET HTTP/1.1, Host, headers, 200 OK, body)
4. SMTP state machine (RFC 5321 conversation: 220 -> EHLO -> DATA -> QUIT -> 221)
5. HLS manifest & segment generation (master.m3u8, variant, 4s TS segments, buffer health)
6. WebSocket lifecycle, connection handshake, and real-time interactive actions
"""

import json
import pytest
from starlette.testclient import TestClient

from app.main import app
from app.protocol_simulator import (
    generate_web_sequence,
    generate_smtp_sequence,
    generate_hls_sequence,
)


@pytest.fixture
def client():
    return TestClient(app)


# ==========================================
# 1. Health & Web Endpoint Tests
# ==========================================

def test_health_endpoint(client):
    """Verifies that /health returns HTTP 200 with status: ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_dashboard_serves_html(client):
    """Verifies that root / serves the HTML dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Layer-7 Protocol Visualizer" in response.text


# ==========================================
# 2. DNS Event Generation Tests
# ==========================================

def test_dns_event_generation():
    """
    Verifies DNS query and response generation:
    - UDP port 53
    - A-record query
    - Recursion Desired flag 0x0100
    - Resolved IP
    - TTL 300 seconds
    """
    events = generate_web_sequence("https://my-uni.edu/research")
    assert len(events) >= 7

    # Event 1: DNS Query
    query_evt = events[0]
    assert query_evt.sequence == 1
    assert query_evt.protocol == "DNS"
    assert query_evt.direction == "client_to_server"
    assert query_evt.destination.endswith(":53")
    assert query_evt.metadata["port"] == 53
    assert query_evt.metadata["record_type"] == "A"
    assert query_evt.metadata["flags"] == "0x0100"
    assert query_evt.metadata["recursion_desired"] is True
    assert "Recursion Desired" in query_evt.wire_data
    assert "my-uni.edu" in query_evt.wire_data

    # Event 2: DNS Response
    resp_evt = events[1]
    assert resp_evt.sequence == 2
    assert resp_evt.protocol == "DNS"
    assert resp_evt.direction == "server_to_client"
    assert resp_evt.source.endswith(":53")
    assert resp_evt.metadata["ttl_seconds"] == 300
    assert resp_evt.metadata["status"] == "NOERROR"
    assert "TTL 300" in resp_evt.wire_data
    assert resp_evt.metadata["resolved_ip"] in resp_evt.wire_data


# ==========================================
# 3. HTTP Transaction Tests
# ==========================================

def test_http_transaction():
    """
    Verifies HTTP transaction:
    - HTTP/1.1 GET
    - TCP port 80
    - Host, User-Agent, Accept, Connection: keep-alive
    - HTTP 200 OK
    - Content-Type, Content-Length, HTML body
    """
    events = generate_web_sequence("http://example.com/docs/intro.html")

    # Locate HTTP GET request (Event 6)
    req_evts = [e for e in events if e.protocol == "HTTP" and e.direction == "client_to_server"]
    assert len(req_evts) == 1
    req = req_evts[0]
    assert req.metadata["method"] == "GET"
    assert req.metadata["path"] == "/docs/intro.html"
    assert req.metadata["headers"]["Host"] == "example.com"
    assert req.metadata["headers"]["Connection"] == "keep-alive"
    assert "GET /docs/intro.html HTTP/1.1" in req.wire_data
    assert "Host: example.com" in req.wire_data
    assert "Connection: keep-alive" in req.wire_data

    # Locate HTTP 200 OK response (Event 7)
    resp_evts = [e for e in events if e.protocol == "HTTP" and e.direction == "server_to_client"]
    assert len(resp_evts) == 1
    resp = resp_evts[0]
    assert resp.metadata["status_code"] == 200
    assert "text/html" in resp.metadata["headers"]["Content-Type"]
    assert "Content-Length" in resp.metadata["headers"]
    assert "<!DOCTYPE html>" in resp.metadata["body"]
    assert "HTTP/1.1 200 OK" in resp.wire_data


# ==========================================
# 4. SMTP State Machine Tests
# ==========================================

def test_smtp_state_machine():
    """
    Verifies full RFC 5321 SMTP conversation:
    220 Service Ready -> EHLO -> 250 ESMTP -> MAIL FROM -> 250 OK ->
    RCPT TO -> 250 OK -> DATA -> 354 Start Input -> MIME + body + <CRLF>.<CRLF> ->
    250 Queued -> QUIT -> 221 Bye.
    Port: TCP port 25.
    """
    events = generate_smtp_sequence(
        sender="carol@domain.org",
        recipient="dave@domain.org",
        subject="Protocol Test",
        body="Testing SMTP RFC 5321 state machine.",
    )

    assert len(events) == 13

    # All events must reference port 25
    for evt in events:
        assert evt.protocol == "SMTP"
        assert evt.metadata["port"] == 25
        assert (":25" in evt.source) or (":25" in evt.destination)

    # Check key state transitions
    assert events[0].direction == "server_to_client"
    assert "220" in events[0].summary and "Service Ready" in events[0].summary

    assert events[1].direction == "client_to_server"
    assert "EHLO" in events[1].wire_data

    assert events[2].direction == "server_to_client"
    assert "250" in events[2].wire_data and "PIPELINING" in events[2].wire_data

    assert events[3].direction == "client_to_server"
    assert "MAIL FROM:<carol@domain.org>" in events[3].wire_data

    assert events[4].direction == "server_to_client"
    assert "250" in events[4].wire_data

    assert events[5].direction == "client_to_server"
    assert "RCPT TO:<dave@domain.org>" in events[5].wire_data

    assert events[6].direction == "server_to_client"
    assert "250" in events[6].wire_data

    assert events[7].direction == "client_to_server"
    assert "DATA" in events[7].wire_data

    assert events[8].direction == "server_to_client"
    assert "354" in events[8].wire_data

    # Payload event
    assert events[9].direction == "client_to_server"
    assert "Subject: Protocol Test" in events[9].wire_data
    assert "From: carol@domain.org" in events[9].wire_data
    assert "To: dave@domain.org" in events[9].wire_data
    assert ".\r\n" in events[9].wire_data

    assert events[10].direction == "server_to_client"
    assert "250" in events[10].wire_data and "queued" in events[10].wire_data

    assert events[11].direction == "client_to_server"
    assert "QUIT" in events[11].wire_data

    assert events[12].direction == "server_to_client"
    assert "221" in events[12].wire_data and "Bye" in events[12].wire_data


# ==========================================
# 5. HLS Manifest and Segments Tests
# ==========================================

def test_hls_manifest_and_segments():
    """
    Verifies HLS streaming simulation:
    - DNS lookup for CDN hostname
    - Master playlist request/response (master.m3u8, bitrate variants)
    - Variant playlist request/response (720p/playlist.m3u8)
    - 4-second MPEG-TS segments (segment_000.ts .. segment_003.ts)
    - Progressive buffer health calculation
    """
    events = generate_hls_sequence("vod/sample", "720p")
    assert len(events) >= 10

    # 1. CDN DNS
    dns_events = [e for e in events if e.protocol == "DNS"]
    assert len(dns_events) == 2
    assert "cdn.videoedge.net" in dns_events[0].wire_data

    # 2. Master Playlist
    master_resp = [e for e in events if e.metadata.get("stage") == "master_manifest_resp"][0]
    assert "#EXTM3U" in master_resp.metadata["body"]
    assert "#EXT-X-STREAM-INF" in master_resp.metadata["body"]
    assert "720p/playlist.m3u8" in master_resp.metadata["body"]

    # 3. Variant Playlist
    variant_resp = [e for e in events if e.metadata.get("stage") == "variant_manifest_resp"][0]
    assert "#EXT-X-TARGETDURATION:4" in variant_resp.metadata["body"]
    assert "segment_000.ts" in variant_resp.metadata["body"]
    assert variant_resp.metadata["target_duration"] == 4.0

    # 4. Progressive Segments & Buffer Tracking
    seg_resp_events = [e for e in events if e.metadata.get("segment_duration_sec") == 4.0]
    assert len(seg_resp_events) == 4

    buffers = [e.metadata["buffer_health_sec"] for e in seg_resp_events]
    assert buffers == [4.0, 8.0, 12.0, 16.0]  # Progressive 4-second increments


# ==========================================
# 6. WebSocket Lifecycle and Synchronized Actions Tests
# ==========================================

def test_websocket_lifecycle_and_actions(client):
    """
    Verifies WebSocket handshake, receiving initial state, and responding
    to interactive simulation actions (start_web, pause, step_next, replay, jump).
    """
    with client.websocket_connect("/ws") as websocket:
        # Initial snapshot sent upon connect
        raw_msg = websocket.receive_text()
        data = json.loads(raw_msg)
        assert data["type"] == "state_update"
        assert "state" in data
        assert data["state"]["total_steps"] > 0

        # Action 1: start_smtp
        websocket.send_text(json.dumps({
            "action": "start_smtp",
            "sender": "test1@abc.com",
            "recipient": "test2@abc.com",
            "subject": "WS Test",
            "body": "Payload"
        }))
        state_msg = json.loads(websocket.receive_text())
        assert state_msg["state"]["activity_type"] == "smtp"
        assert state_msg["state"]["total_steps"] == 13
        assert state_msg["state"]["current_step"] == 1

        # Action 2: pause
        websocket.send_text(json.dumps({"action": "pause"}))
        state_msg = json.loads(websocket.receive_text())
        assert state_msg["state"]["is_playing"] is False

        # Action 3: step_next
        websocket.send_text(json.dumps({"action": "step_next"}))
        state_msg = json.loads(websocket.receive_text())
        assert state_msg["state"]["current_step"] == 2

        # Action 4: step_prev
        websocket.send_text(json.dumps({"action": "step_prev"}))
        state_msg = json.loads(websocket.receive_text())
        assert state_msg["state"]["current_step"] == 1

        # Action 5: jump_to_step
        websocket.send_text(json.dumps({"action": "jump_to_step", "step": 5}))
        state_msg = json.loads(websocket.receive_text())
        assert state_msg["state"]["current_step"] == 5

        # Action 6: replay
        websocket.send_text(json.dumps({"action": "replay"}))
        state_msg = json.loads(websocket.receive_text())
        assert state_msg["state"]["current_step"] == 1
        assert state_msg["state"]["is_playing"] is True

        # Stop ticker for clean shutdown
        websocket.send_text(json.dumps({"action": "pause"}))
        websocket.receive_text()
