import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, DomainFilter, URLPatternFilter
# from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy  # optional

async def main():
    # Optional but helpful on JS-heavy sites; fine to omit if you already saw detail pages before
    browser_cfg = BrowserConfig(headless=True)

    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["amiv.ethz.ch"]),
        # Path-only patterns so both listing and details match
        URLPatternFilter(patterns=[
            "/en/events",      # listing without trailing slash
            "/en/events/",     # listing with trailing slash
            "/en/events/*",    # detail pages
        ])
    ])

    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=5,
            include_external=False,
            filter_chain=filter_chain,
            max_pages=300,
        ),
        # scraping_strategy=LXMLWebScrapingStrategy(),  # OK to keep/remove
        verbose=True,
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        results = await crawler.arun("https://amiv.ethz.ch/en/events/", config=config)
        print(f"Crawled {len(results)} pages.")
        for r in results[:12]:
            print("URL:", r.url)

if __name__ == "__main__":
    asyncio.run(main())
