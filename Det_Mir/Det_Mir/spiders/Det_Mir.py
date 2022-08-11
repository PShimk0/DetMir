import logging

import chompjs
import scrapy

from ..utils import clean_string


class Det_Mir_Spider(scrapy.Spider):
    name = "det_mir"
    start_urls = ["https://www.detmir.ru/"]
    required_regions = ["Москва", "Санкт-Петербург"]
    custom_settings = {"LOG_LEVEL": "DEBUG"}

    def parse(self, response, **kwargs):
        # categories_data = chompjs.parse_js_object(clean_string(response.xpath("//script[@type='text/template'][@id='app-cached-data']/text()").get()))
        region_ids = []
        region_data = chompjs.parse_js_object(
            clean_string(
                response.xpath(
                    "//script[@type='text/template'][@id='app-data']/text()"
                ).get()
            )
        )
        for region_item in region_data["regions"]["data"]["items"]:
            if region_item["city"] in self.required_regions:
                region_ids.append(
                    {"city": region_item["city"], "iso": region_item["iso"]}
                )
        for region in region_ids:
            yield scrapy.Request(
                f'https://api.detmir.ru/v2/products?filter=categories[].alias:konstruktory;promo:false;withregion:{region["iso"]}&limit=100&offset=0&sort=popularity:desc',
                callback=self.parse_data,
                cb_kwargs={"current_offset": 0, "region": region},
            )

    def parse_data(self, response, **kwargs):
        try:
            data = chompjs.parse_js_object(response.text)
            if len(data) != 0:
                for i in data:
                    id = i["id"]
                    title = i["title"]
                    current_price = i["price"]["price"]
                    old_price = i["old_price"]
                    url = i["link"]["web_url"]
                    if old_price:
                        promo_price = current_price
                        price = old_price.get("price", None)
                    else:
                        promo_price = None
                        price = current_price
                    item = {
                        "id": id,
                        "title": title.replace(id, "").strip(),
                        "price": price,
                        "city": kwargs["region"]["city"],
                        "promo_price": promo_price,
                        "url": url,
                    }
                    yield item
                current_page = kwargs["current_offset"]
                next_page = current_page + 100
                next_page_url = self.next_page(response.url, current_page, next_page)
                yield scrapy.Request(
                    next_page_url,
                    callback=self.parse_data,
                    cb_kwargs={"current_offset": next_page, "region": kwargs["region"]},
                )
            else:
                logging.info(
                    f'Ended parsing through category for region: {kwargs["region"]["city"]}'
                )
        except Exception as e:
            logging.error(e)

    def next_page(self, url, current_offset, next_offset):
        url = url.replace(f"offset={current_offset}", f"offset={next_offset}")
        return url
