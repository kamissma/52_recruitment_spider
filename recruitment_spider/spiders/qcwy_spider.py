import re
import time
import scrapy
from ..items import RecruitmentSpiderItem


def safe_re_search(pattern, text):
    """安全正则，匹配不到返回None，不抛异常"""
    if not text:
        return None
    res = re.search(pattern, text)
    if res:
        return res.group(1)
    return None


class QcwySpider(scrapy.Spider):
    name = "qcwy"
    platform = "qcwy"
    allowed_domains = ["we.51job.com"]
    start_urls = ["https://we.51job.com/pc/search?jobArea=060000,260200,070200&keyword=%7Bself.keyword%7D&searchType=2&keywordType="]

    def __init__(self, keyword, city, pages, task_id):
        """
        初始化方法
        接收搜索关键字、城市名称、爬取页数、任务ID
        :param:
        :return:
        """
        self.keyword = keyword
        self.city = city
        self.pages = pages
        self.taskId = task_id

    def start_requests(self):
        """
        默认的start_requests回调函数
        通过爬取指定页数的数据，拼接url地址
        并将该地址推送给scrapy队列发起请求
        :param:
        :return:
        """
        for page in range(1, int(self.pages) + 1):
            url = f"https://we.51job.com/pc/search?jobArea=060000,260200,070200&keyword={self.keyword}&searchType=2&keywordType="
            time.sleep(1)
            yield scrapy.Request(url, callback=self.parse, meta={"use_selenium": True})

    def get_start_url(self):
        """
        该方法用于在中间件中获取到当前请求的URL，便于配置自动化浏览器
        中间件可以调用此方法获取URL
        """
        start_url = ("https://we.51job.com")
        return start_url

    def parse(self, response):
        """
        回调函数，满足通过xpath提取所需要的信息
        该方法主要是对列表页数据进行解析，将解析结果封装成JobItem对象，最终返回Item对象
        :param response:访问职位列表页返回数据对象
        :return:
        """
        position_list = response.xpath('//div[@class="joblist-item-job-wrapper"]')
        print(position_list)
        for item in position_list:
            sal_text = item.xpath('.//span[@class="sal text-cut"]/text()').get()
            nums = re.findall(r'(\d+)', sal_text or "")

            # 薪资容错处理
            if len(nums) >= 2:
                salary_min = int(nums[0])
                salary_max = int(nums[1])
            elif len(nums) == 1:
                salary_min = int(nums[0])
                salary_max = int(nums[0])
            else:
                salary_min = None
                salary_max = None

            sensor_text = item.xpath('.//div[@class="joblist-item-job sensors_exposure"]/@sensorsdata').get()
            experience = safe_re_search(r'jobDegree":"(.*?)",', sensor_text)
            education = safe_re_search(r'jobYear":"(.*?)",', sensor_text)

            job_item = RecruitmentSpiderItem(
                platform='qcwy',
                job_id='',
                task_id=self.taskId,
                title=item.xpath('.//div[@class="job-info text-cut"]/span/text()').get(),
                company=item.xpath('.//span[@class="cname text-cut"]/text()').get(),
                city=item.xpath('.//div[@class="shrink-0"]/text()').get(),
                salary_raw=sal_text,
                salary_min=salary_min,
                salary_max=salary_max,
                experience=experience,
                education=education,
                skills='',
                description='',
            )
            print(job_item)
            if job_item['title']:
                yield job_item