from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
db=SQLAlchemy()
class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(150),unique=True,nullable=False)
    password=db.Column(db.String(150),nullable=False)
    role=db.Column(db.String(50),default='user') #Phan quyen admin/user
class Word(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    english_word=db.Column(db.String(100),nullable=False,index=True)
    phonetics=db.Column(db.String(100))
    word_type=db.Column(db.String(50)) #danh tu, dong tu, tinh tu,...
    vietnamese_meaning=db.Column(db.Text,nullable=False)
    example_sentence=db.Column(db.Text)
    added_by=db.Column(db.Integer,db.ForeignKey('user.id')) #Ai la nguoi dong gop tu nay
    creator = db.relationship('User', backref='words')
