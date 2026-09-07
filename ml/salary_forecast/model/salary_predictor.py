import os
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.preprocessing import RobustScaler
from ml.salary_forecast.config.config import Config
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score
from sklearn.model_selection import RandomizedSearchCV, train_test_split
import sys
from datetime import datetime
from ml.salary_forecast.config.config import Config
from ml.salary_forecast.utils.feature_engineer import FeatureEngineer
from catboost import CatBoostRegressor
from sklearn.linear_model import Lasso
from sklearn.ensemble import GradientBoostingRegressor, StackingRegressor
from ml.salary_forecast.model.predicted import Predicted
import json
import pickle

class SalaryPredictor:
    pass

class SalaryPredictor:

    def __init__(self,x_train,x_test,y_train,y_test, feature_names=None):
        self.x_train = x_train
        self.x_test = x_test
        self.y_train = y_train
        self.y_test = y_test
        self.feature_names = feature_names
        self.models = {}
        self.results = {}

    def xgboost_model(self):
        print(f'{"=" * 50}\n训练 XGBoost 模型\n{"=" * 50}')

        xgb_model = xgb.XGBRegressor(
            objective='reg:squarederror',
            tree_method='hist',
            random_state=42,
            # early_stopping_rounds=10,
        )

        param_grid = {
            # 树的深度越浅，模型欠拟合的风险越大
            'max_depth': [7, 8, 9],
            # 学习率
            'learning_rate': [0.025, 0.03, 0.035],
            # 样本数，每棵树使用75%~85%之间，样本数越多，偏差低，但方差很高
            'subsample': [0.75, 0.8, 0.85],
            # 每棵树特征，每棵树只用70%~90%的特征
            'colsample_bytree': [0.7, 0.8, 0.9],
            # 叶子节点，树分的更细，容易过拟合，树更粗壮，防止过拟合
            'min_child_weight': [1, 3, 5],
            # L1惩罚系数
            'reg_alpha': [0.3, 0.5, 0.8],
            # L2惩罚系数
            'reg_lambda': [0.3, 0.5, 0.8],
            # 树的数量
            'n_estimators': [650, 700, 750],
        }

        random_search = RandomizedSearchCV(
            xgb_model, # 待搜索的估计器
            param_distributions=param_grid, # 超参数字典
            n_iter=20, # 随机尝试20组参数组合
            cv=3, # 3折交叉验证
            scoring='neg_mean_squared_error', # MSE
            random_state=42, # 随机种子
            verbose=1, # 输出搜索进度
            n_jobs=-1 # 使用全部CPU并行
        )

        print("进行超参数搜索...")
        sys.stdout.flush() # 刷新输出缓冲区
        # 在训练集上拟合搜索  需要传递eval_set
        random_search.fit(self.x_train, self.y_train)

        # 获取搜索得到的最优参数
        best_params = random_search.best_params_
        print(f"最佳参数：{best_params}")
        sys.stdout.flush()

        # 将训练集封装为 CGBoost DMatrix
        dtrain = xgb.DMatrix(self.x_train, label=self.y_train)
        dtest = xgb.DMatrix(self.x_test, label=self.y_test)

        # 组装参数
        param = {
            "objective": "reg:squarederror",
            "eval_metric": "rmse",
            **best_params,
        }
        # n_estimators 不是 xgb,train 的 booster 参数
        param.pop("n_estimators",None)

        # 定义训练与验证的评估集合
        evals = [(dtrain, 'train'), (dtest, 'eval')]

        # 调用原生训练接口得到 booster
        model = xgb.train(
            param,
            dtrain,
            num_boost_round=best_params.get("n_estimators", 500),
            evals=evals,
            early_stopping_rounds=50,
            verbose_eval=50,
        )

        # 在测试集 DMatrix 上预测
        y_pred = model.predict(dtest)
        # 计算评估指标
        metrix = self.evaluate(y_pred,self.y_test)

        # 将模型存入 models 字典
        self.models["xgboost"] = model

        # 将指标存入 results 字典
        self.results["xgboost"] = metrix

        print(f"XGBoost - R²:{metrix['r2']:.4f},MAE:{metrix['mae']:.4f},RMSE:{metrix['rmse']:.4f}")
        # 保存模型
        self.save_model("xgboost",model, metrix)
        return model

    def catboost_model(self):
        print(f'{"=" * 50}\n训练 CATBoost 模型\n{"=" * 50}')

        cat_model = CatBoostRegressor(
            eval_metric='RMSE',
            random_state=42,
            verbose=False,
        )

        param_grid = {
            # 树的深度越浅，模型欠拟合的风险越大
            'depth': [2, 4, 6, 8],
            # 学习率
            'learning_rate': [0.01, 0.03, 0.05],
            # 样本数，每棵树使用75%~85%之间，样本数越多，偏差低，但方差很高
            'subsample': [0.7, 0.8, 0.9],
            # L2惩罚系数
            'l2_leaf_reg': [1, 3, 5, 7],
            # 树的数量
            'iterations': [300, 500, 700],
        }

        random_search = RandomizedSearchCV(
            cat_model, # 待搜索的估计器
            param_distributions=param_grid, # 超参数字典
            n_iter=15, # 随机尝试20组参数组合
            cv=3, # 3折交叉验证
            scoring='neg_mean_squared_error', # MSE
            random_state=42, # 随机种子
            verbose=1, # 输出搜索进度
            n_jobs=-1 # 使用全部CPU并行
        )

        print("进行超参数搜索...")
        sys.stdout.flush() # 刷新输出缓冲区
        # 在训练集上拟合搜索  需要传递eval_set
        random_search.fit(self.x_train, self.y_train)

        # 获取搜索得到的最优参数
        best_params = random_search.best_params_
        print(f"最佳参数：{best_params}")
        sys.stdout.flush()

        # 使用最佳参数进行模型训练
        model = CatBoostRegressor(
            **best_params,
            eval_metric="RMSE",
            random_state=42,
            verbose=50,
            early_stopping_rounds=50
        )


        # 调用原生训练接口得到 booster
        model.fit(
            self.x_train, self.y_train,
            eval_set=[(self.x_test, self.y_test)],
            use_best_model=True,
        )

        # 在测试集 DMatrix 上预测
        y_pred = model.predict(self.x_test)
        # 计算评估指标
        metrix = self.evaluate(y_pred,self.y_test)

        # 将模型存入 models 字典
        self.models["catboost"] = model

        # 将指标存入 results 字典
        self.results["catboost"] = metrix

        print(f"CatBoost - R²:{metrix['r2']:.4f},MAE:{metrix['mae']:.4f},RMSE:{metrix['rmse']:.4f}")
        # 保存模型
        self.save_model("catboost",model, metrix)
        return model

    def gradient_boosting_model(self):
        print(f'{"=" * 50}\n训练 GradientBoosting 模型\n{"=" * 50}')

        gd_model = GradientBoostingRegressor(
            random_state=42,
        )

        param_grid = {
            "n_estimators": [300, 400, 500],
            # 树的深度越浅，模型欠拟合的风险越大
            'max_depth': [3, 5, 7, 9],
            # 学习率
            'learning_rate': [0.01, 0.03, 0.05, 0.07],
            # 内部节点再划分最小样本数
            "min_samples_split": [5, 10, 20],
            # 叶子最小样本数
            "min_samples_leaf": [3, 5, 10],
            # 行采样比例
            "subsample": [0.7, 0.8, 0.9, 1.0],
        }

        random_search = RandomizedSearchCV(
            gd_model, # 待搜索的估计器
            param_distributions=param_grid, # 超参数字典
            n_iter=15, # 随机尝试20组参数组合
            cv=3, # 3折交叉验证
            scoring='neg_mean_squared_error', # MSE
            random_state=42, # 随机种子
            verbose=1, # 输出搜索进度
            n_jobs=-1 # 使用全部CPU并行
        )

        print("进行超参数搜索...")
        sys.stdout.flush() # 刷新输出缓冲区
        # 在训练集上拟合搜索  需要传递eval_set
        random_search.fit(self.x_train, self.y_train)

        # 获取搜索得到的最优参数
        best_params = random_search.best_params_
        print(f"最佳参数：{best_params}")
        sys.stdout.flush()

        n_estimators = best_params.get("n_estimators", 300)
        # 使用最佳参数进行模型训练
        model = GradientBoostingRegressor(
            **best_params,
            random_state=42,
            verbose=False,
        )
        print(f"按每 {min(50, n_estimators)} 轮输出一次训练进度")

        # 调用原生训练接口得到 booster
        model = self.fit_with_progress(
            model,
            "GradientBoosting",
            n_estimators,
            log_interval=50
        )

        # 在测试集 DMatrix 上预测
        y_pred = model.predict(self.x_test)
        # 计算评估指标
        metrix = self.evaluate(y_pred,self.y_test)

        # 将模型存入 models 字典
        self.models["gradient_boosting"] = model

        # 将指标存入 results 字典
        self.results["gradient_boosting"] = metrix

        print(f"gradient_boosting - R²:{metrix['r2']:.4f},MAE:{metrix['mae']:.4f},RMSE:{metrix['rmse']:.4f}")
        # 保存模型
        self.save_model("gradient_boosting",model, metrix)
        return model

    def fit_with_progress(self, model, model_name, n_estimators, log_interval=50):
        """
        对模型按树的数量分段训练并输出观测信息
        """
        model.set_params(warm_start=True)
        checkpoints = list(range(log_interval, n_estimators, log_interval))
        if not checkpoints or checkpoints[-1] != n_estimators:
            checkpoints.append(n_estimators)

        for n_trees in checkpoints:
            model.set_params(n_estimators=n_trees)
            model.fit(self.x_train, self.y_train)
            train_pred = model.predict(self.x_train)
            test_pred = model.predict(self.x_test)
            train_rmse = np.sqrt(mean_squared_error(self.y_train, train_pred))  # 计算训练集 RMSE
            test_rmse = np.sqrt(mean_squared_error(self.y_test, test_pred))  # 计算测试集 RMSE
            print(
                f"[{n_trees}]\t{model_name}-train-rmse:{train_rmse:.5f}\t" 
                f"{model_name}-eval-rmse:{test_rmse:.5f}"
            )
            sys.stdout.flush()
        return model

    def stacking_ensemble_model(self):
        """构建Stacking集成模型"""
        print(f"{'=' * 60}\n训练 Stacking 集成模型\n{'=' * 60}")

        # 确保所有单模型已训练
        if "xgboost" not in self.models:
            self.xgboost_model()
        if "catboost" not in self.models:
            self.catboost_model()
        if "gradient_boosting" not in self.models:
            self.gradient_boosting_model()

        # 基础模型
        base_model = [
            (
                "xgboost", xgb.XGBRegressor(
                    n_estimators=500,
                    learning_rate=0.03,
                    max_depth=6,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                )
            ),
            (
                "catboost", CatBoostRegressor(
                    iterations=500,
                    learning_rate=0.05,
                    depth=6,
                    random_state=42,
                    verbose=False,
                )
            ),
            (
                "gb", GradientBoostingRegressor(
                    n_estimators=300,
                    learning_rate=0.05,
                    max_depth=5,
                    subsample=0.8,
                    random_state=42,
                )
            )
        ]

        # 岭回归
        meta_model = Lasso(alpha=0.05)

        # 构建Stacking
        model = StackingRegressor(
            estimators=base_model,  # 传入基学习
            final_estimator=meta_model,  # 传入原模型
            cv=5,
            n_jobs=-1
        )

        print("训练Stacking集成模型，使用5折交叉验证")
        sys.stdout.flush()
        # 在训练集上拟合Stacking
        model.fit(self.x_train, self.y_train)
        # 测试集预测
        y_pred = model.predict(self.x_test)
        # 计算指标
        metrics = self.evaluate(y_pred, self.y_test)
        # 将模型存入 models字典
        self.models["stacking_ensemble"] = model
        # 将指标存入results字典
        self.results["stacking_ensemble"] = metrics
        print(f"stacking_ensemble - R²: {metrics['r2']:.4f}, MAE: {metrics['mae']:.4f}, RMSE: {metrics['rmse']:.4f}")
        # 保存模型
        self.save_model("stacking_ensemble", model, metrics)
        return y_pred

    def train(self):
        """模型训练方法 一次训练四个模型并打印"""
        # 训练模型
        self.xgboost_model()
        self.catboost_model()
        self.gradient_boosting_model()
        self.stacking_ensemble_model()

        #结果汇总
        print(f"{'=' * 60}\n模型性能汇总\n{'=' * 60}")
        results_data = []
        model_names = {
            "xgboost": "XGBoost",
            "catboost": "CatBoost",
            "gradient_boosting": "梯度提升",
            "stacking_ensemble":"Stacking集成"
        }
        for model_key,model_name in model_names.items():
            if model_key in self.results:
                results_data.append({
                    "模型":model_names,
                    "R²":self.results[model_key]["r2"],
                    "MAE":self.results[model_key]["mae"],
                    "RMSE":self.results[model_key]["rmse"],
                    "相对误差百分比":self.results[model_key]["relative_error"],
                    "精度(+-20%)":f"{self.results[model_key]['accuracy_20']:.2f}%",
                })
        results_df = pd.DataFrame(results_data)
        print(results_df.to_string(index=False))

        # 检查模型效果
        if len(results_df) > 0:
            r2_value = results_df["R²"]
            print(f"\nR²范围:{r2_value.min():.4f} - {r2_value.max():.4f}")
            if all(r2_value > 0.93):
                print("所有模型R²>0.93,满足要求")
            elif all(r2_value < 0.90):
                print("所有模型R²>0.90,接近要求")
            else:
                print("部分模型未达到要求，需继续优化")

        # 保存全部模型汇总
        print("\n保存全部模型汇总...")
        try:
            os.makedirs(Config.MODEL_SAVE_PATH, exist_ok=True)
            save_data = {
                'predictor': self,
                'feature_names': self.feature_names,
                'model_info': {
                    'train_date': datetime.now().isoformat(),
                    'train_size': len(self.X_train),
                    'test_size': len(self.X_test),
                    'feature_count': (
                        len(self.feature_names)
                        if self.feature_names is not None
                        else self.X_train.shape[1]
                    ),
                    'data_source': 'database'
                }
            }
            save_path = os.path.join(Config.MODEL_SAVE_PATH, 'optimized_salary_prediction_model.pkl')
            joblib.dump(save_data, save_path)
            print(f"全部模型已保存到 {save_path}")  #
        except Exception as e:
            print(f"模型保存失败: {e}")
        print(f"{'=' * 50}\n薪资预测模型训练完成！\n{'=' * 50}")

    def save_feature_names(self):
        """保存特征名称"""
        with open(os.path.join(Config.MODEL_SAVE_PATH, 'feature_names.pkl'), 'wb') as f:  # 以二进制写模式打开 pkl 文件
            pickle.dump(self.feature_names, f)  # 将特征名列表序列化写入 pkl
        with open(os.path.join(Config.MODEL_SAVE_PATH, 'feature_names.json'), 'w', encoding='utf-8') as f:  # 以 UTF-8 文本写 JSON
            json.dump(self.feature_names, f, ensure_ascii=False, indent=2)

    def evaluate(self,y_pred,y_test):
        y_pred = np.array(y_pred).flatten()
        y_true = np.array(y_test).flatten()

        mae = mean_absolute_error(y_test, y_pred)

        rmse = np.sqrt(mean_squared_error(y_true, y_pred))

        r2 = r2_score(y_true, y_pred)

        relative_error = np.mean(np.abs((y_true - y_pred) / (y_true + 1))) * 100

        accuracy_20 = np.mean(np.abs((y_pred - y_true) / y_true) <= 0.2) * 100
        return {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "relative_error": relative_error,
            "accuracy_20": accuracy_20,
        }

    def save_model(self,model_key,model,metrix=None):
        os.makedirs(Config.MODEL_SAVE_PATH, exist_ok=True)
        save_path = os.path.join(Config.MODEL_SAVE_PATH,f"{model_key}_model.pkl")
        save_data = {
            "model": model,
            "model_key": model_key,
            "metrix": metrix,
            "feature_names": self.feature_names,
            "train_data":datetime.now().isoformat(),
            "train_size":len(self.x_train),
            "test_size":len(self.x_test),
            "feature_count":(len(self.feature_names)
                            if self.feature_names is not None
                            else self.x_train.shape[1]
                          ),
        }
        joblib.dump(save_data, save_path)
        print(f"{model_key}模型 已保存至 {save_path}")

if __name__ == "__main__":
    # 创建特征工程类
    fe = FeatureEngineer()
    # 调用方法获取特征
    df_processed, feature_names = fe.data_partition()
    # 准备训练数据
    X = df_processed[feature_names].values
    y = df_processed['salary_target'].values

    if len(X) == 0 or len(y) == 0:
        print("没有有效数据")
    else:
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)
        has_range = (
            'salary_min_parsed' in df_processed.columns
            and 'salary_max_parsed' in df_processed.columns
        )
        indices = np.arange(len(y))
        if has_range:
            X_train, X_test, y_train, y_test, _, idx_test = train_test_split(
                X_scaled, y, indices, test_size=0.2, random_state=42
            )
            test_min = df_processed['salary_min_parsed'].values[idx_test]
            test_max = df_processed['salary_max_parsed'].values[idx_test]
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            test_min = test_max = None

        print(f"\n训练集大小: {len(X_train)}, 测试集大小: {len(X_test)}")
        print(f"目标口径: (最低薪+最高薪)/2，范围: {y.min():.0f} ~ {y.max():.0f}")

        # 先保存与训练同源的 Scaler，再训练；验证集必须用同一 X_test
        joblib.dump(scaler, Config.ROBUST_SCALER_SAVE_PATH)
        print(f"RobustScaler 已保存 -> {Config.ROBUST_SCALER_SAVE_PATH}")

        salary_predictor = SalaryPredictor(X_train, X_test, y_train, y_test, feature_names)
        salary_predictor.save_feature_names()
        salary_predictor.train()

        # 同会话验证：传入 feature_names + 内存模型，避免列名落成 0,1,2...
        predicted = Predicted(X_test, y_test, feature_names=feature_names)
        predicted.models = dict(salary_predictor.models)
        predicted.save_validation_dataset(salary_min=test_min, salary_max=test_max)
        predicted.validate_all_models()












