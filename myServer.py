import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
from datetime import datetime

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def human_readable(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kali Web Server</title>
<style>
:root {{
  --bg: #0d1117;
  --card: #161b22;
  --accent: #58a6ff;
  --text: #c9d1d9;
  --danger: #ff5555;
}}
body {{
  font-family: Arial, sans-serif;
  background-color: var(--bg);
  color: var(--text);
  text-align: center;
  margin: 0;
  padding: 20px;
}}
.container {{
  max-width: 700px;
  margin: auto;
  background: var(--card);
  padding: 20px;
  border-radius: 15px;
  box-shadow: 0 0 15px rgba(0,0,0,0.5);
}}
h1 {{
  color: var(--accent);
}}
form {{
  margin: 20px 0;
}}
input[type=file] {{
  padding: 10px;
  border-radius: 5px;
  border: none;
}}
input[type=submit] {{
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
}}
input[type=submit]:hover {{
  background: #1f6feb;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}}
th, td {{
  padding: 10px;
  border-bottom: 1px solid #30363d;
}}
a {{
  color: var(--accent);
  text-decoration: none;
}}
a:hover {{
  text-decoration: underline;
}}
.delete {{
  color: var(--danger);
}}
footer {{
  margin-top: 20px;
  font-size: 0.9em;
  color: #8b949e;
}}
</style>
</head>
<body>
<div class="container">
  <h1>Kali Web Server</h1>
  <form enctype="multipart/form-data" method="post">
    <input type="file" name="file" required>
    <input type="submit" value="Upload">
  </form>
  <p><b>Max file size:</b> {max_size}</p>
  <table>
    <tr><th>File Name</th><th>Size</th><th>Modified</th><th>Actions</th></tr>
    {rows}
  </table>
  <footer>📂 Local File Manager | Kali WebServer V2</footer>
</div>
</body>
</html>
"""

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            files = os.listdir(UPLOAD_DIR)
            rows = ""
            for f in files:
                fp = os.path.join(UPLOAD_DIR, f)
                if os.path.isfile(fp):
                    size = human_readable(os.path.getsize(fp))
                    mtime = datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m-%d %H:%M')
                    rows += f"<tr><td>{f}</td><td>{size}</td><td>{mtime}</td><td><a href='/download/{f}'>Download</a> | <a class='delete' href='/delete/{f}'>Delete</a></td></tr>"

            page = INDEX_HTML.format(rows=rows, max_size=human_readable(MAX_FILE_SIZE))
            self.respond(page)

        elif self.path.startswith("/download/"):
            filename = self.path.split("/download/")[1]
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(filepath):
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f"attachment; filename={filename}")
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.respond("<h1>404 File Not Found</h1>", 404)

        elif self.path.startswith("/delete/"):
            filename = self.path.split("/delete/")[1]
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                self.respond(f"<h1>{filename} deleted successfully.</h1><a href='/'>Back</a>")
            else:
                self.respond("<h1>404 File Not Found</h1>", 404)
        else:
            self.respond("<h1>404 Not Found</h1>", 404)

    def do_POST(self):
        content_type = self.headers.get('Content-Type')
        if not content_type or 'multipart/form-data' not in content_type:
            self.respond("<h1>Invalid Request</h1>", 400)
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': content_type}
        )

        if 'file' in form:
            uploaded_file = form['file']
            if uploaded_file.filename:
                filename = os.path.basename(uploaded_file.filename)
                filepath = os.path.join(UPLOAD_DIR, filename)
                data = uploaded_file.file.read()

                if len(data) > MAX_FILE_SIZE:
                    self.respond("<h1>File too large (limit 100MB)</h1>", 400)
                    return

                with open(filepath, 'wb') as f:
                    f.write(data)
                self.respond(f"<h1>{filename} uploaded successfully!</h1><a href='/'>Back</a>")
            else:
                self.respond("<h1>No file selected!</h1>", 400)
        else:
            self.respond("<h1>No file found in form!</h1>", 400)

    def respond(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

def run(port=8080):
    print(f"Listening on http://0.0.0.0:{port} (uploads -> {UPLOAD_DIR})")
    server = HTTPServer(('0.0.0.0', port), MyServer)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()

if __name__ == "__main__":
    run()
