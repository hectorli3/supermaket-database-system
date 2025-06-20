from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User

auth_ns = Namespace('auth', description='身份验证相关操作')

# 定义请求和响应模型
login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码')
})

register_model = auth_ns.model('Register', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码'),
    'role': fields.String(required=True, description='角色', enum=['system_admin', 'store_manager', 'cashier']),
    'store_id': fields.Integer(description='门店ID（员工必填）')
})

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        """用户登录"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                access_token = create_access_token(identity=user.user_id)
                refresh_token = create_refresh_token(identity=user.user_id)
                
                return {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': user.to_dict()
                }, 200
            
            return {'message': '用户名或密码错误'}, 401
        except Exception as e:
            return {'message': f'登录失败: {str(e)}'}, 500

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(register_model)
    def post(self):
        """用户注册"""
        try:
            data = request.get_json()
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=data['username']).first():
                return {'message': '用户名已存在'}, 400
            
            # 创建新用户
            user = User(
                username=data['username'],
                role=data['role'],
                store_id=data.get('store_id')
            )
            user.set_password(data['password'])
            
            db.session.add(user)
            db.session.commit()
            
            return {'message': '注册成功', 'user_id': user.user_id}, 201
        except Exception as e:
            db.session.rollback()
            return {'message': f'注册失败: {str(e)}'}, 500

@auth_ns.route('/refresh')
class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """刷新令牌"""
        try:
            current_user_id = get_jwt_identity()
            new_token = create_access_token(identity=current_user_id)
            return {'access_token': new_token}, 200
        except Exception as e:
            return {'message': f'刷新令牌失败: {str(e)}'}, 500

@auth_ns.route('/profile')
class Profile(Resource):
    @jwt_required()
    def get(self):
        """获取当前用户信息"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            if user:
                return user.to_dict(), 200
            return {'message': '用户不存在'}, 404
        except Exception as e:
            return {'message': f'获取用户信息失败: {str(e)}'}, 500