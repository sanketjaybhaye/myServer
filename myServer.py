import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            files = os.listdir(UPLOAD_DIR)
            file_list = "<ul>"
            for f in files:
                file_list += f"<li>{f} - <a href='/download/{f}'>Download</a> | <a href='/delete/{f}'>Delete</a></li>"
            file_list += "</ul>"

            html = f"""
            <html><body>
            <h1>Kali Web Server</h1>
            <form enctype='multipart/form-data' method='post'>
                <input type='file' name='file'>
                <input type='submit' value='Upload'>
            </form>
            <h3>Uploaded Files:</h3>{file_list}
            </body></html>
            """
            self.respond(html)
        
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
                self.respond(f"<h1>{filename} Deleted Successfully!</h1><a href='/'>Back</a>")
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
            self.respond("<h1>No file part in form!</h1>", 400)

    def respond(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def run(server_class=HTTPServer, handler_class=MyServer, port=8080):
    print(f"[*] Listening on 0.0.0.0:{port}")
    server = server_class(('0.0.0.0', port), handler_class)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server stopped.")
        server.server_close()

if __name__ == "__main__":
    run()
