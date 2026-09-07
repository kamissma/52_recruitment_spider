from flask import Blueprint,current_app,jsonify,request
from ..config import Config
from ..services.predict_service import PredictService
from ..services.resume_parser import ResumeParser

predict_bp = Blueprint("predict",__name__)

@predict_bp.route("/history",methods=["GET"])
def prediction_history():
    """分页查询历史薪资预测记录"""
    page = request.args.get("page",1,type=int)
    per_page = request.args.get("per_page",10,type=int)
    data = PredictService.get_history(page=page,per_page=per_page)
    return jsonify({
        "code":200,
        "data":data
    })

@predict_bp.route('/manual', methods=['POST'])
def manual_predict():
    """根据职位/学历/公司规模/城市/经验等进行薪资预测（输出平均值）。"""
    data = request.get_json() or {}
    skills = data.get('skills', [])
    city = data.get('city', '')
    model_name = data.get('model') or data.get('model_name') or 'gradient_boosting'
    company_size = data.get('company_size') or data.get('companySize') or ''
    job_title = data.get('job') or data.get('job_title') or data.get('title') or ''
    experience = data.get('experience')
    education = data.get('education')
    experience_years = data.get('experience_years')
    education_level = data.get('education_level')

    if not job_title and not skills:
        return jsonify({'code': 400, 'message': '请选择职位或至少填写一项技能'}), 400

    if not skills and job_title:
        from ..services.data_cleaner import extract_skills
        skills = extract_skills(job_title) or [job_title]

    try:
        result = PredictService.predict(
            skills=skills,
            experience=experience,
            experience_years=experience_years,
            education=education,
            education_level=education_level,
            resume_name=job_title or '手动输入',
            city=city,
            model_name=model_name,
            company_size=company_size,
            job_title=job_title,
        )
        return jsonify({'code': 200, 'data': result})
    except FileNotFoundError as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': f'预测失败: {e}'}), 500