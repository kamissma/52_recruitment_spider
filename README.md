# 招聘信息采集与数据分析系统（52_recruitment_spider）

招聘信息**爬取 → 清洗 → 可视化分析 → 薪资预测**的一体化实习项目。

## 模块组成
| 模块 | 技术栈 | 说明 |
| --- | --- | --- |
| `recruitment_spider` | Scrapy | 招聘网站职位信息采集（含 stealth 反爬处理） |
| `backend` | Flask / SQLAlchemy / MySQL | REST API：用户认证、爬虫任务、数据清洗、统计分析、薪资预测 |
| `frontend` | Vue3 / Element Plus / ECharts / Vite | 数据可视化看板与管理界面 |
| `ml/salary_forecast` | XGBoost / CatBoost / scikit-learn | 基于职位特征的薪资预测 |

## 目录结构
```
.
├── backend                  # Flask 后端
│   ├── app
│   │   ├── models/          # ORM 数据模型
│   │   ├── routes/          # API 路由（auth/crawl/jobs/predict/rinse/stats）
│   │   ├── services/        # 业务逻辑
│   │   ├── utils/           # 通用工具
│   │   ├── .env.example     # 环境变量示例
│   │   └── config.py
│   └── run.py               # 后端启动入口
├── frontend                 # Vue3 前端
│   ├── src/                 # 页面 / 组件 / 路由 / 状态管理
│   ├── index.html
│   └── package.json
├── ml/salary_forecast       # 薪资预测模块
│   ├── config/ dataset/ model/ utils/
│   └── data/                # 验证数据（体积较大，未入库）
├── recruitment_spider       # Scrapy 爬虫
├── API接口文档.apifox.json  # 接口文档（Apifox）
├── init.sql                 # 数据库初始化脚本
├── requirements.txt         # Python 依赖
└── scrapy.cfg
```

## 环境要求
- Python 3.9+（开发环境为 3.11）
- Node.js 16+
- MySQL 8.x

## 快速开始
1. **初始化数据库**：将 `init.sql` 导入 MySQL。
2. **配置后端**：复制 `backend/app/.env.example` 为 `backend/app/.env`，填写数据库连接、`SECRET_KEY` 等。
3. **安装依赖**：`pip install -r requirements.txt`
4. **启动后端**：`python backend/run.py`
5. **启动前端**：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
6. **运行爬虫（可选）**：`scrapy crawl <爬虫名>`（爬虫列表见 `recruitment_spider/spiders/`）。

## 说明
- 原始抓取数据（`招聘信息-job_raw.sql`，约 79 MB）及模型训练产物（模型文件、验证数据）体积较大，未纳入本仓库；薪资预测模型可通过 `ml/salary_forecast` 重新训练生成。
- `.env` 为本地敏感配置（含数据库密码、`SECRET_KEY`），已通过 `.gitignore` 排除，请勿提交或外传。