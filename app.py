from flask import Flask, render_template, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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

    words = []
    for page in results:
        props = page.get("properties", {})
        word = get_plain_text(props.get("単語"))
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
    return words


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/words")
def api_words():
    if not NOTION_API_KEY or not DATABASE_ID:
        return jsonify({
            "success": False,
            "error": "環境変数 NOTION_API_KEY または DATABASE_ID が未設定です。.env ファイルを確認してください。",
        })
    try:
        words = fetch_words()
        return jsonify({"success": True, "words": words, "count": len(words)})
    except requests.HTTPError as e:
        code = e.response.status_code if e.response else "?"
        return jsonify({"success": False, "error": f"Notion API エラー (HTTP {code})"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
