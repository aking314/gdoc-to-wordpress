import requests
import os
import base64
from requests.auth import HTTPBasicAuth


def upload_image_to_wordpress(img_src: str) -> str | None:
    wp_url = os.getenv("WP_URL", "").rstrip("/")
    wp_user = os.getenv("WP_USERNAME", "")
    wp_pass = os.getenv("WP_APP_PASSWORD", "")

    try:
        # Handle base64 encoded images
        if img_src.startswith("data:image"):
            header, data = img_src.split(",", 1)
            content_type = header.split(";")[0].split(":")[1]
            ext = content_type.split("/")[-1]
            img_data = base64.b64decode(data)
        else:
            # Handle regular URLs
            response = requests.get(img_src, timeout=15)
            if response.status_code != 200:
                print(f"   ⚠️ Could not download image: {img_src}")
                return None
            content_type = response.headers.get("Content-Type", "image/jpeg")
            ext = content_type.split("/")[-1].split(";")[0]
            img_data = response.content

        filename = f"imported-image.{ext}"
        media_endpoint = f"{wp_url}/wp-json/wp/v2/media"

        upload_response = requests.post(
            media_endpoint,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": content_type,
            },
            data=img_data,
            auth=HTTPBasicAuth(wp_user, wp_pass),
            timeout=30,
        )

        if upload_response.status_code in (200, 201):
            media_data = upload_response.json()
            print(f"   ✅ Image uploaded: {media_data['source_url']}")
            return media_data["source_url"]
        else:
            print(f"   ⚠️ Image upload failed: {upload_response.text}")
            return None

    except Exception as e:
        print(f"   ⚠️ Image error: {e}")
        return None
