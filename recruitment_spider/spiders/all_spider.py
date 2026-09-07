import scrapy

from ..spiders.zhilian_spider import ZhilianSpider
from ..spiders.lagou_spider import LagouSpider
from ..spiders.liepin_spider import LiepinSpider
from ..spiders.qcwy_spider import QcwySpider


class AllSpider(scrapy.Spider):
    """一键触发全部平台爬虫（拉勾 / 猎聘 / 前程无忧 / 智联）"""
    name = 'all'

    def __init__(self, keyword='Python', city='北京', pages='3', task_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyword = keyword
        self.city = city
        self.pages = pages
        self.task_id = task_id

    def start_requests(self):
        spider_classes = [LagouSpider, LiepinSpider, QcwySpider, ZhilianSpider]
        for cls in spider_classes:
            spider = cls(
                keyword=self.keyword,
                city=self.city,
                pages=self.pages,
                task_id=self.task_id,
            )
            spider.crawler = self.crawler
            spider.settings = self.settings
            for req in spider.start_requests():
                yield req
