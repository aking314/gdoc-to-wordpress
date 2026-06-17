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

    # Try <title> tag first
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    # If no title, grab the first h1 from the body
    if not title or title.lower() == "untitled document":
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

    # If still no title, grab the first non-empty paragraph text
    if not title:
        for p in soup.find_all(["p", "h2", "h3"]):
            text = p.get_text(strip=True)
            if text:
                title = text
                break

    title = title or "Untitled Post"

    body = soup.find("body")
    raw_html = str(body) if body else response.text

    return title, raw_html
