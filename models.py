from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Job(db.Model):
    id = db.Column(db.String, primary_key=True)
    status = db.Column(db.String(50))
    filename = db.Column(db.String(100))

class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.String, db.ForeignKey('job.id'), nullable=False)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    address = db.Column(db.String(200))


