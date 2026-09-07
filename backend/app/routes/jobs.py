"""
岗位数据处理：原始数据查询、更新、删除、导出
"""
from flask import Blueprint, jsonify, request
from ..services.job_service import (
    filter_raw_query,
    update_raw_job as update_raw_job_service,  # 别名，避免和路由函数同名
    delete_raw_job,
    export_jobs_response
)
from ..models import JobRaw
from ..config import Config

# 定义蓝图
jobs_bp = Blueprint('jobs', __name__)


def _filter_args():
    """从请求参数中提取岗位筛选条件"""
    return {
        "platform": request.args.get("platform"),
        "city": request.args.get("city"),
        "keyword": request.args.get("keyword"),
        "company": request.args.get("company"),
        "education": request.args.get("education"),
    }


@jobs_bp.route('/raw', methods=['GET'])
def get_raw_jobs():
    """分页查询所有原始岗位数据"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    filters = _filter_args()
    query = filter_raw_query(**filters)
    pagination = query.order_by(JobRaw.crawl_time.desc()).paginate(
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


@jobs_bp.route('/raw/<int:job_id>', methods=['PUT'])
def update_raw_job_route(job_id):          # 改名为 _route，不再遮蔽服务层函数
    """按ID更新一条岗位记录"""
    data = request.get_json() or {}
    job = update_raw_job_service(job_id, data)  # 调用服务层函数
    if not job:
        return jsonify({"code": 404, "message": "记录不存在"}), 404
    return jsonify({"code": 200, "data": job.to_dict(), "message": "更新成功"})


@jobs_bp.route('/raw/<int:job_id>', methods=['DELETE'])
def remove_raw(job_id):
    """按ID删除一条岗位记录"""
    if not delete_raw_job(job_id):
        return jsonify({"code": 404, "message": "记录不存在"}), 404
    return jsonify({"code": 200, "message": "删除成功"})


@jobs_bp.route('/raw/export', methods=['GET'])
def export_raw():
    """导出原始岗位数据（支持 excel/json/txt）"""
    fmt = request.args.get('format', 'excel')
    if fmt not in ('excel', 'json', 'txt'):
        return jsonify({'code': 400, 'message': '不支持的导出格式'}), 400

    filters = _filter_args()
    items = (
        filter_raw_query(**filters)
        .order_by(JobRaw.crawl_time.desc())
        .limit(Config.EXPORT_LIMIT)
        .all()
    )

    if not items:
        return jsonify({'code': 400, 'message': '没有可导出的数据'}), 400

    response = export_jobs_response(items, fmt, '原始数据')
    if not response:
        return jsonify({'code': 400, 'message': '导出失败，请检查服务层实现'}), 400
    return response


@jobs_bp.route("/platforms", methods=['GET'])
def get_platforms():
    """获取招聘平台列表"""
    platform = [{"key": k, "name": v} for k, v in Config.PLATFORM_NAMES.items()]
    return jsonify({"code": 200, "data": platform})