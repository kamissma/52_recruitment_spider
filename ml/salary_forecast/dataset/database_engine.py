"""数据库连接"""
from ml.salary_forecast.config.config import Config
from sqlalchemy import create_engine

class DatabaseEngine:
    @classmethod
    def get_mysql_engine(cls):
        """获取MYSQL连接引擎"""
        try:
            connection_string = (f"mysql+pymysql://{Config.MYSQL_CONFIG['user']}"
                                 f":{Config.MYSQL_CONFIG['password']}"
                                 f"@{Config.MYSQL_CONFIG['host']}"
                                 f":{Config.MYSQL_CONFIG['port']}"
                                 f"/{Config.MYSQL_CONFIG['database']}"
                                 f"?charset={Config.MYSQL_CONFIG['charset']}")
            # 创建引擎
            engine = create_engine(connection_string)
            return engine
        except Exception as e:
            print(f"MYSQL连接失败:{e}")
            return None