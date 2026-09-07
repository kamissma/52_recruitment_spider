import time
import scrapy
from ..items import JobItem

class BossSpider(scrapy.Spider):
    name = 'boss'
    platform = 'boss'
    allowed_domains = ['zhipin.com']
    start_urls = ["https://zhipin.com"]

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
        BOSS直聘真实爬取入口
        实际部署时需配置Cookie、处理反爬机制
        """
        city_code = self._get_city_code(self.city)
        # url = f"https://www.zhipin.com/web/geek/jobs?query={self.keyword}&city={city_code}&industry=&position="
        url = f"https://www.zhipin.com/wapi/zpgeek/search/joblist.json"
        time.sleep(3)
        yield scrapy.Request(url, callback=self.parse)

    def get_start_url(self):
        """
        该方法用于在中间件中获取到当前请求的URL，便于配置自动化浏览器
        中间件可以调用此方法获取URL
        """
        start_url = ("https://zhipin.com")
        return start_url

    def parse(self, response):
        """
        回调函数，满足通过xpath提取所需要的信息
        该方法主要是对列表页数据进行解析，将解析结果封装成JobItem对象，最终返回Item对象
        :param response:访问职位列表页返回数据对象
        :return:
        """
        position_list = response.xpath('//div[@class="item__10RTO"]')
        for item in position_list:
            item = JobItem(
                platform='lagou',
                job_id='',  # job.css('::attr(data-jobid)').get('')
                task_id=self.taskId,
                title=self.parse_industry_location(item.xpath('.//a[@id="openWinPostion"]/text()').get())[0],
                company=item.xpath('.//div[@class="company-name__2-SjF"]/a/text()').get(),
                city=self.parse_industry_location(item.xpath('.//a[@id="openWinPostion"]/text()').get())[1],
                salary_raw=item.xpath('.//span[@class="money__3Lkgq"]/text()').get(),
                # salary_min=int(item.xpath('.//span[@class="money__3Lkgq"]/text()').get().split('-')[0][-1]),
                salary_min=int(re.findall(r'(\d+)', item.xpath('.//span[@class="money__3Lkgq"]/text()').get())[0]),
                # salary_max=int(item.xpath('.//span[@class="money__3Lkgq"]/text()').get().split('-')[1][-1]),
                salary_max=int(re.findall(r'(\d+)', item.xpath('.//span[@class="money__3Lkgq"]/text()').get())[1]),
                experience=self.parse_job_info(item.xpath('.//div[@class="p-bom__JlNur"]/text()').get()).get(
                    "experience"),
                education=self.parse_job_info(item.xpath('.//div[@class="p-bom__JlNur"]/text()').get()).get(
                    'education'),
                skills='',
                description='',
            )
            if item['title']:
                yield item

    def _get_city_code(self, city):
        city_map = {
            '北京': '101010100', '上海': '101020100', '深圳': '101280600',
            '杭州': '101210100', '广州': '101280100', '成都': '101270100',
        }
        return city_map.get(city, '101010100')
