from models_front import db
from datetime import datetime

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    bind_key = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(10), nullable=False)   
    time = db.Column(db.String(8), nullable=False)   
    action = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<ActivityLog {self.login} | {self.action} | {self.result}>'

def init_log_db():
    pass

def record_activity(usr_name, act_name, res_status):
    now = datetime.now()
    new_entry = ActivityLog(
        login=usr_name,
        date=now.strftime('%Y-%m-%d'),
        time=now.strftime('%H:%M:%S'),
        action=act_name,
        result=res_status
    )
    try:
        db.session.add(new_entry)
        db.session.commit()
    except Exception:
        db.session.rollback()