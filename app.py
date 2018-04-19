from flask import Flask, render_template, request, flash,redirect, url_for, session
from forms import LoginForm, RegisterForm,PasswordResetForm, AddQuestionForm,QuizForm
from flask_sqlalchemy import SQLAlchemy
import datetime

#adding password security using werkzug
from werkzeug.security import generate_password_hash, check_password_hash

#adding flask login to resrict user to do first sign in 
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

import operator

app = Flask(__name__,template_folder='../testonline/templates')

app.config["SECRET_KEY"]="Thisisascretkey"
app.config['SQLALCHEMY_DATABASE_URI']='postgresql+psycopg2://arpit:honey@localhost/testonline'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=True

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'open_login'

class User(UserMixin,db.Model):
  __tablename__ = 'users'
  
  id = db.Column('id', db.Integer, db.Sequence('user_id_seq',start=1), primary_key=True,)
  username = db.Column(db.String(80), unique=True)
  password = db.Column(db.String(80))
  email = db.Column(db.String(80), unique=True)
  created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  is_admin = db.Column(db.Boolean, unique=False, default=False)

  def __init__(self, username, password, email, is_admin):
      self.username = username
      self.password = password
      self.email = email
      self.is_admin = is_admin

class Questions(db.Model):
  # __tablename__ = 'questions'
  # __searchable__=['title','content']
  
  id = db.Column('id', db.Integer, db.Sequence('question_id_seq',start=1),primary_key=True)
  question = db.Column(db.Text())
  is_active = db.Column(db.Boolean, unique=False, default=False)
  created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  questions_choices = db.relationship('QuestionsChoices', backref='main_question', cascade="all,delete",lazy=True)
  right_choice = db.Column(db.String)

class QuestionsChoices(db.Model):
  __tablename__ = 'questions_choices'
  # __searchable__=['title','content']
  
  id = db.Column('id', db.Integer, db.Sequence('choice_id_seq',start=1),primary_key=True)
  choice = db.Column(db.Text())
  question_id = db.Column(db.Integer,db.ForeignKey('questions.id'), nullable=False)
  created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class UserQuestionAnswer(db.Model):
  # __tablename__ = 'questions_choices'
  # __searchable__=['title','content']
  
  id = db.Column('id', db.Integer, db.Sequence('user_question_ans_id_seq',start=1),primary_key=True)
  question_id = db.Column(db.Integer,db.ForeignKey('questions.id'), nullable=False)
  choice_id = db.Column(db.Integer,db.ForeignKey('questions_choices.id'), nullable=False)
  created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  user_id = db.Column(db.Integer,db.ForeignKey('users.id'), nullable=False)
 
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

@app.route("/sign_in", methods=["GET","POST"])
def open_login():
  form = LoginForm()
  if form.validate_on_submit():
    # return '<h1>'+form.username.data +' ' +form.password.data+ '</h1>'
    user = User.query.filter_by(username=form.username.data).first()
    try:
      if user:
        if check_password_hash(user.password,form.password.data) :
          login_user(user, remember=form.remember.data)
          return redirect(url_for('start_test'))
        else:
          flash("Password does not match.Forgot password ?")
      else:
          flash("User does not exist ! Please Create account.")

    except Exception as e:
      flash("User does not exist ! Please Create account.")
 
  return render_template("login_activity.html",form=form)
  # return render_template("login_activity.html")

@app.route("/create_account", methods=["GET","POST"])
def create_login():
  form = RegisterForm()
  if form.validate_on_submit():
    hash_password = generate_password_hash(form.password.data,method='sha256')
    try :
      new_user = User(username=form.username.data, email=form.email.data, password= hash_password,is_admin=False)
      db.session.add(new_user)
      db.session.commit()
      flash("User created sucessfully! now login.")
    except Exception as inst:
      flash("User name or Email is already created!.")


    # return "New User Has been created!"
    # return '<h1>'+form.username.data +' ' +form.password.data+ '</h1>'

  return render_template("create_account.html", form=form)
  # return render_template("create_account.html")

@app.route("/logout")
@login_required
def log_out():
  logout_user()
  return redirect(url_for('open_login'))

@app.route("/password_reset", methods=["GET","POST"])
def forgot_password():
  form = PasswordResetForm()
  if form.validate_on_submit():
    user = User.query.filter_by(email=form.email.data).first()
    try:
      if user:
        #when both password are same
        if form.new_password.data == form.confirm_password.data:
          hash_password = generate_password_hash(form.confirm_password.data,method='sha256')
          user.password = hash_password
          db.session.commit()
          flash("Password reset sucessfully!.")
          # return '<h1>'+ 'Password is reset' +'</h1>'
        else:
          flash("Password not match!.")
    except Exception as e:
      flash("There is no user for this Email.")
    

  return render_template("forgot_password.html",form=form)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_test',methods=['GET', 'POST'])
def submit_test():
    if request.method=='POST':
      all_questions_with_ans = []
      ques = []
      choc = []
      form_data = request.form.to_dict()
      for each in form_data:
          if each.startswith('question'):
            each_val = each.split('_')
            ques.append(int(each_val[1]))
          elif each.startswith('choice'):
            each_val = each.split('_')
            choc.append((int(each_val[1]),form_data.get(each))) 

      for map_ques in ques:
          for map_ch in choc:
              if map_ques==map_ch[0]:
                all_questions_with_ans.append((map_ques,map_ch[1]))
      if all_questions_with_ans:
        for aqw in all_questions_with_ans:
            ques = Questions.query.filter_by(id=aqw[0]).first()
            if ques:
              choice_id = QuestionsChoices.query.filter_by(question_id=ques.id,choice=aqw[1]).first()
              datatoadd = UserQuestionAnswer(question_id=ques.id,choice_id=choice_id.id,user_id=current_user.id)
              db.session.add(datatoadd)
              db.session.commit()

    return render_template('thanks.html',data=UserQuestionAnswer.query.all())

@app.route('/start_test',methods=['GET', 'POST'])
@login_required
def start_test():
    form = QuizForm()
    print "request=====",request,request.form
    if not current_user.is_admin:
      already_submit = UserQuestionAnswer.query.filter_by(user_id=int(current_user.id)).first()
      print ("already_submit",already_submit)
      if already_submit:
        flash("Sorry!You have already submitted the test.")
        return redirect(url_for('open_login'))
    # for each in Questions.query.all():
    #     form.question = (each.id,each.question)
    #     form.answers.choices = [(probot.id, probot.choice) for probot in each.questions_choices]
    #     return render_template('quiz.html', form=form,questions = Questions.query.all())
    # print "form>>>>>>>>>>data",form

    return render_template('quiz.html', form=form,questions = Questions.query.all(),name=current_user.username)


@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    form = AddQuestionForm()
    print "form.validate_on_submit()",request.method,form.validate(),form.validate_on_submit()
    if request.method=='POST':
        if form.validate()==False:
          flash("All fields are required")
          return render_template('add_questions.html', form=form)
        else:
          ques = Questions.query.filter_by(question=request.form['name']).first()
          if not ques:
            question = Questions(question=request.form['name'],is_active=request.form['is_active'],right_choice=request.form['right_choice'])
            db.session.add(question)
            db.session.commit()

            # print "ques=====",ques
            opt1 = QuestionsChoices(choice= request.form['option1'], main_question=question)
            opt2 = QuestionsChoices(choice= request.form['option2'], main_question=question)
            opt3 = QuestionsChoices(choice= request.form['option3'], main_question=question)
            opt4 = QuestionsChoices(choice= request.form['option4'], main_question=question)
            db.session.add(opt1)
            db.session.add(opt2)
            db.session.add(opt3)
            db.session.add(opt4)
            db.session.commit()
            flash("Questions added sucessfully!")
          return render_template('questions_added.html', form=form,questions =Questions.query.all())



    return render_template('questions_added.html')

@app.route('/all_question')
@login_required
def view_all_question():
    return render_template('questions_added.html',questions =Questions.query.all())

@app.route('/manage_questions')
@login_required
def manage_questions():
    form = AddQuestionForm()
    
  
    return render_template('add_questions.html', form=form)

@app.route('/edit_question/<int:ques_id>',methods=['GET', 'POST'])
def edit_question(ques_id=False):
  form = AddQuestionForm()
  search_result = Questions.query.filter_by(id=int(ques_id)).first()
  all_option = {}
  for each in search_result.questions_choices:
      print "eachhhhhhhhh=",each
      if 'option1' not in all_option:
          all_option.update({'option1':each.choice})
      elif 'option2' not in all_option:
          all_option.update({'option2':each.choice})
      elif 'option3' not in all_option:
          all_option.update({'option3':each.choice})
      elif 'option4' not in all_option:
          all_option.update({'option4':each.choice})
  print ("all_optionnnnn=====",all_option)
  return render_template("edit_question.html",form=form, search_result = search_result, all_options=all_option)

@app.route('/delete_question/<int:ques_id>',methods=['GET', 'POST'])
def delete_question(ques_id=False):
  print ("ques_id========",ques_id)
  search_result = Questions.query.filter_by(id=int(ques_id)).first()
  if search_result:
      message = ""
      message+=str(search_result.question)
      db.session.delete(search_result)
      db.session.commit()
      flash(message+" "+"Deleted Sucessfully.")
      return redirect(url_for('view_all_question'))
  return "Delete User"


if __name__ == '__main__':
  db.create_all()
  app.run(host='0.0.0.0',port=5001,debug=True)
