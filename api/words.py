from http.server import BaseHTTPRequestHandler
import json
import requests
import os

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")


def get_plain_text(prop):
    if not prop:
        return ""
    for key in ("title", "rich_text"):
        items = prop.get(key)
        if items:
            return items[0].get("plain_text", "")
    return ""


def fetch_words():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    results = []
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = requests.post(url, headers=headers, json=body, timeout=30)
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    debug_props = list(results[0]["properties"].keys()) if results else []
    words = []
    for page in results:
        props = page.get("properties", {})
        word = get_plain_text(props.get("英語"))
        pronunciation = get_plain_text(props.get("発音"))
        translation = get_plain_text(props.get("和訳"))
        memo = get_plain_text(props.get("メモ"))
        if word and translation:
            words.append({
                "word": word,
                "pronunciation": pronunciation,
                "translation": translation,
                "memo": memo,
            })
    return words, debug_props


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not NOTION_API_KEY or not DATABASE_ID:
            self._send(500, {
                "success": False,
                "error": "環境変数 NOTION_API_KEY または DATABASE_ID が未設定です。",
            })
            return
        try:
            words, debug_props = fetch_words()
            response = {"success": True, "words": words, "count": len(words)}
            if len(words) == 0 and debug_props:
                response["debug_properties"] = debug_props
            self._send(200, response)
        except requests.HTTPError as e:
            code = e.response.status_code if e.response else "?"
            body = e.response.text[:200] if e.response else str(e)
            self._send(500, {"success": False, "error": f"Notion API エラー (HTTP {code}): {body}"})
        except requests.exceptions.RequestException as e:
            self._send(500, {"success": False, "error": f"接続エラー: {str(e)}"})
        except Exception as e:
            self._send(500, {"success": False, "error": f"{type(e).__name__}: {str(e)}"})

    def _send(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
