import os
import requests
from requests.auth import HTTPBasicAuth

CATEGORIES = [
    "Amazon", "CMO", "Creative", "SEO", "PPC",
    "News", "Industry Insights", "Social", "Feed Management"
]

def detect_category(title: str, content: str) -> list[str]:
    """Use Claude API to pick the best categories for the post."""
    try:
        snippet = content[:1500]
        prompt = f"""You are helping categorize a blog post for a digital marketing agency.

Available categories: {", ".join(CATEGORIES)}

Post title: {title}

Post content (first section):
{snippet}

Reply with ONLY the matching category names from the list above, comma separated.
Only include categories that are a strong match. Most posts will have 1-2 categories.
Nothing else, no explanation."""

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )

        if response.status_code == 200:
            raw = response.json()["content"][0]["text"].strip()
            detected = [c.strip() for c in raw.split(",") if c.strip() in CATEGORIES]
            if detected:
                print(f"   🏷️  Categories detected: {', '.join(detected)}")
                return detected
            else:
                print(f"   ⚠️ No matching categories found")
                return []
        else:
            print(f"   ⚠️ Category detection failed: {response.text}")
            return []

    except Exception as e:
        print(f"   ⚠️ Category error: {e}")
        return []


def get_category_id(category_name: str, wp_url: str, wp_user: str, wp_pass: str) -> int | None:
    """Look up the WordPress category ID by name."""
    try:
        response = requests.get(
            f"{wp_url}/wp-json/wp/v2/categories",
            params={"search": category_name, "per_page": 10},
            auth=HTTPBasicAuth(wp_user, wp_pass),
            timeout=10,
        )
        if response.status_code == 200:
            results = response.json()
            for cat in results:
                if cat["name"].lower() == category_name.lower():
                    return cat["id"]
        return None
    except Exception as e:
        print(f"   ⚠️ Could not fetch category ID: {e}")
        return None
