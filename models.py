import os
from pydantic import BaseModel, field_validator
from bs4 import BeautifulSoup
import time
import requests
import json

class ScrapeSettings(BaseModel):
    pages_limit: int = None
    proxy: str = None

    @field_validator('pages_limit')
    def validate_page_limit(cls, v):
        if v is not None and v <= 0:
            raise ValueError('pages_limit must be greater than 0')
        return v

class NotificationStrategy:
    def notify(self, request, scraped_count: int):
        message = f"Scraping completed. {scraped_count} products were scraped and updated in the database."
        request.app.logger.debug(message)
        return message

class ScrapingTool:
    def __init__(self, settings: ScrapeSettings, retry_limit=3, delay=5):
        self.settings = settings
        self.retry_limit = retry_limit
        self.delay = delay
        self.base_url = "https://dentalstall.com/shop/"
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.proxies = {"http": settings.proxy, "https": settings.proxy} if settings.proxy else None
        self.notification_strategy = NotificationStrategy()

    def scrape_page(self, request, page: int):
        url = f"{self.base_url}?page={page}" if page > 1 else self.base_url
        retry_count = 0
        while retry_count < self.retry_limit:
            try:
                response = requests.get(url, headers=self.headers, proxies=self.proxies)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                retry_count += 1
                request.app.logger.debug(f"Error fetching page {page}. Retrying in {self.delay} seconds...")
                time.sleep(self.delay)
                if retry_count == self.retry_limit:
                    request.app.logger.debug(f"Failed to fetch page {page} after {self.retry_limit} attempts.")
                    return None

    def save_image(self, request, image_url: str, product_name: str):
        try:
            image_data = requests.get(image_url).content
            image_name = f"{product_name.replace(' ', '_')}.jpg"
            image_path = os.path.join(request.app.config["IMAGE_DIR"], image_name)
            with open(image_path, 'wb') as handler:
                handler.write(image_data)
            request.app.logger.debug(f"image_path: {image_path}")
            return image_path
        except Exception as e:
            request.app.logger.debug(f"Failed to save image for {product_name}: {e}")
            return None

    def scrape(self, request):
        page = 1
        scraped_count = 0
        scraped_products = []

        while True:
            if self.settings.pages_limit and page > self.settings.pages_limit:
                break

            content = self.scrape_page(request, page)
            request.app.logger.debug(f"page: {page}")
            if not content:
                break

            soup = BeautifulSoup(content, "lxml")
            products = soup.select("ul.products.columns-4 li")

            for product in products:
                product_name = product.select_one("h2.woo-loop-product__title").get_text(strip=True)
                request.app.logger.debug(f"product_name: {product_name}")

                price_text = product.select_one("span.woocommerce-Price-amount.amount bdi").get_text(strip=True)
                price = price_text.replace('₹', '').replace(',', '').split('.')[0]

                request.app.logger.debug(f"price: {price}")

                image_url = product.select_one(".mf-product-thumbnail img")["data-lazy-src"]
                request.app.logger.debug(f"image_url: {image_url}")


                cached_price = request.app.redis.get(product_name)
                request.app.logger.debug(f"cached_price: {cached_price}")
                if cached_price is None or cached_price.decode('utf-8') != price:
                    request.app.redis.set(product_name, price)
                    image_path = self.save_image(request, image_url, product_name)
                    if image_path:
                        scraped_products.append({
                            "product_title": product_name,
                            "product_price": price,
                            "path_to_image": image_path
                        })
                        scraped_count += 1

            page += 1
            if not products:
                break

        self.save_to_json(request, scraped_products)

        return self.notification_strategy.notify(request, scraped_count)

    def save_to_json(self, request, scraped_products):
        try:
            with open(request.app.config["DATA_FILE"], 'w') as f:
                json.dump(scraped_products, f, indent=4)
            request.app.logger.debug(f"Scraped data successfully saved to {request.app.config['DATA_FILE']}.")
        except Exception as e:
            request.app.logger.debug(f"Failed to save scraped data to JSON: {e}")
