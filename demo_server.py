"""Lightweight local HTTP demo server for testing Playwright MCP browser automation."""

import http.server
import socketserver
import threading
import time
import socket
from pathlib import Path
from config import DEMO_SERVER_PORT, BASE_DIR

STATIC_DIR = BASE_DIR / "static"
DEMO_HTML_FILE = STATIC_DIR / "demo_jobs.html"


class DemoJobPortalHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving the demo jobs portal."""
    
    def do_GET(self):
        # Route /jobs, /, /jobs/* to demo_jobs.html
        if self.path.startswith("/jobs") or self.path == "/":
            if not DEMO_HTML_FILE.exists():
                self.send_error(404, "demo_jobs.html not found")
                return
            
            with open(DEMO_HTML_FILE, "rb") as f:
                content = f.read()
                
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            super().do_GET()

    def log_message(self, format, *args):
        # Suppress noisy standard logs in console
        pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


_server_instance = None
_server_thread = None


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if the demo server port is currently listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def start_demo_server(port: int = DEMO_SERVER_PORT) -> bool:
    """Start the demo HTTP server in a background thread if not already running."""
    global _server_instance, _server_thread
    
    if is_port_in_use(port):
        return True
        
    try:
        _server_instance = ThreadedTCPServer(("127.0.0.1", port), DemoJobPortalHandler)
        _server_thread = threading.Thread(target=_server_instance.serve_forever, daemon=True)
        _server_thread.start()
        # Brief pause to verify startup
        time.sleep(0.3)
        return is_port_in_use(port)
    except Exception as e:
        print(f"Warning: could not start demo server on port {port}: {e}")
        return False


def stop_demo_server() -> None:
    """Stop the demo HTTP server."""
    global _server_instance, _server_thread
    if _server_instance:
        try:
            _server_instance.shutdown()
            _server_instance.server_close()
        except Exception:
            pass
        _server_instance = None
        _server_thread = None


if __name__ == "__main__":
    print(f"Starting TechCareers Demo Portal on http://127.0.0.1:{DEMO_SERVER_PORT}/jobs ...")
    server = ThreadedTCPServer(("127.0.0.1", DEMO_SERVER_PORT), DemoJobPortalHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down demo server.")
        server.shutdown()
