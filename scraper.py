import json
import re
from playwright.sync_api import sync_playwright

TARGET_URL = "https://yju7zm.movielinkbd.at/"

def scrape_movies():
    movies = []
    with sync_playwright() as p:
        # Browser launch
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print("Fetching main homepage...")
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            cards = page.query_selector_all(".movie-card, article, .post")
            print(f"Total movies found on homepage: {len(cards)}")
            
            # প্রথম ১০টি মুভি স্ক্র্যাপ করা হচ্ছে (Actions-এর টাইমআউট এড়াতে)
            for card in cards[:10]:
                img = card.query_selector("img")
                link = card.query_selector("a")
                title_elem = card.query_selector(".title, h2, h3")

                if img and link:
                    title = title_elem.inner_text().strip() if title_elem else "Unknown Movie"
                    poster = img.get_attribute("src") or img.get_attribute("data-src") or ""
                    movie_page_url = link.get_attribute("href") or ""

                    if movie_page_url and not movie_page_url.startswith("http"):
                        movie_page_url = TARGET_URL.rstrip('/') + '/' + movie_page_url.lstrip('/')

                    print(f"Processing: {title}")
                    
                    stream_url = ""
                    detail_page = context.new_page()
                    
                    # Pop-up window block
                    detail_page.on("popup", lambda p_page: p_page.close())

                    # Network request monitor (ভিডিও ফাইল ধরা)
                    captured_video_url = []
                    def handle_request(request):
                        req_url = request.url
                        if any(ext in req_url for ext in [".mp4", ".m3u8", "master.m3u8"]) and not any(bad in req_url for bad in ["google", "analytics", "doubleclick"]):
                            captured_video_url.append(req_url)

                    detail_page.on("request", handle_request)

                    try:
                        # Detail page-এ নেভিগেট
                        detail_page.goto(movie_page_url, wait_until="domcontentloaded", timeout=30000)
                        detail_page.wait_for_timeout(3000)

                        # ১. নেটওয়ার্ক থেকে যদি ভিডিও লিংক পাওয়া যায়
                        if captured_video_url:
                            stream_url = captured_video_url[0]

                        # ২. যদি না পাওয়া যায়, তবে iframe চেক
                        if not stream_url:
                            iframe = detail_page.query_selector("iframe")
                            if iframe:
                                stream_url = iframe.get_attribute("src") or ""

                        # ৩. রিডাইরেক্ট পেজের জন্য ব্যাকআপ ডাইরেক্ট পেজ ইউআরএল
                        if not stream_url:
                            stream_url = movie_page_url

                    except Exception as e:
                        print(f"Error scraping detail page for {title}: {e}")
                        stream_url = movie_page_url
                    finally:
                        detail_page.close()

                    movies.append({
                        "title": title,
                        "poster": poster,
                        "embed_url": stream_url
                    })

        except Exception as e:
            print("General scraping error:", e)
        finally:
            browser.close()

    if movies:
        with open("movies.json", "w", encoding="utf-8") as f:
            json.dump(movies, f, ensure_ascii=False, indent=2)
        print(f"Successfully updated movies.json with {len(movies)} movies!")

if __name__ == "__main__":
    scrape_movies()
