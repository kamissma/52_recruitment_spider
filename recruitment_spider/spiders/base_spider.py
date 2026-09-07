import json
import random
import uuid
from datetime import datetime, timedelta

import scrapy

from ..items import JobItem


JOB_TITLES = [
    'Python开发工程师', 'Java后端开发', '前端开发工程师', '全栈工程师',
    '数据分析师', '算法工程师', 'DevOps工程师', 'Go开发工程师',
    'React开发工程师', 'Vue.js开发工程师', 'Android开发', 'iOS开发',
    '测试工程师', '运维工程师', '产品经理', 'UI设计师',
    '大数据工程师', '机器学习工程师', 'NLP工程师', '爬虫工程师',
    '架构师', '技术经理', 'DBA', '安全工程师',
]

COMPANIES = [
    '字节跳动', '阿里巴巴', '腾讯科技', '百度在线', '美团', '京东集团',
    '滴滴出行', '网易游戏', '华为技术', '小米科技', '拼多多', '快手科技',
    '商汤科技', '旷视科技', '科大讯飞', '携程旅行', '哔哩哔哩', '知乎',
    '蚂蚁集团', '顺丰科技', '贝壳找房', '理想汽车', '蔚来汽车', '大疆创新',
]

CITIES = ['北京', '上海', '深圳', '杭州', '广州', '成都', '南京', '武汉', '西安', '苏州']

SKILLS_POOL = [
    ['Python', 'Django', 'Flask', 'MySQL', 'Redis'],
    ['Java', 'Spring', 'MySQL', 'Redis', '微服务'],
    ['JavaScript', 'Vue', 'React', 'Node.js', 'Webpack'],
    ['Python', 'TensorFlow', 'PyTorch', '机器学习', '数据分析'],
    ['Go', 'Docker', 'Kubernetes', '微服务', '分布式'],
    ['Python', 'Spark', 'Hadoop', 'Hive', 'Kafka'],
    ['C++', 'Linux', '算法', '数据结构'],
    ['Python', 'Scrapy', 'Selenium', '爬虫', '数据分析'],
]

SALARY_RANGES = [
    ('8-12K', 8, 12), ('10-15K', 10, 15), ('12-18K', 12, 18),
    ('15-25K', 15, 25), ('18-30K', 18, 30), ('20-35K', 20, 35),
    ('25-40K', 25, 40), ('30-50K', 30, 50), ('35-60K', 35, 60),
    ('40-70K', 40, 70),
]

EXPERIENCES = ['不限', '1-3年', '3-5年', '5-10年', '应届', '1年以下']
EDUCATIONS = ['不限', '大专', '本科', '硕士', '博士']


class MockDataMixin:
    """模拟数据生成混入类，用于演示和测试"""

    def generate_mock_jobs(self, platform, keyword, city, pages):
        jobs_per_page = getattr(self, 'jobs_per_page', 15)
        for page in range(1, pages + 1):
            for i in range(jobs_per_page):
                title = random.choice(JOB_TITLES)
                if keyword and keyword.lower() not in title.lower():
                    title = f'{keyword}{title}'

                salary_info = random.choice(SALARY_RANGES)
                skills = random.choice(SKILLS_POOL)
                target_city = city if city else random.choice(CITIES)

                item = JobItem()
                item['platform'] = platform
                item['job_id'] = f'{platform}_{uuid.uuid4().hex[:12]}'
                item['title'] = title
                item['company'] = random.choice(COMPANIES)
                item['city'] = target_city
                item['salary_raw'] = salary_info[0]
                item['salary_min'] = salary_info[1]
                item['salary_max'] = salary_info[2]
                item['experience'] = random.choice(EXPERIENCES)
                item['education'] = random.choice(EDUCATIONS)
                item['skills'] = skills
                item['description'] = (
                    f'负责{title}相关工作，要求熟悉{", ".join(skills[:3])}等技术栈。'
                    f'参与产品设计与开发，具备团队协作能力。'
                )
                item['publish_time'] = (
                    datetime.now() - timedelta(days=random.randint(0, 30))
                ).isoformat()
                yield item


class BaseJobSpider(scrapy.Spider, MockDataMixin):
    custom_settings = {
        'USE_MOCK_DATA': True,
    }

    def __init__(self, keyword='Python', city='北京', pages='3', task_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyword = keyword
        self.city = city
        self.pages = int(pages)
        self.task_id = task_id
        self.platform = 'unknown'

    def start_requests(self):
        use_mock = self.settings.getbool('USE_MOCK_DATA', True)
        if use_mock:
            for item in self.generate_mock_jobs(
                self.platform, self.keyword, self.city, self.pages
            ):
                yield scrapy.Request(
                    url='data:,mock',
                    callback=self.parse_mock,
                    meta={'item': item},
                    dont_filter=True,
                )
        else:
            yield from self.start_real_requests()

    def start_real_requests(self):
        """子类实现真实爬取逻辑"""
        raise NotImplementedError

    def parse_mock(self, response):
        yield response.meta['item']

    def make_item(self, **kwargs):
        item = JobItem()
        item['platform'] = self.platform
        for key, val in kwargs.items():
            item[key] = val
        if isinstance(item.get('skills'), list):
            pass
        elif item.get('skills'):
            item['skills'] = json.loads(item['skills']) if isinstance(item['skills'], str) else []
        return item
