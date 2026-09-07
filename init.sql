-- 招聘数据采集与分析系统 - 数据库初始化脚本
CREATE DATABASE IF NOT EXISTS recruitment_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE recruitment_db;

-- 原始岗位数据表
CREATE TABLE IF NOT EXISTS job_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(50) NOT NULL COMMENT '招聘平台: boss/zhaopin/lagou/liepin',
    job_id VARCHAR(100) COMMENT '平台岗位ID',
    task_id VARCHAR(100) COMMENT '任务ID',
    title VARCHAR(200) NOT NULL COMMENT '岗位名称',
    company VARCHAR(200) COMMENT '公司名称',
    city VARCHAR(50) COMMENT '城市',
    salary_raw VARCHAR(100) COMMENT '原始薪资文本',
    salary_min DECIMAL(10,2) COMMENT '最低薪资(K)',
    salary_max DECIMAL(10,2) COMMENT '最高薪资(K)',
    experience VARCHAR(50) COMMENT '经验要求',
    education VARCHAR(50) COMMENT '学历要求',
    skills TEXT COMMENT '技能要求(JSON)',
    description TEXT COMMENT '岗位描述',
    publish_time DATETIME COMMENT '发布时间',
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    is_cleaned TINYINT DEFAULT 0 COMMENT '是否已清洗',
    INDEX idx_platform (platform),
    INDEX idx_city (city),
    INDEX idx_crawl_time (crawl_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 清洗后岗位数据表
CREATE TABLE IF NOT EXISTS job_clean (
    id INT AUTO_INCREMENT PRIMARY KEY,
    raw_id INT COMMENT '关联原始数据ID',
    platform VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    company VARCHAR(200),
    city VARCHAR(50),
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    salary_avg DECIMAL(10,2) COMMENT '平均薪资(K)',
    experience_years INT COMMENT '经验年限',
    education_level INT COMMENT '学历等级 1-5',
    skills TEXT COMMENT '技能标签(JSON)',
    skill_count INT DEFAULT 0 COMMENT '技能数量',
    clean_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_platform (platform),
    INDEX idx_city (city),
    INDEX idx_salary (salary_avg),
    FOREIGN KEY (raw_id) REFERENCES job_raw(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 爬虫任务记录表
CREATE TABLE IF NOT EXISTS crawl_task (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    keyword VARCHAR(100) COMMENT '搜索关键词',
    city VARCHAR(50) COMMENT '目标城市',
    status ENUM('pending','running','completed','failed') DEFAULT 'pending',
    total_count INT DEFAULT 0 COMMENT '采集数量',
    start_time DATETIME,
    end_time DATETIME,
    error_msg TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 薪资预测记录表
CREATE TABLE IF NOT EXISTS salary_prediction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resume_name VARCHAR(200),
    predicted_salary_min DECIMAL(10,2),
    predicted_salary_max DECIMAL(10,2),
    predicted_salary_avg DECIMAL(10,2),
    matched_jobs INT COMMENT '匹配岗位数',
    skills_extracted TEXT COMMENT '提取的技能(JSON)',
    experience_years INT,
    education_level INT,
    confidence DECIMAL(5,4) COMMENT '预测置信度',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户表
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(120) UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(256) NOT NULL COMMENT '密码哈希',
    nickname VARCHAR(50) COMMENT '昵称',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 统计分析缓存表
CREATE TABLE IF NOT EXISTS stats_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stat_type VARCHAR(50) NOT NULL COMMENT '统计类型',
    stat_key VARCHAR(100) COMMENT '统计维度',
    stat_value TEXT COMMENT '统计值(JSON)',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_type_key (stat_type, stat_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
