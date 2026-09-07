import scrapy
from ..items import RecruitmentSpiderItem

def safe_extract(xpath_obj):
    val = xpath_obj.get()
    return val.strip() if val else ""

class ZhilianSpider(scrapy.Spider):
    name = "zhaopin"
    allowed_domains = ["zhaopin.com"]

    def __init__(self, keyword=None, city=None, pages=None, task_id=None, **kwargs):
        super().__init__(**kwargs)
        self.keyword = keyword or "Python"
        self.city = city or "重庆"
        self.pages = int(pages) if pages else 10
        self.task_id = task_id
        self.MAX_PAGES = self.pages
        self.start_urls = [
            f"https://www.zhaopin.com/sou?jl=639&kw={self.keyword}&p=1"
        ]

    def parse(self, response):
        current_page = response.meta.get("page", 1)
        position_list = response.xpath('//div[@class="joblist-box__item clearfix joblist-box__item-unlogin"]')

        for position in position_list:
            position_name = safe_extract(position.xpath("./div//a[@class='jobinfo__name']/text()"))
            position_salary = safe_extract(position.xpath("./div//p[@class='jobinfo__salary']/text()"))

            position_skills = position.xpath(".//div[@class='jobinfo']//div[@class='joblist-box__item-tag']")
            skills = []
            for skill in position_skills:
                skill_text = safe_extract(skill.xpath("./text()"))
                if skill_text:
                    skills.append(skill_text)

            position_location = safe_extract(position.xpath("./div//div[@class='jobinfo__other-info-item']/span/text()"))
            position_year = safe_extract(position.xpath("./div//div[@class='jobinfo__other-info-item'][2]/text()"))
            position_education = safe_extract(position.xpath("./div//div[@class='jobinfo__other-info-item'][3]/text()"))
            company_name = safe_extract(position.xpath(".//a[@class='companyinfo__name']/text()")) or "未知"

            print(f"职位名称:{position_name}")
            print(f"职位薪资:{position_salary}")
            print(f"职位技能:{skills}")
            print(f"工作地点:{position_location}")
            print(f"工作年限:{position_year}")
            print(f"学历:{position_education}")
            print(f"公司名称:{company_name}")

            item = RecruitmentSpiderItem(
                platform="zhilian",
                job_id="",
                task_id=self.task_id,
                title=position_name,
                company=company_name,
                city=position_location,
                salary_raw=position_salary,
                experience=position_year,
                education=position_education,
                skills=skills,
                description=""
            )
            yield item

        next_page = current_page + 1
        if next_page <= self.MAX_PAGES:
            base_url = f"https://www.zhaopin.com/sou?jl=639&kw={self.keyword}&p="
            next_url = f"{base_url}{next_page}"
            print(f"正在爬取第 {next_page} 页...")
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={"page": next_page}
            )