import os
import requests
import re
import json


def generate_seo(title: str, content: str) -> dict:
    """Use Claude API to generate a URL slug and meta description."""
    try:
        snippet = content[:2000]
        prompt = f"""You are an SEO expert for a digital marketing agency blog.

Post title: {title}

Post content (first section):
{snippet}

Generate the following and return ONLY a JSON object, nothing else:
{{
    "slug": "url-friendly-slug-here",
    "meta_description": "155 character max meta description here"
}}

Rules:
- slug: lowercase, hyphens only, no special characters, 5-8 words max
- meta_description: compelling, includes main keyword, 140-155 characters max"""

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )

        if response.status_code == 200:
            raw = response.json()["content"][0]["text"].strip()
            raw = re.sub(r"```json|```", "", raw).strip()
            data = json.loads(raw)
            print(f"   🔗 Slug: {data.get('slug')}")
            print(f"   📝 Meta: {data.get('meta_description')}")
            return data
        else:
            print(f"   ⚠️ SEO generation failed: {response.text}")
            return {}

    except Exception as e:
        print(f"   ⚠️ SEO error: {e}")
        return {}
