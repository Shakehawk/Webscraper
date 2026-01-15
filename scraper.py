from playwright.sync_api import sync_playwright
import re
import time


def clean_price(text):
    text = text.replace("€", "").replace(",", ".")
    m = re.search(r"\d+(\.\d+)?", text)
    return float(m.group()) if m else None


def scrape_shop(shop):
    results = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            viewport={"width": 1400, "height": 900}
        )

        page = context.new_page()
        page.goto(shop["url"], timeout=60000)
        time.sleep(3)

        #  Cookie-Banner akzeptieren (best effort)
        for txt in ["Alle akzeptieren", "Akzeptieren", "Zustimmen", "Accept all"]:
            try:
                page.get_by_text(txt, timeout=2000).click()
                break
            except:
                pass

        time.sleep(2)

        #  Alle Links sammeln
        for a in page.query_selector_all("a"):
            href = a.get_attribute("href")
            if not href:
                continue

            href = href.lower()
            if "vape" in href and href.startswith("http"):
                seen_urls.add(href)

        print(f"🔎 {shop['shop_name']}: {len(seen_urls)} Vape-Links gefunden")

        # Produktseiten besuchen (Limit zum Schutz)
        for url in list(seen_urls)[:20]:
            try:
                page.goto(url, timeout=30000)
                time.sleep(2)

                title = page.query_selector("h1")
                price_el = page.query_selector(
                    ".price, .product-price, .price--default, [data-price]"
                )

                if not title or not price_el:
                    continue

                name = title.inner_text().strip()
                price = clean_price(price_el.inner_text())

                if not price:
                    continue

                results.append({
                    "name": name,
                    "price": price,
                    "url": url,
                    "shop": shop["shop_name"]
                })

            except Exception:
                continue

        browser.close()

    print(f"{shop['shop_name']}: {len(results)} Produkte extrahiert")
    return results
