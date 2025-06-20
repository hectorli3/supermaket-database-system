from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from app.models.work_log import WorkLog

work_logs_ns = Namespace('work_logs', description='工作日志管理')

@work_logs_ns.route('/')
class WorkLogList(Resource):
    @jwt_required()
    def get(self):
        """获取工作日志"""
        logs = WorkLog.query.all()
        return [log.to_dict() for log in logs], 200 