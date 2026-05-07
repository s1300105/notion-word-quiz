from http.server import BaseHTTPRequestHandler
import json
import requests
import os

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")


def get_checkboxes(score):
    return {
        "OK":       {"checkbox": score >= 10},
        "もう少し": {"checkbox": 5 <= score < 10},
        "要チェック": {"checkbox": score < 5},
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            page_id = body.get("page_id")
            new_score = int(body.get("new_score", 0))

            props = {"正解数": {"number": new_score}, **get_checkboxes(new_score)}
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{page_id}",
                headers={
                    "Authorization": f"Bearer {NOTION_API_KEY}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28",
                },
                json={"properties": props},
                timeout=10,
            )
            self._send(200 if r.ok else 500, {"ok": r.ok})
        except Exception as e:
            self._send(500, {"ok": False, "error": str(e)})

    def do_OPTIONS(self):
        self._send(204, {})

    def _send(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
