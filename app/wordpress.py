import os
import requests
from requests.auth import HTTPBasicAuth
from app.category import detect_category, get_category_id
from app.seo import generate_seo


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

    # Auto-detect categories
    category_names = detect_category(title, content)
    category_ids = []
    for name in category_names:
        cat_id = get_category_id(name, wp_url, wp_user, wp_pass)
        if cat_id:
            category_ids.append(cat_id)
            print(f"   ✅ Category assigned: {name} (ID: {cat_id})")

    # Author
    author_id = int(os.getenv("WP_AUTHOR_ID", 0)) or None
    if author_id:
        print(f"   ✅ Author assigned: Steve (ID: {author_id})")

    # SEO
    seo = generate_seo(title, content)
    slug = seo.get("slug", "")
    meta_description = seo.get("meta_description", "")

    payload = {
        "title": title,
        "content": content,
        "status": status,
    }

    if category_ids:
        payload["categories"] = category_ids

    if author_id:
        payload["author"] = author_id

    if slug:
        payload["slug"] = slug
        print(f"   ✅ Slug set: {slug}")

    if meta_description:
        payload["wpseo_description"] = meta_description
        print(f"   ✅ Meta description set")

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
