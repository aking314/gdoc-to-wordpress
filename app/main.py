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
