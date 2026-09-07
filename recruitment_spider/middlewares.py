# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import time

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from scrapy.http import HtmlResponse
# 改成Edge的options
from selenium.webdriver.edge.options import Options
from selenium import webdriver
from tldextract import tldextract


class RecuitmentSpiderSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class RecuitmentSpiderDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class SeleniumMiddlewares(object):
    """
    创建使用selenium访问网页的中间件
    功能说明：
    1. 在爬虫启动时初始化 Edge 浏览器实例
    2. 拦截所有请求，使用 Selenium 动态加载 JavaScript 渲染的页面
    3. 将渲染后的页面源码封装成 Scrapy Response 对象返回
    4. 在爬虫关闭时自动销毁浏览器实例，释放资源
    """
    def __init__(self):
        self.options = None
        self.driver = None
        # 新增：stealth文件路径
        self.stealth_js_path = "stealth.min.js"

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)
        return middleware

    def spider_opened(self, spider):
        self.options = Options()
        # 可选参数
        # self.options.add_argument("--headless=new")
        # self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-dev-shm-usage')

        if hasattr(spider, 'get_start_url'):
            start_url = spider.get_start_url()
            extracted = tldextract.extract(start_url)
            domain = extracted.domain
            spider.logger.info(f"主域名: {domain}")
            # ==========【重点】删掉 debugger_address 这一行！==========
            if domain == 'lagou' or domain == "51job" or domain == "liepin":
                self.options.debugger_address = "127.0.0.1:8888"
            spider.logger.info(f'浏览器已启动，起始URL: {start_url}, 主域名: {domain}')
        else:
            spider.logger.info('浏览器已启动')

        # 创建Edge驱动
        self.driver = webdriver.Edge(options=self.options)
        spider.logger.info('浏览器已启动')

        # ====================== 新增stealth注入核心代码 ======================
        try:
            # 读取stealth.min.js文件，使用绝对路径
            with open(r"D:\hy\cs\52_recuitment_spider\recruitment_spider\stealth.min.js", "r", encoding="utf-8") as f:
                js_content = f.read()
            # CDP命令：在每个新文档加载之前执行JS，隐藏selenium指纹
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": js_content
                }
            )
            spider.logger.info("✅ stealth.min.js 指纹隐藏脚本注入成功")
        except FileNotFoundError:
            spider.logger.error(f"❌ 找不到stealth.min.js，请确认文件路径！")
        except Exception as e:
            spider.logger.error(f"❌ stealth注入异常：{e}")
        # =================================================================

    def spider_closed(self, spider):
        if self.driver:
            try:
                self.driver.quit()
                spider.logger.info('浏览器已关闭')
            except Exception as e:
                spider.logger.error(f'关闭浏览器时发生异常: {e}')

    def process_request(self, request, spider):
        if not self.driver:
            spider.logger.warning('浏览器驱动不可用，跳过 Selenium 处理')
            return None
        try:
            self.driver.get(request.url)
            spider.logger.debug(f'页面加载完成: {request.url}')
        except Exception as e:
            spider.logger.error(f'Selenium 访问失败: {e}')
            return None
        time.sleep(3)
        source = self.driver.page_source
        response = HtmlResponse(url=self.driver.current_url, body=source, request=request, encoding='utf-8')
        spider.logger.info(f'Selenium 处理完成: {request.url}')
        return response