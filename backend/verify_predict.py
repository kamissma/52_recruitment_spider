# -*- coding: utf-8 -*-
"""验证：升级 sklearn 后模型可加载、预测可用"""
import traceback
from app import create_app

app = create_app()
with app.app_context():
    import sklearn, joblib
    print(f'sklearn={sklearn.__version__} joblib={joblib.__version__}')
    from app.services.predict_service import PredictService
    try:
        data = PredictService.predict(
            skills=['python'],
            experience_years=3,
            education_level=3,
            city='广州',
            company_size='150-500人',
            job_title='python',
            model_name='gradient_boosting',
        )
        print('PREDICT_OK avg_k=', data.get('predicted_salary_avg'))
    except Exception:
        traceback.print_exc()
        print('PREDICT_FAILED')
