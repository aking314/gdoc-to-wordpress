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
