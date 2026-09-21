"""
Protocol Simulator Module
Deterministic RFC-compliant protocol packet generation for:
- Web Browsing (DNS resolution via UDP 53, TCP 3-way handshake, HTTP/1.1 GET / 200 OK)
- SMTP Email Dispatch (RFC 5321 SMTP handshake, envelopes, MIME body, termination via TCP 25)
- HLS Video Streaming (RFC 8216 CDN DNS, master.m3u8, variant playlist, 4s MPEG-TS segments, buffer tracking)
"""

from datetime import datetime, timezone
import random
from typing import Dict, List, Literal, Optional, Any
from urllib.parse import urlparse
from pydantic import BaseModel, Field


class ProtocolEvent(BaseModel):
    sequence: int
    protocol: Literal["DNS", "TCP", "HTTP", "SMTP", "HLS"]
    direction: Literal["client_to_server", "server_to_client"]
    source: str
    destination: str
    summary: str
    wire_data: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3])
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SimulationState(BaseModel):
    activity_type: Literal["idle", "web", "smtp", "hls"] = "idle"
    is_playing: bool = False
    current_step: int = 0  # 0 indicates not started or ready, 1..total_steps indicates current event
    total_steps: int = 0
    events: List[ProtocolEvent] = Field(default_factory=list)
    playback_speed: float = 1.0  # Multiplier (e.g. 1.0 = normal, 1.5 = faster)
    hls_buffer_sec: float = 0.0
    activity_log: List[Dict[str, Any]] = Field(default_factory=list)


def format_hex_dump(data: str) -> str:
    """Generates an educational side-by-side hex and ASCII view of text payload."""
    raw_bytes = data.encode("utf-8", errors="replace")
    lines = []
    for i in range(0, len(raw_bytes), 16):
        chunk = raw_bytes[i : i + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{i:04x}   {hex_part:<48}   |{ascii_part}|")
    return "\n".join(lines)


# ==========================================
# 1. Web Browsing Sequence Generator
# ==========================================

def generate_web_sequence(url: str) -> List[ProtocolEvent]:
    """
    Generates deterministic events for Web Browsing:
    1. DNS Query (UDP 53, A-record, Recursion Desired 0x0100)
    2. DNS Response (UDP 53, Resolved IP, TTL 300)
    3. TCP SYN (Port 80)
    4. TCP SYN-ACK (Port 80)
    5. TCP ACK (Port 80)
    6. HTTP/1.1 GET Request
    7. HTTP 200 OK Response
    """
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    hostname = parsed.hostname or "example.com"
    path = parsed.path or "/"
    if parsed.query:
        path += f"?{parsed.query}"

    # Deterministic IP resolution derived from hostname
    hash_val = sum(ord(c) for c in hostname)
    resolved_ip = f"93.184.{(hash_val % 200) + 10}.{(hash_val * 7 % 240) + 10}"
    client_ip = "192.168.1.105"
    client_port = 54321
    dns_server = "8.8.8.8:53"
    web_server = f"{resolved_ip}:80"

    tx_id = f"0x{(hash_val * 17) % 65535:04x}"
    events: List[ProtocolEvent] = []

    # Step 1: DNS Query
    dns_query_wire = (
        f"+-------------------------------------------------------------------------+\n"
        f"| User Datagram Protocol (UDP), Src Port: {client_port}, Dst Port: 53             |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"| Domain Name System (Query)                                              |\n"
        f"| Transaction ID: {tx_id:<8} Flags: 0x0100 (Standard query, Recursion Desired)   |\n"
        f"| Questions: 1, Answer RRs: 0, Authority RRs: 0, Additional RRs: 0        |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"Queries:\n"
        f"  Name: {hostname}\n"
        f"  Type: A (Host Address) (1)\n"
        f"  Class: IN (0x0001)\n"
        f"Flags Detailed:\n"
        f"  0... .... .... .... = Response: Message is a query\n"
        f"  .000 0... .... .... = Opcode: Standard query (0)\n"
        f"  .... ..1. .... .... = Truncated: Message is not truncated\n"
        f"  .... ...1 .... .... = Recursion desired: Do query recursively (1)\n"
    )
    events.append(
        ProtocolEvent(
            sequence=1,
            protocol="DNS",
            direction="client_to_server",
            source=f"{client_ip}:{client_port}",
            destination=dns_server,
            summary=f"Standard query {tx_id} A {hostname} (Recursion Desired: 0x0100)",
            wire_data=dns_query_wire,
            metadata={
                "transport": "UDP",
                "port": 53,
                "tx_id": tx_id,
                "query": hostname,
                "record_type": "A",
                "flags": "0x0100",
                "recursion_desired": True,
            },
        )
    )

    # Step 2: DNS Response
    dns_resp_wire = (
        f"+-------------------------------------------------------------------------+\n"
        f"| User Datagram Protocol (UDP), Src Port: 53, Dst Port: {client_port}             |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"| Domain Name System (Response)                                           |\n"
        f"| Transaction ID: {tx_id:<8} Flags: 0x8180 (Standard query response, No error) |\n"
        f"| Questions: 1, Answer RRs: 1, Authority RRs: 0, Additional RRs: 0        |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"Queries:\n"
        f"  Name: {hostname} (Type A, Class IN)\n"
        f"Answers:\n"
        f"  {hostname}: type A, class IN, TTL 300\n"
        f"    Addr: {resolved_ip}\n"
        f"Flags Detailed:\n"
        f"  1... .... .... .... = Response: Message is a response\n"
        f"  .... ...1 .... .... = Recursion desired: 1\n"
        f"  .... .... 1... .... = Recursion available: Server can do recursive queries\n"
        f"  .... .... .... 0000 = Reply code: No error (0)\n"
    )
    events.append(
        ProtocolEvent(
            sequence=2,
            protocol="DNS",
            direction="server_to_client",
            source=dns_server,
            destination=f"{client_ip}:{client_port}",
            summary=f"Standard query response {tx_id} A {hostname} -> {resolved_ip} (TTL 300s)",
            wire_data=dns_resp_wire,
            metadata={
                "transport": "UDP",
                "port": 53,
                "tx_id": tx_id,
                "resolved_ip": resolved_ip,
                "ttl_seconds": 300,
                "flags": "0x8180",
                "status": "NOERROR",
            },
        )
    )

    # Step 3: TCP SYN Handshake
    tcp_syn_wire = (
        f"+-------------------------------------------------------------------------+\n"
        f"| Transmission Control Protocol (TCP), Src Port: {client_port}, Dst Port: 80       |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"| Sequence Number: 1000001 (relative 0)                                   |\n"
        f"| Acknowledgment Number: 0                                                |\n"
        f"| Header Length: 32 bytes, Window size: 65535                            |\n"
        f"| Flags: 0x002 (SYN) [Synchronize Sequence Numbers]                       |\n"
        f"+-------------------------------------------------------------------------+\n"
    )
    events.append(
        ProtocolEvent(
            sequence=3,
            protocol="TCP",
            direction="client_to_server",
            source=f"{client_ip}:{client_port}",
            destination=web_server,
            summary="[SYN] Seq=0 Win=65535 Len=0 MSS=1460",
            wire_data=tcp_syn_wire,
            metadata={"transport": "TCP", "flags": "SYN", "seq": 1000001, "ack": 0},
        )
    )

    # Step 4: TCP SYN-ACK
    tcp_synack_wire = (
        f"+-------------------------------------------------------------------------+\n"
        f"| Transmission Control Protocol (TCP), Src Port: 80, Dst Port: {client_port}       |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"| Sequence Number: 5000001 (relative 0)                                   |\n"
        f"| Acknowledgment Number: 1000002 (relative 1)                             |\n"
        f"| Header Length: 32 bytes, Window size: 65535                            |\n"
        f"| Flags: 0x012 (SYN, ACK) [Connection Accepted]                           |\n"
        f"+-------------------------------------------------------------------------+\n"
    )
    events.append(
        ProtocolEvent(
            sequence=4,
            protocol="TCP",
            direction="server_to_client",
            source=web_server,
            destination=f"{client_ip}:{client_port}",
            summary="[SYN, ACK] Seq=0 Ack=1 Win=65535 Len=0",
            wire_data=tcp_synack_wire,
            metadata={"transport": "TCP", "flags": "SYN, ACK", "seq": 5000001, "ack": 1000002},
        )
    )

    # Step 5: TCP ACK
    tcp_ack_wire = (
        f"+-------------------------------------------------------------------------+\n"
        f"| Transmission Control Protocol (TCP), Src Port: {client_port}, Dst Port: 80       |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"| Sequence Number: 1000002 (relative 1)                                   |\n"
        f"| Acknowledgment Number: 5000002 (relative 1)                             |\n"
        f"| Flags: 0x010 (ACK) [Handshake Established]                              |\n"
        f"+-------------------------------------------------------------------------+\n"
    )
    events.append(
        ProtocolEvent(
            sequence=5,
            protocol="TCP",
            direction="client_to_server",
            source=f"{client_ip}:{client_port}",
            destination=web_server,
            summary="[ACK] Seq=1 Ack=1 Win=65535 Len=0 (3-Way Handshake Established)",
            wire_data=tcp_ack_wire,
            metadata={"transport": "TCP", "flags": "ACK", "seq": 1000002, "ack": 5000002},
        )
    )

    # Step 6: HTTP/1.1 GET Request
    http_req_text = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {hostname}\r\n"
        f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetSimulator/1.0\r\n"
        f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
        f"Connection: keep-alive\r\n"
        f"\r\n"
    )
    http_req_wire = (
        f"+-------------------------------------------------------------------------+\n"
        f"| Hypertext Transfer Protocol (HTTP/1.1 Request) - TCP Port 80            |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"{http_req_text}"
    )
    events.append(
        ProtocolEvent(
            sequence=6,
            protocol="HTTP",
            direction="client_to_server",
            source=f"{client_ip}:{client_port}",
            destination=web_server,
            summary=f"GET {path} HTTP/1.1 (Host: {hostname}, Connection: keep-alive)",
            wire_data=http_req_wire,
            metadata={
                "method": "GET",
                "path": path,
                "version": "HTTP/1.1",
                "headers": {
                    "Host": hostname,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetSimulator/1.0",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Connection": "keep-alive",
                },
            },
        )
    )

    # Step 7: HTTP 200 OK Response
    html_body = (
        f"<!DOCTYPE html>\n"
        f"<html lang=\"en\">\n"
        f"<head>\n"
        f"  <meta charset=\"UTF-8\">\n"
        f"  <title>{hostname} - Welcome</title>\n"
        f"</head>\n"
        f"<body>\n"
        f"  <h1>Welcome to {hostname}!</h1>\n"
        f"  <p>This page was served directly via HTTP/1.1 over TCP port 80.</p>\n"
        f"  <p>Resource Path: <code>{path}</code></p>\n"
        f"  <footer>RFC 2616 Educational Protocol Simulator</footer>\n"
        f"</body>\n"
        f"</html>\n"
    )
    content_length = len(html_body.encode("utf-8"))
    date_str = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    http_resp_text = (
        f"HTTP/1.1 200 OK\r\n"
        f"Date: {date_str}\r\n"
        f"Server: Apache/2.4.52 (Ubuntu)\r\n"
        f"Content-Type: text/html; charset=UTF-8\r\n"
        f"Content-Length: {content_length}\r\n"
        f"Connection: keep-alive\r\n"
        f"\r\n"
        f"{html_body}"
    )
    http_resp_wire = (
        f"+-------------------------------------------------------------------------+\n"
        f"| Hypertext Transfer Protocol (HTTP/1.1 Response) - TCP Port 80           |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"{http_resp_text}"
    )
    events.append(
        ProtocolEvent(
            sequence=7,
            protocol="HTTP",
            direction="server_to_client",
            source=web_server,
            destination=f"{client_ip}:{client_port}",
            summary=f"HTTP/1.1 200 OK (text/html, {content_length} bytes)",
            wire_data=http_resp_wire,
            metadata={
                "status_code": 200,
                "reason_phrase": "OK",
                "headers": {
                    "Date": date_str,
                    "Server": "Apache/2.4.52 (Ubuntu)",
                    "Content-Type": "text/html; charset=UTF-8",
                    "Content-Length": str(content_length),
                    "Connection": "keep-alive",
                },
                "body": html_body,
            },
        )
    )

    return events


# ==========================================
# 2. SMTP Email Sequence Generator
# ==========================================

def generate_smtp_sequence(
    sender: str = "alice@example.com",
    recipient: str = "bob@example.com",
    subject: str = "Project Update",
    body: str = "Hello Bob,\n\nThe quarterly network architecture review is completed.\n\nRegards,\nAlice",
) -> List[ProtocolEvent]:
    """
    Simulates complete SMTP conversation (RFC 5321):
    1.  220 Service Ready
    2.  EHLO client.fqdn
    3.  250 ESMTP
    4.  MAIL FROM
    5.  250 OK
    6.  RCPT TO
    7.  250 OK
    8.  DATA
    9.  354 Start Input
    10. MIME headers + body + <CRLF>.<CRLF>
    11. 250 Queued
    12. QUIT
    13. 221 Bye
    Port: TCP port 25
    """
    sender = sender.strip() or "alice@example.com"
    recipient = recipient.strip() or "bob@example.com"
    subject = subject.strip() or "No Subject"

    client_ip = "192.168.1.105"
    client_port = 59124
    smtp_server = "smtp.example.com"
    server_addr = "198.51.100.25:25"
    client_addr = f"{client_ip}:{client_port}"
    client_fqdn = "mailclient.localdomain"

    now_rfc = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    message_id = f"<{random.randint(100000, 999999)}.net-sim@{client_fqdn}>"
    queue_id = f"{random.randint(10000000, 99999999):X}"

    mime_payload = (
        f"From: {sender}\r\n"
        f"To: {recipient}\r\n"
        f"Date: {now_rfc}\r\n"
        f"Subject: {subject}\r\n"
        f"Message-ID: {message_id}\r\n"
        f"MIME-Version: 1.0\r\n"
        f"Content-Type: text/plain; charset=UTF-8\r\n"
        f"Content-Transfer-Encoding: 7bit\r\n"
        f"\r\n"
        f"{body.replace(chr(10), chr(13) + chr(10))}\r\n"
        f".\r\n"
    )

    steps_config = [
        # (Seq, Dir, Command/Reply, Summary, Meta)
        (
            1,
            "server_to_client",
            f"220 {smtp_server} ESMTP Postfix Service Ready\r\n",
            f"220 {smtp_server} ESMTP Postfix Service Ready",
            {"code": 220, "description": "Service Ready"},
        ),
        (
            2,
            "client_to_server",
            f"EHLO {client_fqdn}\r\n",
            f"EHLO {client_fqdn}",
            {"command": "EHLO", "domain": client_fqdn},
        ),
        (
            3,
            "server_to_client",
            f"250-{smtp_server}\r\n250-PIPELINING\r\n250-SIZE 10485760\r\n250-8BITMIME\r\n250 OK\r\n",
            "250 OK (Supported capabilities: PIPELINING, SIZE, 8BITMIME)",
            {"code": 250, "extensions": ["PIPELINING", "SIZE 10485760", "8BITMIME"]},
        ),
        (
            4,
            "client_to_server",
            f"MAIL FROM:<{sender}>\r\n",
            f"MAIL FROM:<{sender}>",
            {"command": "MAIL FROM", "sender": sender},
        ),
        (
            5,
            "server_to_client",
            "250 2.1.0 Ok\r\n",
            "250 2.1.0 Ok (Sender accepted)",
            {"code": 250, "status": "Sender accepted"},
        ),
        (
            6,
            "client_to_server",
            f"RCPT TO:<{recipient}>\r\n",
            f"RCPT TO:<{recipient}>",
            {"command": "RCPT TO", "recipient": recipient},
        ),
        (
            7,
            "server_to_client",
            "250 2.1.5 Ok recipient ok\r\n",
            "250 2.1.5 Ok (Recipient accepted)",
            {"code": 250, "status": "Recipient accepted"},
        ),
        (
            8,
            "client_to_server",
            "DATA\r\n",
            "DATA (Client requesting permission to transmit message body)",
            {"command": "DATA"},
        ),
        (
            9,
            "server_to_client",
            "354 End data with <CR><LF>.<CR><LF>\r\n",
            "354 Start mail input; end with <CRLF>.<CRLF>",
            {"code": 354, "status": "Start Input"},
        ),
        (
            10,
            "client_to_server",
            mime_payload,
            f"MIME Message Body ({len(mime_payload)} bytes, Subject: {subject})",
            {
                "command": "PAYLOAD",
                "headers": {
                    "From": sender,
                    "To": recipient,
                    "Subject": subject,
                    "Date": now_rfc,
                },
                "body": body,
            },
        ),
        (
            11,
            "server_to_client",
            f"250 2.0.0 Ok: queued as {queue_id}\r\n",
            f"250 2.0.0 Ok: queued as {queue_id}",
            {"code": 250, "queue_id": queue_id},
        ),
        (
            12,
            "client_to_server",
            "QUIT\r\n",
            "QUIT (Client closing SMTP session)",
            {"command": "QUIT"},
        ),
        (
            13,
            "server_to_client",
            f"221 2.0.0 Bye\r\n",
            "221 2.0.0 Bye (Service closing transmission channel)",
            {"code": 221, "status": "Bye"},
        ),
    ]

    events: List[ProtocolEvent] = []
    for seq, direction, raw_data, summary, meta in steps_config:
        src = client_addr if direction == "client_to_server" else server_addr
        dst = server_addr if direction == "client_to_server" else client_addr
        wire_hdr = (
            f"+-------------------------------------------------------------------------+\n"
            f"| Simple Mail Transfer Protocol (SMTP, RFC 5321) - TCP Port 25            |\n"
            f"| Direction: {direction.replace('_', ' ').title():<59} |\n"
            f"+-------------------------------------------------------------------------+\n"
        )
        events.append(
            ProtocolEvent(
                sequence=seq,
                protocol="SMTP",
                direction=direction,
                source=src,
                destination=dst,
                summary=summary,
                wire_data=wire_hdr + raw_data,
                metadata={"port": 25, **meta},
            )
        )

    return events


# ==========================================
# 3. HLS Video Streaming Sequence Generator
# ==========================================

def generate_hls_sequence(
    stream_name: str = "live/stream1",
    selected_bitrate: str = "720p",
) -> List[ProtocolEvent]:
    """
    Simulates HTTP Live Streaming (HLS, RFC 8216):
    - DNS lookup for CDN hostname (e.g. cdn.videoedge.net)
    - Master playlist request (master.m3u8)
    - Master playlist response (Available bitrate variants: 1080p, 720p, 360p)
    - Variant playlist request (e.g. 720p/playlist.m3u8)
    - Variant playlist response (4-second MPEG-TS segments)
    - Progressive HTTP GET requests for 4-second segments:
      segment_000.ts, segment_001.ts, segment_002.ts, segment_003.ts
    - Progressive buffer-health calculation (dynamic segment downloading)
    """
    cdn_host = "cdn.videoedge.net"
    cdn_ip = "198.51.100.42"
    client_ip = "192.168.1.105"
    client_port = 57890
    dns_server = "8.8.8.8:53"
    cdn_addr = f"{cdn_ip}:80"
    client_addr = f"{client_ip}:{client_port}"

    # Supported bitrates
    bitrate_map = {
        "1080p": {"bandwidth": 5000000, "resolution": "1920x1080", "codecs": "avc1.64002a,mp4a.40.2"},
        "720p": {"bandwidth": 2500000, "resolution": "1280x720", "codecs": "avc1.4d401f,mp4a.40.2"},
        "360p": {"bandwidth": 800000, "resolution": "640x360", "codecs": "avc1.42e01e,mp4a.40.2"},
    }
    variant_info = bitrate_map.get(selected_bitrate, bitrate_map["720p"])

    events: List[ProtocolEvent] = []
    seq = 1

    # 1. DNS Query for CDN Hostname
    dns_query_wire = (
        f"+-------------------------------------------------------------------------+\n"
        f"| User Datagram Protocol (UDP), Src Port: {client_port}, Dst Port: 53             |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"| Domain Name System (Query)                                              |\n"
        f"| Transaction ID: 0x4a12  Flags: 0x0100 (Standard query, Recursion Desired) |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"Query: {cdn_host}\n"
        f"Type: A (Host Address) (1), Class: IN (0x0001)\n"
    )
    events.append(
        ProtocolEvent(
            sequence=seq,
            protocol="DNS",
            direction="client_to_server",
            source=client_addr,
            destination=dns_server,
            summary=f"DNS Query A {cdn_host} (Resolve CDN edge node)",
            wire_data=dns_query_wire,
            metadata={"port": 53, "query": cdn_host, "type": "DNS Query"},
        )
    )
    seq += 1

    # 2. DNS Response for CDN Hostname
    dns_resp_wire = (
        f"+-------------------------------------------------------------------------+\n"
        f"| User Datagram Protocol (UDP), Src Port: 53, Dst Port: {client_port}             |\n"
        f"+-------------------------------------------------------------------------+\n"
        f"| Domain Name System (Response)                                           |\n"
        f"| Answers: {cdn_host} -> {cdn_ip} (TTL 300s)                              |\n"
        f"+-------------------------------------------------------------------------+\n"
    )
    events.append(
        ProtocolEvent(
            sequence=seq,
            protocol="DNS",
            direction="server_to_client",
            source=dns_server,
            destination=client_addr,
            summary=f"DNS Response {cdn_host} -> {cdn_ip} (TTL 300s)",
            wire_data=dns_resp_wire,
            metadata={"port": 53, "resolved_ip": cdn_ip, "ttl": 300},
        )
    )
    seq += 1

    # 3. Master Playlist Request (master.m3u8)
    master_req_text = (
        f"GET /{stream_name}/master.m3u8 HTTP/1.1\r\n"
        f"Host: {cdn_host}\r\n"
        f"User-Agent: HLSPlayer/3.2 (WebClient)\r\n"
        f"Accept: application/vnd.apple.mpegurl, application/x-mpegURL, */*\r\n"
        f"Connection: keep-alive\r\n"
        f"\r\n"
    )
    events.append(
        ProtocolEvent(
            sequence=seq,
            protocol="HTTP",
            direction="client_to_server",
            source=client_addr,
            destination=cdn_addr,
            summary=f"GET /{stream_name}/master.m3u8 HTTP/1.1 (Request Master Manifest)",
            wire_data=(
                f"+-------------------------------------------------------------------------+\n"
                f"| HTTP/1.1 Request: Master Playlist (RFC 8216)                            |\n"
                f"+-------------------------------------------------------------------------+\n"
                f"{master_req_text}"
            ),
            metadata={"stage": "master_manifest_req", "uri": f"/{stream_name}/master.m3u8"},
        )
    )
    seq += 1

    # 4. Master Playlist Response
    master_body = (
        f"#EXTM3U\n"
        f"#EXT-X-VERSION:3\n"
        f"#EXT-X-INDEPENDENT-SEGMENTS\n"
        f"#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS=\"avc1.42e01e,mp4a.40.2\"\n"
        f"360p/playlist.m3u8\n"
        f"#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720,CODECS=\"avc1.4d401f,mp4a.40.2\"\n"
        f"720p/playlist.m3u8\n"
        f"#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080,CODECS=\"avc1.64002a,mp4a.40.2\"\n"
        f"1080p/playlist.m3u8\n"
    )
    master_resp_text = (
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: application/vnd.apple.mpegurl\r\n"
        f"Content-Length: {len(master_body.encode())}\r\n"
        f"Server: CloudCDN/2.1\r\n"
        f"Access-Control-Allow-Origin: *\r\n"
        f"\r\n"
        f"{master_body}"
    )
    events.append(
        ProtocolEvent(
            sequence=seq,
            protocol="HLS",
            direction="server_to_client",
            source=cdn_addr,
            destination=client_addr,
            summary="HTTP 200 OK (Master Playlist delivered: 360p, 720p, 1080p variants)",
            wire_data=(
                f"+-------------------------------------------------------------------------+\n"
                f"| HLS Master Playlist Delivered (RFC 8216)                                |\n"
                f"+-------------------------------------------------------------------------+\n"
                f"{master_resp_text}"
            ),
            metadata={
                "stage": "master_manifest_resp",
                "variants": ["360p (800kbps)", "720p (2.5Mbps)", "1080p (5Mbps)"],
                "body": master_body,
            },
        )
    )
    seq += 1

    # 5. Variant Playlist Request
    variant_req_text = (
        f"GET /{stream_name}/{selected_bitrate}/playlist.m3u8 HTTP/1.1\r\n"
        f"Host: {cdn_host}\r\n"
        f"User-Agent: HLSPlayer/3.2 (WebClient)\r\n"
        f"Accept: application/vnd.apple.mpegurl\r\n"
        f"Connection: keep-alive\r\n"
        f"\r\n"
    )
    events.append(
        ProtocolEvent(
            sequence=seq,
            protocol="HTTP",
            direction="client_to_server",
            source=client_addr,
            destination=cdn_addr,
            summary=f"GET /{stream_name}/{selected_bitrate}/playlist.m3u8 HTTP/1.1 (Request {selected_bitrate} Media Playlist)",
            wire_data=(
                f"+-------------------------------------------------------------------------+\n"
                f"| HTTP/1.1 Request: Variant Playlist ({selected_bitrate})                 |\n"
                f"+-------------------------------------------------------------------------+\n"
                f"{variant_req_text}"
            ),
            metadata={"stage": "variant_manifest_req", "selected_bitrate": selected_bitrate},
        )
    )
    seq += 1

    # 6. Variant Playlist Response
    variant_body = (
        f"#EXTM3U\n"
        f"#EXT-X-VERSION:3\n"
        f"#EXT-X-TARGETDURATION:4\n"
        f"#EXT-X-MEDIA-SEQUENCE:0\n"
        f"#EXTINF:4.000,\n"
        f"segment_000.ts\n"
        f"#EXTINF:4.000,\n"
        f"segment_001.ts\n"
        f"#EXTINF:4.000,\n"
        f"segment_002.ts\n"
        f"#EXTINF:4.000,\n"
        f"segment_003.ts\n"
    )
    variant_resp_text = (
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: application/vnd.apple.mpegurl\r\n"
        f"Content-Length: {len(variant_body.encode())}\r\n"
        f"Server: CloudCDN/2.1\r\n"
        f"\r\n"
        f"{variant_body}"
    )
    events.append(
        ProtocolEvent(
            sequence=seq,
            protocol="HLS",
            direction="server_to_client",
            source=cdn_addr,
            destination=client_addr,
            summary=f"HTTP 200 OK (Variant Playlist: TargetDuration=4s, 4 TS segments)",
            wire_data=(
                f"+-------------------------------------------------------------------------+\n"
                f"| HLS Media Playlist ({selected_bitrate}) Delivered (RFC 8216)            |\n"
                f"+-------------------------------------------------------------------------+\n"
                f"{variant_resp_text}"
            ),
            metadata={
                "stage": "variant_manifest_resp",
                "target_duration": 4.0,
                "segments": ["segment_000.ts", "segment_001.ts", "segment_002.ts", "segment_003.ts"],
                "body": variant_body,
            },
        )
    )
    seq += 1

    # 7..14. Progressive Segment Downloads (4 segments: request + response each)
    buffer_sec = 0.0
    for seg_idx in range(4):
        seg_name = f"segment_{seg_idx:03d}.ts"
        seg_size_bytes = int((variant_info["bandwidth"] / 8) * 4)  # 4 seconds worth of data
        seg_size_kb = seg_size_bytes // 1024

        # Request
        seg_req_text = (
            f"GET /{stream_name}/{selected_bitrate}/{seg_name} HTTP/1.1\r\n"
            f"Host: {cdn_host}\r\n"
            f"User-Agent: HLSPlayer/3.2 (WebClient)\r\n"
            f"Accept: video/MP2T, */*\r\n"
            f"Range: bytes=0-\r\n"
            f"Connection: keep-alive\r\n"
            f"\r\n"
        )
        events.append(
            ProtocolEvent(
                sequence=seq,
                protocol="HTTP",
                direction="client_to_server",
                source=client_addr,
                destination=cdn_addr,
                summary=f"GET /{selected_bitrate}/{seg_name} HTTP/1.1 (Request 4.0s MPEG-TS)",
                wire_data=(
                    f"+-------------------------------------------------------------------------+\n"
                    f"| HTTP/1.1 Segment Request ({seg_name})                                   |\n"
                    f"+-------------------------------------------------------------------------+\n"
                    f"{seg_req_text}"
                ),
                metadata={
                    "segment": seg_name,
                    "bitrate": selected_bitrate,
                    "buffer_health_sec": buffer_sec,
                },
            )
        )
        seq += 1

        # Response
        buffer_sec += 4.0
        dummy_hex = f"47 40 11 10 00 42 f0 25 00 01 c1 00 00 ff ff ff\n47 01 00 11 00 02 b0 1d 00 01 c1 00 00 e1 00 e1"
        seg_resp_text = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: video/MP2T\r\n"
            f"Content-Length: {seg_size_bytes}\r\n"
            f"Server: CloudCDN/2.1\r\n"
            f"Accept-Ranges: bytes\r\n"
            f"\r\n"
            f"[MPEG-2 Transport Stream Sync Byte 0x47 ... ({seg_size_kb} KB video data)]\n\n"
            f"Hex preview:\n{dummy_hex}"
        )
        events.append(
            ProtocolEvent(
                sequence=seq,
                protocol="HLS",
                direction="server_to_client",
                source=cdn_addr,
                destination=client_addr,
                summary=f"HTTP 200 OK ({seg_name} [4s, {seg_size_kb} KB] -> Buffer: {buffer_sec:.1f}s)",
                wire_data=(
                    f"+-------------------------------------------------------------------------+\n"
                    f"| HLS MPEG-TS Packet Ingest ({seg_name})                                  |\n"
                    f"+-------------------------------------------------------------------------+\n"
                    f"{seg_resp_text}"
                ),
                metadata={
                    "segment": seg_name,
                    "bitrate": selected_bitrate,
                    "segment_duration_sec": 4.0,
                    "size_bytes": seg_size_bytes,
                    "buffer_health_sec": buffer_sec,
                    "resolution": variant_info["resolution"],
                },
            )
        )
        seq += 1

    return events
