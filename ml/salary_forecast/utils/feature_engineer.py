from collections import Counter
from sklearn.model_selection import train_test_split
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import RobustScaler, LabelEncoder
from ml.salary_forecast.dataset.data_loader import DataLoader
import pandas as pd
import re

class FeatureEngineer:
    def __init__(self):
        self.df=DataLoader().get_datas()
        self.scaler=RobustScaler()
        self.label_encoders={}
        self.feature_importance=None

    def clean_data(self):
        print("开始数据清洗")
        if "skills" in self.df.columns:
            # 如果单元格是list，转为字符串；字符串保持原样
            self.df["skills"] = self.df["skills"].apply(lambda x: str(x) if isinstance(x, list) else x)

        self.df = self.df.drop_duplicates()  # 现在没有list类型，可以安全去重

        if "title" in self.df.columns:
            self.df["title"] = self.df["title"].fillna("")

        if "skills" in self.df.columns:
            # 恢复解析skills为list，就是你原来的解析逻辑
            def parse_skill_field(x):
                if pd.isna(x) or x == "":
                    return []
                if isinstance(x, str):
                    if x.startswith('['):
                        try:
                            return eval(x)
                        except:
                            return [s.strip() for s in x.split(",")]
                    else:
                        return [x.strip()]
                elif isinstance(x, list):
                    return x
                return []

            self.df["skills"] = self.df["skills"].apply(parse_skill_field)

        if "experience" in self.df.columns:
            self.df["experience"]=self.df["experience"].fillna("无需经验")

        if "education" in self.df.columns:
            self.df["education"]=self.df["education"].fillna("不限学历")

        if "description" in self.df.columns:
            self.df["description"]=self.df["description"].fillna("")

        print(f"数据清洗完成，剩余{len(self.df)}条数据")
        return self

    def parse_salary(self):
        def parse_salary_raw(raw):
            raw = str(raw.get("salary_raw", ""))
            raw=raw.replace("·","").replace("薪资","").strip()
            try:
                if '元/天' in raw:
                    nums=re.findall(r'(\d+\.?\d*)',raw)
                    daily=float(nums[0])
                    monthly=daily * 22
                    return monthly*0.9,monthly*1.1

                if '元/时' in raw or '元/小时' in raw:
                    nums=re.findall(r'(\d+\.?\d*)',raw)
                    if nums:
                        hourly=float(nums[0])
                        monthly=hourly * 8 * 22
                        return hourly*0.9,monthly*1.1

                if '万/年' in raw:
                    nums=re.findall(r'(\d+\.?\d*)',raw)
                    if nums:
                        annual=float(nums[0])*10000
                        monthly=annual / 12
                        if len(nums)>=2:
                            return float(nums[0])*10000/12,float(nums[1])*10000/12
                        return monthly*0.85,monthly*1.15

                if '千' in raw:
                    nums=re.findall(r'(\d+\.?\d*)',raw)
                    if len(nums)>=2:
                        return float(nums[0])*1000,float(nums[1])*1000
                    elif nums:
                        val=float(nums[0])*1000
                        return val*0.8,val*1.2

                if '万' in raw:
                    nums = re.findall(r'(\d+\.?\d*)', raw)
                    if len(nums) >= 2:
                        return float(nums[0]) * 10000, float(nums[1]) * 10000
                    elif nums:
                        val = float(nums[0]) * 10000
                        return val * 0.8, val * 1.2

                if '以上' in raw:
                    nums = re.findall(r'(\d+\.?\d*)', raw)
                    if nums:
                        val=float(nums[0])
                        if '千' in raw:
                            val*=1000
                        elif '万' in raw:
                            val*=10000
                        return val,val*1.5

                nums=re.findall(r'(\d+\.?\d*)',raw)
                if len(nums) >= 2:
                    return float(nums[0]), float(nums[1])
                elif len(nums) == 1:
                    val=float(nums[0])
                    val = float(nums[0])
                    if '千' in raw:
                        val *= 1000
                    elif '万' in raw:
                        val *= 10000
                    return val, val * 1.5
            except Exception as e:
                pass
            return np.nan, np.nan

        self.df[["salary_min_parsed", "salary_max_parsed"]] = self.df.apply(
            parse_salary_raw, axis=1, result_type="expand"
        )
        self.df = self.df.dropna(subset=["salary_min_parsed", "salary_max_parsed"])
        self.df=self.df[
            (self.df["salary_min_parsed"] >=2000)&
            (self.df["salary_max_parsed"] <=80000)
        ]
        if len(self.df) == 0:
            print("无有效薪资数据")
            return self
        self.df["salary_target"]=(self.df["salary_min_parsed"] + self.df["salary_max_parsed"]) / 2
        self.df["salary_target_log"]=np.log1p(self.df["salary_target"])

        Q1=self.df["salary_target"].quantile(0.02)
        Q3=self.df["salary_target"].quantile(0.98)
        IQR=Q3 - Q1
        lower_bound=max(2000,Q1-2*IQR)
        upper_bound=min(80000,Q3+2*IQR)

        self.df=self.df[
            (self.df["salary_target"]>=lower_bound)&
            (self.df["salary_target"]<=upper_bound)
        ]
        print(f"薪资解析完成，有效数据：{len(self.df)}条")
        print(f"薪资范围：{self.df['salary_target'].min():.0f}~{self.df['salary_target'].max():.0f}")
        print(f"平均薪资：{self.df['salary_target'].mean():.0f}")
        return self

    def encode_experience(self):
        def encode_exp(exp):
            if pd.isna(exp):
                return 0
            exp=str(exp).lower()

            if '在校生' in exp or '应届生' in exp:
                return 0
            if '无需' in exp or '不想' in exp:
                return 0

            nums=re.findall(r"(\d+\.?\d*)",exp)
            if nums:
                if len(nums)>=2:
                    exp_val=(float(nums[0])+float(nums[1]))/2
                else:
                    exp_val=float(nums[0])

                if exp_val <= 1:
                    return 1
                elif exp_val <= 3:
                    return 2
                elif exp_val <= 5:
                    return 3
                elif exp_val <= 10:
                    return 4
                else:
                    return 5
            return 0
        self.df["experience_level"]=self.df["experience"].apply(encode_exp)
        self.df["experience_years"]=self.df["experience"].apply(
            lambda x: float(re.findall(r"(\d+\.?\d*)",str(x))[0] if re.findall(r"(\d+\.?\d*)",str(x)) else 0)
        )

    def encode_education(self):
        edu_level_map={
            '博士':6,'硕士':5,'研究生':5,
            '本科':4,'大专':3,'中专':2,
            '高中':2,'初中':1,'小学':1
        }

        edu_category_map={
            '博士':'博士',
            '硕士': '硕士',
            '研究生': '硕士',
            '本科': '本科',
            '大专': '大专',
            '中专': '中专',
            '高中': '高中',
            '初中': '初中',
            '小学': '小学',
        }

        def map_education(edu):
            if pd.isna(edu):
                return 3
            edu=str(edu)
            if '不限' in edu:
                return 3
            for key,val in edu_level_map.items():
                if key in edu:
                    return val
            return 3
        self.df["education_level"]=self.df["education"].apply(map_education)

        def map_education_category(edu):
            if pd.isna(edu):
                return '大专'
            edu=str(edu)
            if '不限' in edu:
                return '大专'
            for key,val in edu_level_map.items():
                if key in edu:
                    return val
            return '大专'
        self.df["education_level"] = pd.to_numeric(self.df["education_level"], errors="coerce").fillna(3)
        return self

    def company_features(self):
        company_types={
            "国企","民营","上市公司","资金","合资","私营"
        }
        for ctype in company_types:
            self.df[f'company_type_{ctype}']=self.df["description"].apply(
                lambda x: 1 if isinstance(x,str) and ctype in x else 0
            )

        scale_map={
            '少于50人':1,
            '50-100人':2,
            '150-500人': 3,
            '500-1000人': 4,
            '1000-5000人': 5,
            '50100人以上': 6,
        }

        def extract_scale(desc):
            if not isinstance(desc, str):
                return 0
            for key,val in scale_map.items():
                if key in desc:
                    return val
            return 0
        self.df['company_scale_level']=self.df["description"].apply(extract_scale)

        industries=[
            "互联网","金融","电商","医疗","教育","服务业","制造业"
        ]
        for industry in industries:
            self.df['industry_{industry}']=self.df["description"].apply(
                lambda x: 1 if isinstance(x,str) and industry in x else 0
            )
        print(f"进行处理后的数据：{self.df}")
        return self

    def extract_skills(self):
        self.df["skill_count"] = self.df["skills"].apply(
            lambda x:len(x) if isinstance(x,list) else 0
        )

        all_skills=[]
        for skills in self.df['skills']:
            if isinstance (skills,list):
                for skill in skills:
                    if isinstance(skill,list):
                        all_skills.extend([str(s.lower()) for s in skill])
                    else:
                        all_skills.append(str(skill).lower())
            elif isinstance (skills,str):
                all_skills.extend([s.strip().lower() for s in skills.split(",") if s.strip()])

        skill_counter=Counter(all_skills)
        print(f"总共有{len(skill_counter)}个不同技能")

        #定义技能的分类字典
        skill_categories = {
            'programming': ['python', 'java', 'c++', 'go', 'rust', 'javascript', 'typescript'],
            'web': ['react', 'vue', 'angular', 'html', 'css', 'node', 'spring', 'django'],
            'data': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
            'cloud': ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'linux'],
            'ml': ['tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy'],
            'management': ['管理', '项目', '团队', '领导', '协调']
        }

        #批量计算技能类别进行匹配
        for category,skills in skill_categories.items():
            self.df[f"skill_category_{category}"]=self.df["skills"].apply(
                lambda x, skills=skills:sum(1 for s in x if isinstance(x,list) and
                                            any(skill in str(s).lower() for skill in skills))
                                               if isinstance(x,list) else 0
            )

        top_skills=[s for s, _ in skill_counter.most_common(30)]

        for skill in top_skills[:25]:
            col_name = f"skill_{skill.replace(' ','_').replace('-','_')[:20]}"
            self.df[col_name]=self.df["skills"].apply(
                lambda x,skill=skill:1 if isinstance(x,list) and any(
                    skill in str(s).lower() for s in x
                )else(1 if isinstance(x,str) and skill in x.lower() else 0)
            )

        #关键技能组合
        key_skill_combinations = [
            ['python', 'sql'], ['python', 'java'], ['react', 'node'],
            ['docker', 'kubernetes'], ['管理', '项目'], ['测试', '自动化']
        ]

        for combo in key_skill_combinations:
            combo_name='_'.join(combo)
            self.df[f"skill_combo_{combo_name}"]=self.df["skills"].apply(
                lambda x,combo=combo:1 if isinstance(x,list) and all(
                    any(skill in str(s).lower() for s in x) for skill in combo
                )else 0
            )

        return self

    def extract_city(self):
        def clean_city_name(city_text):
            if pd.isna(city_text) or not isinstance(city_text, str):
                return "未知"
            city_text=city_text.strip()
            for sep in ['·','-','（','(']:
                if sep in city_text:
                    city_text=city_text.split(sep)[0]
                    break
            return city_text
        self.df["city_clean"]=self.df["city"].apply(clean_city_name)

        city_tier_map = {
            # 一线 (5)
            '北京': 5, '上海': 5, '广州': 5, '深圳': 5,
            # 新一线 (4)
            '成都': 4, '杭州': 4, '武汉': 4, '南京': 4, '重庆': 4,
            '西安': 4, '苏州': 4, '天津': 4, '长沙': 4, '郑州': 4,
            '东莞': 4, '青岛': 4, '合肥': 4, '宁波': 4, '无锡': 4,
            # 二线 (3)
            '佛山': 3, '济南': 3, '长春': 3, '大连': 3, '厦门': 3,
            '沈阳': 3, '昆明': 3, '石家庄': 3, '南昌': 3, '哈尔滨': 3,
            '太原': 3, '贵阳': 3, '乌鲁木齐': 3, '兰州': 3, '南宁': 3,
            '福州': 3, '中山': 3, '潍坊': 3, '盐城': 3, '洛阳': 3,
            '芜湖': 3, '扬州': 3,
            # 三线及以下 (2)
            '三亚': 2, '万宁': 2,
        }

        self.df["city_level"]=self.df["city_clean"].map(city_tier_map).fillna(3)

        le = LabelEncoder()
        self.df["city_encoded"]=le.fit_transform(self.df["city"].fillna("未知"))
        self.label_encoders["city"]=le

        self.df["is_tier1"]=(self.df["city_level"]>=4).astype(int)

        return self

    def extract_text_features(self):
        title_col='title' if 'title' in self.df.columns else "job_title"
        desc_col='description' if 'description' in self.df.columns else "job_description"

        self.df["text"]=self.df[title_col].fillna('')+' '+self.df[desc_col].fillna('')
        if self.df["text"].str.len().sum()==0:
            print("文本数据为空")
            for i in range(10):
                self.df[f"text_feature_{i}"]=0
            return 0

        try:
            tfidf_char=TfidfVectorizer(
                max_features=30,
                analyzer='char',
                ngram_range=(2, 4)
            )

            tfidf_word = TfidfVectorizer(
                max_features=20,
                stop_words='english',
                ngram_range=(1, 2)
            )

            char_matrix=tfidf_char.fit_transform(self.df["text"].fillna(""))
            char_features=char_matrix.toarray()

            word_matrix=tfidf_word.fit_transform(self.df["text"].fillna(""))
            word_features=word_matrix.toarray()

            combined_features=np.hstack((char_features, word_features))

            n_components=min(20,combined_features.shape[1])

            if n_components > 1:
                svd=TruncatedSVD(n_components=n_components,random_state=42)
                text_features=svd.fit_transform(combined_features)
                for i in range(text_features.shape[1]):
                    self.df[f"text_feature_{i}"]=text_features[:,i]

            else:
                for i in range(min(10, combined_features.shape[1])):
                    self.df[f"text_feature_{i}"]=combined_features[:,i]

        except Exception as e:
            print(f"文本特征提取出错：{e}")
            for i in range(10):
                self.df[f"text_feature_{i}"] = 0

        return self

    def create_derived_features(self):
        """衍生特征"""
        # 薪资范围比例
        self.df['salary_range_ratio'] = (self.df['salary_max_parsed'] - self.df['salary_min_parsed']) / \
                                        (self.df['salary_min_parsed'] + 1)

        # 经验和教育交互
        if 'experience_years' in self.df.columns and 'education_level' in self.df.columns:
            self.df['exp_edu_interaction'] = self.df['experience_years'] * self.df['education_level']
            self.df['exp_edu_ratio'] = self.df['experience_years'] / (self.df['education_level'] + 1)

        # 技能丰富
        self.df['skill_richness'] = self.df['skill_count'] / 10

        # 薪资等级
        self.df['salary_level'] = pd.qcut(self.df['salary_target'], q=5, labels=False)

        # 工作经验等级
        if 'experience_level' in self.df.columns:
            self.df['experience_level_squared'] = self.df['experience_level'] ** 2

        return self

    def prepare_features(self):
        """准备特征"""
        # 基础特征
        feature_names = [
            'skill_count', 'salary_range_ratio', 'skill_richness',
            'city_level', 'city_encoded', 'company_scale_level'
        ]

        # 经验特征
        if 'experience_years' in self.df.columns:
            feature_names.append('experience_years')
        if 'experience_level' in self.df.columns:
            feature_names.append('experience_level')
        if 'experience_level_squared' in self.df.columns:
            feature_names.append('experience_level_squared')

        # 教育特征
        if 'education_level' in self.df.columns:
            feature_names.append('education_level')

        # 交互特征
        interaction_cols = ['exp_edu_interaction', 'exp_edu_ratio']
        for col in interaction_cols:
            if col in self.df.columns:
                feature_names.append(col)

        # 公司特征
        company_cols = [col for col in self.df.columns if col.startswith('company_type_')]
        feature_names.extend(company_cols)

        # 行业特征
        industry_cols = [col for col in self.df.columns if col.startswith('industry_')]
        feature_names.extend(industry_cols)

        # 技能特征
        skill_cols = [col for col in self.df.columns if col.startswith('skill_') and
                      col not in ['skill_count', 'skill_richness']]
        feature_names.extend(skill_cols[:25])

        # 技能组合
        combo_cols = [col for col in self.df.columns if col.startswith('skill_combo_')]
        feature_names.extend(combo_cols)

        # 技能类别
        category_cols = [col for col in self.df.columns if col.startswith('skill_category_')]
        feature_names.extend(category_cols)

        # 文本特征
        text_cols = [col for col in self.df.columns if col.startswith('text_feature_')]
        feature_names.extend(text_cols[:15])

        # 区域特征
        region_cols = [col for col in self.df.columns if col.startswith('region_')]
        feature_names.extend(region_cols)

        # 去重
        feature_n = list(set(feature_names))
        available_cols = [c for c in feature_names if c in self.df.columns]

        print(f"特征工程完成，共 {len(available_cols)} 个特征")
        print(f"特征列表: {available_cols[:15]}...")

        # 处理缺失值
        for col in available_cols:
            if self.df[col].isnull().any():
                self.df[col] = self.df[col].fillna(0)

        self.feature_names = available_cols
        return self.df, available_cols

    def data_partition(self):
        # 特征工程
        print(f"{'=' * 50}\n开始特征工程\n{'=' * 50}")
        # 调用特征工程类完成特征工程
        self.clean_data()
        self.parse_salary()
        self.encode_experience()
        self.encode_education()
        self.extract_skills()
        self.company_features()
        self.extract_city()
        self.extract_text_features()
        self.create_derived_features()
        df_processed, feature_names = self.prepare_features()
        # # 3. 准备训练数据
        # X = df_processed[feature_names].values
        # y = df_processed['salary_target'].values
        #
        # if len(X) == 0 or len(y) == 0:
        #     print("没有有效数据")
        #     return None, None
        #
        # # 标准化
        # scaler = RobustScaler()
        # X_scaled = scaler.fit_transform(X)
        #
        # # 划分数据
        # X_train, X_test, y_train, y_test =train_test_split(
        #     X_scaled, y, test_size=0.2, random_state=42
        # )
        # # print(f"X_train: {X_train}, X_test: {X_test}, y_train: {y_train}, y_test: {y_test}")
        # print(f"\n训练集大小: {len(X_train)}, 测试集大小: {len(X_test)}")
        # return X_train, X_test, y_train, y_test, feature_names
        return df_processed,feature_names

if __name__ == "__main__":
    engineer = FeatureEngineer()
    engineer.clean_data()
    engineer.parse_salary()
    engineer.encode_experience()
    engineer.encode_education()
    engineer.company_features()
    engineer.extract_skills()
    engineer.extract_city()
    engineer.extract_text_features()
    engineer.create_derived_features()
    engineer.prepare_features()
    engineer.data_partition()


