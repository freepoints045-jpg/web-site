import json
from playwright.sync_api import sync_playwright

TARGET_URL = "https://yju7zm.movielinkbd.at/"

def scrape_movies():
    movies = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        try:
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            cards = page.query_selector_all(".movie-card, article, .post")
            for card in cards[:20]:
                img = card.query_selector("img")
                link = card.query_selector("a")
                title_elem = card.query_selector(".title, h2, h3")

                if img and link:
                    title = title_elem.inner_text().strip() if title_elem else "Unknown Movie"
                    poster = img.get_attribute("src") or img.get_attribute("data-src") or ""
                    movie_url = link.get_attribute("href") or ""

                    if movie_url and not movie_url.startswith("http"):
                        movie_url = TARGET_URL.rstrip('/') + '/' + movie_url.lstrip('/')

                    movies.append({
                        "title": title,
                        "poster": poster,
                        "embed_url": movie_url
                    })
        except Exception as e:
            print("Error during scraping:", e)
        finally:
            browser.close()

    if movies:
        with open("movies.json", "w", encoding="utf-8") as f:
            json.dump(movies, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(movies)} movies to movies.json")

if __name__ == "__main__":
    scrape_movies()
