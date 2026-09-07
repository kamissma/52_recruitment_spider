"""数据清洗"""
from flask import Blueprint, jsonify, request
from ..models import JobClean
from ..config import Config
from ..services.data_cleaner import DataCleaner
from ..services.rinse_service import (
    filter_clean_query,
    update_clean_job,       # 新增导入
    delete_clean_job,
    export_jobs_response
)

rinse_bp = Blueprint('rinse', __name__)


def _filter_args():
    return {
        "platform": request.args.get("platform"),
        "city": request.args.get("city"),
        "keyword": request.args.get("keyword"),
        "company": request.args.get("company"),
        "education": request.args.get("education"),
    }


# 专项清洗类型 → 处理函数
CLEAN_TYPE_HANDLERS = {
    'salary': DataCleaner.clean_salary,
    'education': DataCleaner.clean_education,
    'experience': DataCleaner.clean_experience,
    'city': DataCleaner.clean_city,
    'job': DataCleaner.clean_job,
    'skills': DataCleaner.clean_skills,
    'description': DataCleaner.clean_description,
}


@rinse_bp.route('/clean', methods=['GET', 'POST'])
def get_clean_jobs():
    """分页查询清洗后岗位数据"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    filters = _filter_args()
    query = filter_clean_query(**filters)
    pagination = query.order_by(JobClean.clean_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "code": 200,
        "data": {
            "items": [j.to_dict() for j in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
        }
    })


@rinse_bp.route('/clean/run', methods=['POST'])
def clean_run():
    """执行数据清洗"""
    data = request.get_json() or {}
    platform = data.get("platform")
    count = DataCleaner.clean_all_uncleaned(platform=platform)
    details = {}
    for name, handler in CLEAN_TYPE_HANDLERS.items():
        try:
            if name == "skills":
                details[name] = handler(platform=platform, top_n=50)
            elif name == "description":
                details[name] = handler(platform=platform, max_features=100)
            else:
                details[name] = handler(platform=platform)
        except Exception as e:
            details[name] = {"error": str(e)}
    return jsonify({
        "code": 200,
        "data": {
            "cleaned_count": count,
            "details": details
        },
        "message": "清洗完成"
    })


@rinse_bp.route('/clean/<int:job_id>', methods=['PUT'])  # 修正：jon_id → job_id
def update_clean_route(job_id):   # 改名为 _route，不再遮蔽服务层函数
    """按ID更新一条清洗后的岗位记录"""
    data = request.get_json() or {}
    print(data)
    job = update_clean_job(job_id, data)   # 调用服务层函数
    if not job:
        return jsonify({"code": 404, "message": "记录不存在"}), 404
    return jsonify({
        "code": 200,
        "data": job.to_dict(),
        "message": "更新成功"
    })


@rinse_bp.route('/clean/<int:job_id>', methods=['DELETE'])  # 修正：jon_id → job_id
def remove_clean(job_id):   # 修正：jon_id → job_id
    """删除一条清洗记录"""
    if not delete_clean_job(job_id):
        return jsonify({"code": 404, "message": "记录不存在"}), 404
    return jsonify({"code": 200, "message": "删除成功"})


@rinse_bp.route('/clean/export', methods=['GET'])
def export_clean():
    """导出清洗后岗位数据（支持 excel/json/txt）"""
    fmt = request.args.get('format', 'excel')
    if fmt not in ('excel', 'json', 'txt'):
        return jsonify({'code': 400, 'message': '不支持的导出格式'}), 400
    filters = _filter_args()
    items = (
        filter_clean_query(**filters)
        .order_by(JobClean.clean_time.desc())
        .limit(Config.EXPORT_LIMIT)
        .all()
    )
    if not items:
        return jsonify({'code': 400, 'message': '没有可导出的数据'}), 400
    response = export_jobs_response(items, fmt, '清洗数据')
    if not response:
        return jsonify({'code': 400, 'message': '导出失败'}), 400
    return response