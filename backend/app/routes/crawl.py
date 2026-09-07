"""
爬虫调度路由 用于启动数据采集、查询任务、删除任务
"""
from flask import Blueprint,jsonify,request
from ..services.crawl_service import CrawlService

#定义蓝图
crawl_dp = Blueprint('crawl',__name__)

@crawl_dp.route('/start',methods=['POST'])
def start_crawl():
    """启动爬虫启动任务(可选平台、城市、关键词、页数)"""
    #接收参数
    data = request.get_json() or {}
    tasks = CrawlService.start_crawl(
        platform = data.get('platform'),
        keyword = data.get('keyword'),
        city = data.get('city'),
        pages = data.get('pages'),
    )
    #返回结果
    return jsonify({"code":200,"data":tasks,"message":"success"})

@crawl_dp.route('/tasks',methods=['GET'])
def get_tasks():
    """分页查询爬虫任务列表"""
    #接收页面和每页展示条数
    page = request.args.get("page",1,type=int)
    page_size = request.args.get("per_page",20,type=int)
    #调用服务层获取所有数据
    data = CrawlService.get_tasks(page, page_size)
    #返回数据
    return jsonify({"code":200,"data":data})

@crawl_dp.route('/tasks/<int:task_id>',methods=['DELETE'])
def delete_task(task_id):
    """按ID删除爬虫任务记录"""
    ok,message = CrawlService.delete_task(task_id)
    if not ok:
        #任务不存在返回的信息
        code = 404 if message == "任务不存在" else 400
        return jsonify({"code":code,"message":message})
    #任务存在返回的信息
    return jsonify({"code":200,"message":message})