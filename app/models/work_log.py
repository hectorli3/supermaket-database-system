from app import db
from datetime import datetime

class WorkLog(db.Model):
    __tablename__ = 'work_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    clock_in_time = db.Column(db.DateTime(timezone=True))
    clock_out_time = db.Column(db.DateTime(timezone=True))
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'store_id': self.store_id,
            'clock_in_time': self.clock_in_time.isoformat() if self.clock_in_time else None,
            'clock_out_time': self.clock_out_time.isoformat() if self.clock_out_time else None,
            'notes': self.notes,
            'user_name': self.user.username if self.user else None,
            'store_name': self.store.name if self.store else None
        }
    
    def __repr__(self):
        return f'<WorkLog {self.log_id}>' 