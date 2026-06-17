from bs4 import BeautifulSoup
from app.images import upload_image_to_wordpress


def clean_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup.find_all(["style", "script"]):
        tag.decompose()

    for tag in soup.find_all(True):
        tag.attrs = {
            k: v for k, v in tag.attrs.items()
            if k in ("href", "src", "alt", "target", "rel")
        }

    for p in soup.find_all("p"):
        if not p.get_text(strip=True) and not p.find("img"):
            p.decompose()

    blocks = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "img", "blockquote"]):
        text = tag.get_text(strip=True)

        if tag.name == "h1":
            blocks.append(f'<!-- wp:heading {{"level":1}} -->\n<h1>{text}</h1>\n<!-- /wp:heading -->')
        elif tag.name == "h2":
            blocks.append(f'<!-- wp:heading -->\n<h2>{text}</h2>\n<!-- /wp:heading -->')
        elif tag.name == "h3":
            blocks.append(f'<!-- wp:heading {{"level":3}} -->\n<h3>{text}</h3>\n<!-- /wp:heading -->')
        elif tag.name == "h4":
            blocks.append(f'<!-- wp:heading {{"level":4}} -->\n<h4>{text}</h4>\n<!-- /wp:heading -->')
        elif tag.name == "p":
            if text:
                # Check if paragraph contains an image
                img = tag.find("img")
                if img and img.get("src"):
                    wp_url = upload_image_to_wordpress(img["src"])
                    if wp_url:
                        alt = img.get("alt", "")
                        blocks.append(f'<!-- wp:image -->\n<figure class="wp-block-image"><img src="{wp_url}" alt="{alt}"/></figure>\n<!-- /wp:image -->')
                else:
                    inner = str(tag.decode_contents())
                    blocks.append(f'<!-- wp:paragraph -->\n<p>{inner}</p>\n<!-- /wp:paragraph -->')
        elif tag.name == "img":
            src = tag.get("src")
            if src:
                wp_url = upload_image_to_wordpress(src)
                if wp_url:
                    alt = tag.get("alt", "")
                    blocks.append(f'<!-- wp:image -->\n<figure class="wp-block-image"><img src="{wp_url}" alt="{alt}"/></figure>\n<!-- /wp:image -->')
        elif tag.name == "ul":
            inner = str(tag)
            blocks.append(f'<!-- wp:list -->\n{inner}\n<!-- /wp:list -->')
        elif tag.name == "ol":
            inner = str(tag)
            blocks.append(f'<!-- wp:list {{"ordered":true}} -->\n{inner}\n<!-- /wp:list -->')
        elif tag.name == "blockquote":
            inner = str(tag.decode_contents())
            blocks.append(f'<!-- wp:quote -->\n<blockquote>{inner}</blockquote>\n<!-- /wp:quote -->')

    return "\n\n".join(blocks)
