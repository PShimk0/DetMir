import csv

from scrapy import signals
from scrapy.exporters import CsvItemExporter


class DetMirCSVPipeline(object):

    items = []

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.file = open('det_mir_data.csv', 'w', encoding = 'utf-8-sig', newline='')

    def spider_closed(self, spider):
        writer = csv.DictWriter(self.file, fieldnames=self.items[0].keys())
        writer.writeheader()
        writer.writerows(self.items)
        self.file.close()

    def process_item(self, item, spider):
        self.items.append(item)
        return item
