import os
import re
from ..services.data_cleaner import EDUCATION_MAP, extract_skills

class ResumeParser:
    """简历解析服务"""
    @staticmethod
    def parse_text(text):
        skills = extract_skills(text)
        experience = ResumeParser._extract_experience(text)
        education = ResumeParser._extract_education(text)
        return {
            'skills': skills,
            'experience_years': experience,
            'education_level': education,
            'city': ResumeParser._extract_city(text),
            'job_title': ResumeParser._extract_job_title(text),
            'company_size': ResumeParser._extract_company_size(text),
            'text_length': len(text),
        }

    @staticmethod
    def _extract_city(text):
        # 常见城市列表，按优先级匹配
        cities = [
            '北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京',
            '西安', '重庆', '苏州', '天津', '长沙', '郑州', '青岛', '大连',
            '厦门', '合肥', '济南', '福州', '东莞', '佛山', '无锡', '宁波',
        ]
        for city in cities:
            if city in text:
                return city
        return ''

    @staticmethod
    def _extract_job_title(text):
        # 应聘意向、技术岗位等正则模式
        patterns = [
            r'(?:应聘|求职|目标|意向)[职位岗位]*[：:\s]*([^\n，,。；;]{2,20})',
            r'(Python|Java|前端|后端|算法|数据|测试|运维|产品)[^\n]{0,12}(?:工程师|开发|经理|专员)',
        ]
        # 依次尝试匹配
        for pattern in patterns:
            # 忽略大小写搜索
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 取捕获组或整段匹配
                return (match.group(1) if match.lastindex else match.group(0)).strip()
        return ''

    @staticmethod
    def _extract_company_size(text):
        # 人数区间、以上、少于等规模表述
        patterns = [
            r'(\d+\s*[-~到至]\s*\d+\s*人)',
            r'(\d+\s*人\s*以上)',
            r'(少于\s*\d+\s*人)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # 去掉空格后返回
                return match.group(1).replace(' ', '')
        return ''

    @staticmethod
    def _extract_experience(text):
        # 中文/英文工作年限表述
        patterns = [
            r'(\d+)\s*年\s*(以上)?\s*(工作|开发|相关)?经验',
            r'工作(\d+)年',
            r'(\d+)years?',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 上限 20 年，避免异常大数
                return min(int(match.group(1)), 20)
        return 0

    @staticmethod
    def _extract_education(text):
        # 遍历学历关键词映射
        for key, val in EDUCATION_MAP.items():
            if key in text:
                return val
        return 3

    @staticmethod
    def extract_text(filepath):
        """从简历文件提取纯文本，供预览与解析共用"""
        ext = os.path.splitext(filepath)[1].lower()
        text = ''

        if ext == '.txt':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        elif ext == '.pdf':
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(filepath)
                for page in reader.pages:
                    text += page.extract_text() or ''
            except Exception:
                text = ''
        elif ext in ('.doc', '.docx'):
            try:
                from docx import Document
                doc = Document(filepath)
                text = '\n'.join(p.text for p in doc.paragraphs)
            except Exception:
                text = ''
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

        return text or ''

    @staticmethod
    def parse_file(filepath):
        text = ResumeParser.extract_text(filepath)  # 先提取纯文本
        return ResumeParser.parse_text(text)  # 对提取文本做结构化解析