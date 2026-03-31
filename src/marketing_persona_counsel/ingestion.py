import httpx
from bs4 import BeautifulSoup
from pathlib import Path
import frontmatter


def fetch_url_content(url: str) -> tuple[str, str]:
    """Fetch and parse content from a URL. Returns (title, text)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = httpx.get(url, headers=headers, follow_redirects=True)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Simple extraction: title and main content
    title = soup.title.string if soup.title else "Untitled URL"
    
    # Try to find common content areas
    article = soup.find("article") or soup.find("main") or soup.body
    
    # Remove script, style, nav, footer
    for tag in article.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
        
    return title, article.get_text(separator="\n", strip=True)


def load_markdown_content(path: Path) -> tuple[str, str]:
    """Load and parse content from a markdown file. Returns (title, text)."""
    post = frontmatter.load(path)
    title = post.get("title") or path.stem
    return title, post.content
