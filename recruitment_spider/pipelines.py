# Define your item pipelines here
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import os
from datetime import datetime

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymysql


class RecuitmentSpiderPipeline:
    def process_item(self, item):
        return item

class MysqlPipeline:
    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host = os.getenv("DB_HOST", spider.settings["MYSQL_HOST"]),
            port = int(os.getenv("DB_PORT", spider.settings["MYSQL_PORT"])),
            user = os.getenv("DB_USER", spider.settings["MYSQL_USERNAME"]),
            password = os.getenv("DB_PASSWORD", spider.settings["MYSQL_PASSWORD"]),
            database = os.getenv("DB_NAME", spider.settings["MYSQL_DB"]),
            charset = "utf8mb4"
        )
        self.cursor = self.conn.cursor()

    def close_spider(self, spider):
        """
        关闭游标与数据库连接
        """
        self.cursor.close()
        self.conn.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        skills = adapter.get("skills")
        if isinstance(skills, list):
            skills = json.dumps(skills, ensure_ascii=False)
        publish_time = adapter.get("publish_time")
        if isinstance(publish_time, str):
            try:
                publish_time = datetime.fromisoformat(publish_time)
            except ValueError:
                publish_time = datetime.now()

        sql = """
            INSERT INTO job_raw (platform, job_id, task_id, title, company, city, salary_raw, salary_min,
             salary_max, experience, education, skills, description, publish_time, crawl_time, is_cleaned)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
             ON DUPLICATE KEY UPDATE
             title = VALUES(title), salary_raw = VALUES(salary_raw), crawl_time = VALUES(crawl_time)
        """
        self.cursor.execute(sql,(
            adapter.get("platform"),
            adapter.get("job_id"),
            adapter.get("task_id"),
            adapter.get("title"),
            adapter.get("company"),
            adapter.get("city"),
            adapter.get("salary_raw"),
            adapter.get("salary_min"),
            adapter.get("salary_max"),
            adapter.get("experience"),
            adapter.get("education"),
            skills,
            adapter.get("description"),
            publish_time,
            datetime.now()
        ))
        self.conn.commit()
        return item