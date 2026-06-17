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
