import re
import sys
import urllib.request
import modal

app = modal.App("example-scraper")

# Custom image to install Chromium and Playwright in Modal.
playwright_image = modal.Image.debian_slim(python_version="3.10").run_commands(
    "apt-get update",
    "apt-get install -y software-properties-common",
    "apt-add-repository non-free",
    "apt-add-repository contrib",
    "pip install playwright==1.42.0",
    "playwright install-deps chromium",
    "playwright install chromium",
)

@app.function(image=playwright_image)
async def get_links(cur_url: str) -> list[str]:
    from playwright.async_api import (
        TimeoutError as PlaywrightTimeoutError,
        async_playwright,
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            await page.goto(cur_url, timeout=10_000)  # ten seconds
        except PlaywrightTimeoutError:
            print(f"Timeout loading {cur_url}, skipping")
            await browser.close()
            return []

        links = await page.eval_on_selector_all(
            "a[href]", "elements => elements.map(element => element.href)"
        )
        await browser.close()

    print("Links", links)
    return list(set(links))

@app.local_entrypoint()
def main():
    urls = ["http://modal.com", "http://github.com"]
    for links in get_links.map(urls):
        for link in links:
            print(link)