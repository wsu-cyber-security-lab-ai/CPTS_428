#!/usr/bin/env python3
"""
CrimsonCart Receipts - IDOR Lab
================================
A small, self-contained web app for teaching Insecure Direct Object
Reference (IDOR) / broken access control.

Uses ONLY the Python standard library (http.server). No external
packages, no network calls, no database. Fully deterministic.

Run:
    python3 server.py
Then visit:
    http://localhost:8000/lab
"""

import html
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# Cloud hosts (Render, Replit, etc.) assign a port via the PORT environment
# variable. Locally, nothing sets that, so it falls back to 8000.
PORT = int(os.environ.get("PORT", 8000))
IS_CLOUD = "PORT" in os.environ

# ---------------------------------------------------------------------------
# Fixed, deterministic receipt data. This is the ONLY place the flag lives.
# The server does not check who is "logged in" - it just looks up whatever
# id the client asks for. That is the entire vulnerability.
# ---------------------------------------------------------------------------
RECEIPTS = {
    1001: {
        "buyer": "Alex Chen",
        "role": "Student",
        "item": "CPTS 428 Course Pack (used)",
        "amount": "$18.00",
        "date": "2026-09-02",
    },
    1002: {
        "buyer": "Priya Patel",
        "role": "Student",
        "item": "Graphing Calculator",
        "amount": "$64.99",
        "date": "2026-09-03",
    },
    1003: {
        "buyer": "Jordan Miles",
        "role": "Student",
        "item": "WSU Hoodie (M)",
        "amount": "$39.50",
        "date": "2026-09-04",
    },
    1004: {
        "buyer": "R. Whitfield",
        "role": "Procurement Office",
        "item": "Site License - Campus Network Monitoring Suite",
        "amount": "$4,200.00",
        "date": "2026-08-21",
        "flag": "CRIMSON{ids_are_not_access_control}",
    },
    1005: {
        "buyer": "Sam Okafor",
        "role": "Student",
        "item": "Lab Notebook + Pens",
        "amount": "$11.25",
        "date": "2026-09-05",
    },
}

DEFAULT_ID = 1001


def page(title, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} - CrimsonCart Receipts</title>
<style>
  :root {{ --crimson:#a6192e; --ink:#1a1a2e; --muted:#6b6b6b; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; margin:0;
         background:#f7f7f9; color:#222; }}
  header {{ background:var(--ink); padding:16px 24px; }}
  header .brand {{ color:#fff; font-weight:bold; font-size:19px; }}
  header .sub {{ color:#9aa3b2; font-size:12px; margin-top:2px; }}
  main {{ max-width:640px; margin:50px auto; padding:0 20px; }}
  h1 {{ font-size:24px; margin-bottom:6px; }}
  p.lede {{ color:var(--muted); margin-top:0; }}
  .card {{ background:#fff; border:1px solid #e6e6ea; border-radius:10px;
          padding:24px; margin-top:20px; }}
  .row {{ display:flex; justify-content:space-between; padding:8px 0;
         border-bottom:1px solid #f0f0f2; font-size:14px; }}
  .row:last-child {{ border-bottom:none; }}
  .row .k {{ color:var(--muted); }}
  .row .v {{ font-weight:600; text-align:right; }}
  .badge {{ display:inline-block; background:#fff0f1; color:var(--crimson);
            border:1px solid var(--crimson); border-radius:20px; padding:2px 10px;
            font-size:12px; font-weight:bold; margin-bottom:10px; }}
  .flag {{ margin-top:16px; font-size:16px; font-weight:bold; color:var(--crimson);
          background:#fff0f1; border:1px dashed var(--crimson); padding:12px;
          border-radius:8px; }}
  input[type=text] {{ padding:9px 12px; border:1px solid #ccc; border-radius:6px;
          font-size:14px; width:160px; }}
  button {{ background:var(--crimson); color:#fff; border:none; padding:9px 16px;
           border-radius:6px; font-size:14px; cursor:pointer; margin-left:6px; }}
  button:hover {{ opacity:.92; }}
  .error {{ color:var(--crimson); font-weight:bold; }}
  code {{ background:#f1f1f4; padding:1px 5px; border-radius:4px; }}
  footer {{ max-width:640px; margin:30px auto; padding:0 20px 40px; color:#999; font-size:12px; }}
</style>
</head>
<body>
<header>
  <div class="brand">CrimsonCart Receipts</div>
  <div class="sub">Campus marketplace &middot; order history</div>
</header>
<main>
{body}
</main>
<footer>CrimsonCart Receipts &mdash; internal lab build. Not a real store.</footer>
</body></html>"""


def render_landing():
    body = """
    <h1>Your Receipts</h1>
    <p class="lede">Look up an order receipt by its receipt number.</p>
    <div class="card">
      <form method="GET" action="/lab/receipt">
        <label for="id">Receipt ID</label><br><br>
        <input type="text" id="id" name="id" placeholder="e.g. 1001" autocomplete="off">
        <button type="submit">View Receipt</button>
      </form>
      <p style="margin-top:16px; color:#6b6b6b; font-size:13px;">
        Receipts are private and tied to the account that made the purchase.
      </p>
    </div>
    """
    return page("Receipts", body)


def render_receipt(raw_id):
    if raw_id is None or raw_id.strip() == "":
        rid = DEFAULT_ID
    else:
        try:
            rid = int(raw_id.strip())
        except ValueError:
            body = f"""
            <h1>Receipt</h1>
            <div class="card">
              <p class="error">That doesn't look like a valid receipt ID.</p>
              <p><a href="/lab">Back to receipts</a></p>
            </div>
            """
            return page("Invalid receipt", body)

    receipt = RECEIPTS.get(rid)

    if receipt is None:
        body = f"""
        <h1>Receipt #{rid}</h1>
        <div class="card">
          <p class="error">No receipt found with that ID.</p>
          <p><a href="/lab">Back to receipts</a></p>
        </div>
        """
        return page("Not found", body)

    flag_html = ""
    if "flag" in receipt:
        flag_html = f'<div class="flag">{html.escape(receipt["flag"])}</div>'

    rows = "".join(
        f'<div class="row"><span class="k">{html.escape(k.capitalize())}</span>'
        f'<span class="v">{html.escape(str(v))}</span></div>'
        for k, v in receipt.items() if k != "flag"
    )

    body = f"""
    <h1>Receipt #{rid}</h1>
    <span class="badge">Private &mdash; buyer only</span>
    <div class="card">
      {rows}
      {flag_html}
    </div>
    <p style="margin-top:16px;"><a href="/lab">&larr; Back to receipts</a></p>
    """
    return page(f"Receipt #{rid}", body)


class Handler(BaseHTTPRequestHandler):
    server_version = "CrimsonCartLab/1.0"

    def log_message(self, fmt, *args):
        # quieter, single-line request log
        print(f"[{self.address_string()}] {fmt % args}")

    def _send_html(self, html_body, status=200):
        encoded = html_body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/" or path == "/lab":
            self._send_html(render_landing())
        elif path == "/lab/receipt":
            raw_id = query.get("id", [None])[0]
            self._send_html(render_receipt(raw_id))
        else:
            self._send_html(page("Not found", "<h1>404</h1><p><a href='/lab'>Go to /lab</a></p>"), status=404)


def main():
    url = f"http://localhost:{PORT}/lab"
    try:
        server = HTTPServer(("0.0.0.0", PORT), Handler)
    except OSError:
        print(f"Could not start on port {PORT} - it's already in use.")
        print("Close whatever else is using it, or edit PORT near the top of server.py.")
        sys.exit(1)

    print(f"CrimsonCart Receipts lab running at {url}")
    print("Press Ctrl+C to stop.")

    # Only try to pop open a local browser window when actually running on
    # someone's own machine - on a cloud host there's no desktop to open.
    if not IS_CLOUD:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        server.server_close()


if __name__ == "__main__":
    main()
