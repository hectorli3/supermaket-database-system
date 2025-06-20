from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_restx import Api
from config import config
import warnings
import sqlalchemy.exc

# 忽略SQLAlchemy版本警告
warnings.filterwarnings('ignore', category=sqlalchemy.exc.SAWarning)

# 初始化扩展
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    
    # 创建API
    api = Api(
        app,
        version='1.0',
        title='超市管理系统API',
        description='基于OpenGauss的超市管理系统后端API',
        doc='/docs/'
    )
    
    # 注册蓝图
    from app.resources import register_namespaces
    register_namespaces(api)
    
    # 添加健康检查路由
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': '超市管理系统后端正常运行'}, 200
    
    return app 