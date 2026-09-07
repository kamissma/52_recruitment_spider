# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import dataclass

import scrapy

class RecruitmentSpiderItem(scrapy.Item):
    platform = scrapy.Field()
    job_id = scrapy.Field()
    task_id = scrapy.Field()
    title = scrapy.Field()
    company = scrapy.Field()
    city = scrapy.Field()
    salary_raw = scrapy.Field()
    salary_min = scrapy.Field()
    salary_max = scrapy.Field()
    experience = scrapy.Field()
    education = scrapy.Field()
    skills = scrapy.Field()
    description = scrapy.Field()
class JobItem(scrapy.Item):
    title = scrapy.Field()