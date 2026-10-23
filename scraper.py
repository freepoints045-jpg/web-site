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
            print("Navigating to main page...")
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            cards = page.query_selector_all(".movie-card, article, .post")
            print(f"Found {len(cards)} movie cards.")
            
            # প্রথম ১২টি মুভি স্ক্র্যাপ করা হচ্ছে (টাইমআউট এড়াতে)
            for card in cards[:12]:
                img = card.query_selector("img")
                link = card.query_selector("a")
                title_elem = card.query_selector(".title, h2, h3")

                if img and link:
                    title = title_elem.inner_text().strip() if title_elem else "Unknown Movie"
                    poster = img.get_attribute("src") or img.get_attribute("data-src") or ""
                    movie_page_url = link.get_attribute("href") or ""

                    if movie_page_url and not movie_page_url.startswith("http"):
                        movie_page_url = TARGET_URL.rstrip('/') + '/' + movie_page_url.lstrip('/')

                    print(f"Extracting video link for: {title}")
                    
                    # মুভির ভেতরের পেজে প্রবেশ করে iframe src খোঁজা
                    embed_url = ""
                    try:
                        detail_page = context.new_page()
                        detail_page.goto(movie_page_url, wait_until="domcontentloaded", timeout=30000)
                        detail_page.wait_for_timeout(3000)
                        
                        # পেজের ভেতরের iframe এলিমেন্ট নির্বাচন করা
                        iframe_elem = detail_page.query_selector("iframe")
                        if iframe_elem:
                            embed_url = iframe_elem.get_attribute("src") or ""
                        
                        detail_page.close()
                    except Exception as e:
                        print(f"Error fetching inner page {movie_page_url}: {e}")
                        embed_url = movie_page_url

                    if not embed_url:
                        embed_url = movie_page_url

                    movies.append({
                        "title": title,
                        "poster": poster,
                        "embed_url": embed_url
                    })
        except Exception as e:
            print("Error during scraping:", e)
        finally:
            browser.close()

    if movies:
        with open("movies.json", "w", encoding="utf-8") as f:
            json.dump(movies, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(movies)} movies with direct player links.")

if __name__ == "__main__":
    scrape_movies()
