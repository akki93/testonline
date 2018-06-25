from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://arpit:honey@localhost/testonline'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
import logging
logging.basicConfig()



class Exams(db.Model):
    # __tablename__ = 'questions'
    # __searchable__=['title','content']

    id = db.Column('id', db.Integer, db.Sequence('exam_id_seq', start=1), primary_key=True)
    exam = db.Column(db.Text())

    def __repr__(self):
        return '{}'.format(self.exam)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column('id', db.Integer, db.Sequence('user_id_seq', start=1), primary_key=True, )
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    email = db.Column(db.String(80), unique=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_admin = db.Column(db.Boolean, unique=False, default=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'))
    

class Questions(db.Model):
    # __tablename__ = 'questions'
    # __searchable__=['title','content']

    id = db.Column('id', db.Integer, db.Sequence('question_id_seq', start=1), primary_key=True)
    question = db.Column(db.Text())
    is_active = db.Column(db.Boolean, unique=False, default=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    questions_choices = db.relationship('QuestionsChoices', backref='main_question', cascade="all,delete", lazy=True)
    right_choice = db.Column(db.String)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=True)


class QuestionsChoices(db.Model):
    __tablename__ = 'questions_choices'
    # __searchable__=['title','content']

    id = db.Column('id', db.Integer, db.Sequence('choice_id_seq', start=1), primary_key=True)
    choice = db.Column(db.Text())
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id',ondelete='CASCADE'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_right = db.Column(db.Boolean,  default=False)


class UserQuestionAnswer(db.Model):
    # __tablename__ = 'questions_choices'
    # __searchable__=['title','content']

    id = db.Column('id', db.Integer, db.Sequence('user_question_ans_id_seq', start=1), primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    choice_id = db.Column(db.Integer, db.ForeignKey('questions_choices.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class UserMarksReport(db.Model):
    __tablename__ = 'user_marks_report'
    exam_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    uid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, primary_key=True)
    marks = db.Column(db.Integer)
    percentage = db.Column(db.Float)

if __name__ == '__main__':
    manager.run()