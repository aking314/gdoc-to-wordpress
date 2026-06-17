#!/bin/bash
# setup.sh — creates all project files for gdoc-to-wordpress

echo "📁 Creating project structure..."
mkdir -p app

# ─── app/__init__.py ───────────────────────────────────────────────
cat > app/__init__.py << 'EOF'
# app package
EOF

# ─── app/gdocs.py ──────────────────────────────────────────────────
cat > app/gdocs.py << 'EOF'
import re
import requests
from bs4 import BeautifulSoup


def extract_doc_id(url_or_id: str) -> str:
    match = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    return url_or_id.strip()


def fetch_google_doc_html(url_or_id: str) -> tuple[str, str]:
    doc_id = extract_doc_id(url_or_id)
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=html"

    response = requests.get(export_url, timeout=15)

    if response.status_code == 403:
        raise ValueError(
            "Google Doc is not publicly accessible. "
            "Share it as 'Anyone with the link can view' and try again."
        )
    if response.status_code != 200:
        raise ValueError(
            f"Failed to fetch Google Doc (HTTP {response.status_code}). "
            "Check that the doc ID or URL is correct."
        )

    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Untitled Post"
    body = soup.find("body")
    raw_html = str(body) if body else response.text

    return title, raw_html
EOF

# ─── app/cleaner.py ────────────────────────────────────────────────
cat > app/cleaner.py << 'EOF'
from bs4 import BeautifulSoup

ALLOWED_TAGS = {
    "p", "br", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "strong", "em", "b", "i", "u", "s",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
    "blockquote", "pre", "code",
    "hr",
}


def clean_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup.find_all(["style", "script"]):
        tag.decompose()

    for tag in soup.find_all(True):
        tag.attrs = {
            k: v for k, v in tag.attrs.items()
            if k in ("href", "src", "alt", "target", "rel")
        }

    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()

    for p in soup.find_all("p"):
        if not p.get_text(strip=True) and not p.find("img"):
            p.decompose()

    for br in soup.find_all("br"):
        next_sib = br.find_next_sibling()
        if next_sib and next_sib.name == "br":
            next_sib.decompose()

    return str(soup)
EOF

# ─── app/wordpress.py ──────────────────────────────────────────────
cat > app/wordpress.py << 'EOF'
import os
import requests
from requests.auth import HTTPBasicAuth


def get_wp_config() -> tuple[str, str, str]:
    url = os.getenv("WP_URL", "").rstrip("/")
    username = os.getenv("WP_USERNAME", "")
    password = os.getenv("WP_APP_PASSWORD", "")

    if not all([url, username, password]):
        raise ValueError(
            "Missing WordPress config. Set WP_URL, WP_USERNAME, "
            "and WP_APP_PASSWORD in your .env file."
        )
    return url, username, password


def post_to_wordpress(title: str, content: str, status: str = "draft") -> dict:
    wp_url, wp_user, wp_pass = get_wp_config()
    endpoint = f"{wp_url}/wp-json/wp/v2/posts"

    payload = {
        "title": title,
        "content": content,
        "status": status,
    }

    response = requests.post(
        endpoint,
        json=payload,
        auth=HTTPBasicAuth(wp_user, wp_pass),
        timeout=20,
    )

    if response.status_code not in (200, 201):
        raise ValueError(
            f"WordPress API error ({response.status_code}): {response.text}"
        )

    return response.json()
EOF

# ─── app/main.py ───────────────────────────────────────────────────
cat > app/main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.gdocs import fetch_google_doc_html
from app.cleaner import clean_html
from app.wordpress import post_to_wordpress

app = FastAPI(title="Google Doc → WordPress Poster")


class PostRequest(BaseModel):
    google_doc_url: str
    wp_title: str | None = None
    wp_status: str = "draft"


@app.post("/post")
def create_post(req: PostRequest):
    try:
        title, raw_html = fetch_google_doc_html(req.google_doc_url)
        clean_content = clean_html(raw_html)
        final_title = req.wp_title or title
        result = post_to_wordpress(final_title, clean_content, req.wp_status)
        return {
            "success": True,
            "wordpress_post_id": result["id"],
            "wordpress_post_url": result["link"],
            "title": final_title,
            "status": req.wp_status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
EOF

# ─── run.py ────────────────────────────────────────────────────────
cat > run.py << 'EOF'
from dotenv import load_dotenv
load_dotenv()

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
EOF

# ─── test_post.py ──────────────────────────────────────────────────
cat > test_post.py << 'EOF'
import sys
from dotenv import load_dotenv
load_dotenv()

from app.gdocs import fetch_google_doc_html
from app.cleaner import clean_html
from app.wordpress import post_to_wordpress


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_post.py <google_doc_url>")
        sys.exit(1)

    url = sys.argv[1]
    status = sys.argv[2] if len(sys.argv) > 2 else "draft"

    print(f"📄 Fetching Google Doc...")
    title, raw_html = fetch_google_doc_html(url)
    print(f"   Title: {title}")

    print(f"🧹 Cleaning HTML...")
    clean_content = clean_html(raw_html)
    print(f"   Done ({len(clean_content)} chars)")

    print(f"🚀 Posting to WordPress as '{status}'...")
    result = post_to_wordpress(title, clean_content, status)
    print(f"   ✅ Post created!")
    print(f"   ID:  {result['id']}")
    print(f"   URL: {result['link']}")


if __name__ == "__main__":
    main()
EOF

# ─── requirements.txt ──────────────────────────────────────────────
cat > requirements.txt << 'EOF'
fastapi==0.111.0
uvicorn[standard]==0.29.0
requests==2.31.0
beautifulsoup4==4.12.3
python-dotenv==1.0.1
pydantic==2.7.1
EOF

# ─── .env.example ──────────────────────────────────────────────────
cat > .env.example << 'EOF'
WP_URL=https://yoursite.com
WP_USERNAME=your_wp_username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
EOF

# ─── .gitignore ────────────────────────────────────────────────────
cat > .gitignore << 'EOF'
.env
venv/
__pycache__/
*.pyc
.DS_Store
EOF

echo ""
echo "✅ All files created! Now run:"
echo ""
echo "   pip install -r requirements.txt"
echo "   cp .env.example .env"
echo "   # edit .env with your WordPress credentials"
echo ""
