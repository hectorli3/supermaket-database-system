from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from app import db
from app.models.user import User

users_ns = Namespace('users', description='用户管理')

@users_ns.route('/')
class UserList(Resource):
    @jwt_required()
    def get(self):
        """获取所有用户"""
        users = User.query.all()
        return [user.to_dict() for user in users], 200