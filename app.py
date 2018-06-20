from flask import Flask, render_template, request, flash, redirect, url_for, session, Response
from forms import LoginForm, RegisterForm, PasswordResetForm, AddQuestionForm, QuizForm
from flask_sqlalchemy import SQLAlchemy
import datetime

# adding password security using werkzug
from werkzeug.security import generate_password_hash, check_password_hash

# adding flask login to resrict user to do first sign in
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

import operator

# for exporting data to a  report
import xlsxwriter

from cStringIO import StringIO
# from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from sqlalchemy import create_engine

app = Flask(__name__, template_folder='../testonline/templates')

app.config["SECRET_KEY"] = "Thisisascretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://arpit:honey@localhost/testonline'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'open_login'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column('id', db.Integer, db.Sequence('user_id_seq', start=1), primary_key=True, )
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

class Exams(db.Model):
    # __tablename__ = 'questions'
    # __searchable__=['title','content']

    id = db.Column('id', db.Integer, db.Sequence('exam_id_seq', start=1), primary_key=True)
    exam = db.Column(db.Text())
    

class Questions(db.Model):
    # __tablename__ = 'questions'
    # __searchable__=['title','content']

    id = db.Column('id', db.Integer, db.Sequence('question_id_seq', start=1), primary_key=True)
    question = db.Column(db.Text())
    is_active = db.Column(db.Boolean, unique=False, default=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    questions_choices = db.relationship('QuestionsChoices', backref='main_question', cascade="all,delete", lazy=True)
    right_choice = db.Column(db.String)


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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/sign_in", methods=["GET", "POST"])
def open_login():
    form = LoginForm()
    if form.validate_on_submit():
        # return '<h1>'+form.username.data +' ' +form.password.data+ '</h1>'
        user = User.query.filter_by(username=form.username.data).first()
        try:
            if user.is_admin:
                if check_password_hash(user.password, form.password.data):
                    login_user(user, remember=form.remember.data)
                    return redirect(url_for('control_center'))
                else:
                    flash("Password does not match. Forgot Password ?")
            elif user:
                if check_password_hash(user.password, form.password.data):
                    login_user(user, remember=form.remember.data)
                    return redirect(url_for('index'))
                else:
                    flash("Password does not match.Forgot password ?")
            else:
                flash("User does not exist ! Please Create account.")

        except Exception as e:
            flash("User does not exist ! Please Create account.")

    return render_template("login_activity.html", form=form)
    # return render_template("login_activity.html")


@app.route("/create_account", methods=["GET", "POST"])
def create_login():
    form = RegisterForm()
    if form.validate_on_submit():
        hash_password = generate_password_hash(form.password.data, method='sha256')
        try:
            new_user = User(username=form.username.data, email=form.email.data, password=hash_password, is_admin=False)
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


@app.route("/password_reset", methods=["GET", "POST"])
def forgot_password():
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        try:
            if user:
                # when both password are same
                if form.new_password.data == form.confirm_password.data:
                    hash_password = generate_password_hash(form.confirm_password.data, method='sha256')
                    user.password = hash_password
                    db.session.commit()
                    flash("Password reset sucessfully!.")
                    # return '<h1>'+ 'Password is reset' +'</h1>'
                else:
                    flash("Password not match!.")
        except Exception as e:
            flash("There is no user for this Email.")

    return render_template("forgot_password.html", form=form)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit_test', methods=['GET', 'POST'])
def submit_test():
    if request.method == 'POST':
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
                choc.append((int(each_val[1]), form_data.get(each)))

        for map_ques in ques:
            for map_ch in choc:
                if map_ques == map_ch[0]:
                    all_questions_with_ans.append((map_ques, map_ch[1]))
        question_count = len(ques)
        marks = 0
        correct_ans = 0

        if all_questions_with_ans:
            for aqw in all_questions_with_ans:
                ques = Questions.query.filter_by(id=aqw[0]).first()
                if ques:
                    choice_id = QuestionsChoices.query.filter_by(question_id=ques.id, choice=aqw[1]).first()
                    datatoadd = UserQuestionAnswer(question_id=ques.id, choice_id=choice_id.id, user_id=current_user.id)
                    db.session.add(datatoadd)
                    db.session.commit()

        curr_user_submit = UserQuestionAnswer.query.filter_by(user_id=current_user.id).all()

        for each_quest in curr_user_submit:
            correct_ans_id = QuestionsChoices.query.filter_by(question_id=each_quest.question_id, is_right=True).first()
            choice_id = QuestionsChoices.query.filter_by(question_id=correct_ans_id.question_id,
                                                         choice=correct_ans_id.choice).first()
            if each_quest and each_quest.choice_id == choice_id.id:
                correct_ans += 1
        incorrect_answers = question_count - correct_ans
        user_percentage = ((correct_ans * 100) / float(question_count))
        user_percentage = format(user_percentage, '.2f')
        user_marks_report = UserMarksReport(uid=current_user.id, marks=correct_ans, percentage=float(user_percentage))
        db.session.add(user_marks_report)
        db.session.commit()
    return render_template('thanks.html', name=current_user, **locals())


@app.route('/start_test', methods=['GET', 'POST'])
@login_required
def start_test():
    form = QuizForm()
    print "request=====", request, request.form
    if not current_user.is_admin:
        already_submit = UserQuestionAnswer.query.filter_by(user_id=int(current_user.id)).first()
        print ("already_submit", already_submit)
        if already_submit:
            flash("Sorry!You have already submitted the test.")
            return redirect(url_for('open_login'))
    # for each in Questions.query.all():
    #     form.question = (each.id,each.question)
    #     form.answers.choices = [(probot.id, probot.choice) for probot in each.questions_choices]
    #     return render_template('quiz.html', form=form,questions = Questions.query.all())
    # print "form>>>>>>>>>>data",form

    return render_template('quiz.html', form=form, questions=Questions.query.all(), name=current_user.username)


@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    form = AddQuestionForm()
    print "form.validate_on_submit()", request.method, form.validate(), form.validate_on_submit()
    if request.method == 'POST':
        if form.validate() == False:
            flash("All fields are required")
            return render_template('add_questions.html', form=form)
        else:
            ques = Questions.query.filter_by(question=request.form['name']).first()
            if not ques:
                print "request.form['right_choice']>>>>>>>", request.form['right_choice']
                question = Questions(question=request.form['name'], is_active=request.form['is_active'],
                                     right_choice=request.form['right_choice'])
                db.session.add(question)
                db.session.commit()
                option1 = False
                option2 = False
                option3 = False
                option4 = False
                if str(request.form['right_choice']) == 'option1':
                    option1 = True
                elif str(request.form['right_choice']) == 'option2':
                    option2 = True
                elif str(request.form['right_choice']) == 'option3':
                    option3 = True
                elif str(request.form['right_choice']) == 'option4':
                    option4 = True

                opt1 = QuestionsChoices(choice=request.form['option1'], is_right=option1,main_question=question)
                opt2 = QuestionsChoices(choice=request.form['option2'], is_right=option2, main_question=question)
                opt3 = QuestionsChoices(choice=request.form['option3'], is_right=option3, main_question=question)
                opt4 = QuestionsChoices(choice=request.form['option4'], is_right=option4, main_question=question)
                db.session.add(opt1)
                db.session.add(opt2)
                db.session.add(opt3)
                db.session.add(opt4)
                db.session.commit()
                flash("Questions added sucessfully!")
            return render_template('questions_added.html', form=form, questions=Questions.query.all())

    return render_template('questions_added.html')


@app.route('/all_question')
@login_required
def view_all_question():
    return render_template('questions_added.html', questions=Questions.query.all())


@app.route('/all_users')
@login_required
def view_all_users():
    if current_user.is_admin:
        return render_template('all_users.html', users=User.query.all())
    else:
        flash("You are not an admin user. Hence you cannot view this page!!")
        return redirect(url_for('index'))


@app.route('/control-center')
@login_required
def control_center():
    if current_user.is_admin:
        return render_template('control-center.html')
    else:
        flash('Please log-in with Administrator account to view the control panel')
        return redirect(url_for('index'))


@app.route('/control-center/export')
@login_required
def export():
    if current_user.is_admin:
        return render_template('export-data.html')
    else:
        flash('Please log-in with Administrator account to view the control panel')
        return redirect(url_for('index'))


@app.route('/control-center/export-data', methods=['GET', 'POST'])
@login_required
def export_data():
    engine = create_engine('postgresql+psycopg2://arpit:honey@localhost/testonline')
    cur = engine.connect()
    all_questions = cur.execute("select question from questions")
    all_answers = cur.execute("select choice from questions_choices where is_right = true")
    quest_set = []
    ans_set = []
    for each_quest in all_questions:
        quest_set.append(each_quest[0])
    for each_ans in all_answers:
        ans_set.append(each_ans[0])
    quest_ans_set = zip(quest_set, ans_set)
    if current_user.is_admin and request.form['selected_report_type'] == 'XLS':
        file_data = StringIO()
        workbook = xlsxwriter.Workbook(file_data)
        worksheet = workbook.add_worksheet('Data')
        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({'bold': True})
        worksheet.write('A1', 'Question', bold)
        # Start from the first cell. Rows and columns are zero indexed.
        row = 1
        col = 0
        for each_q_ans in quest_ans_set:
            worksheet.write(row, col, each_q_ans[0])
            row += 1
            worksheet.write(row, col, 'Ans: ' + each_q_ans[1])
            row += 1
        workbook.close()
        file_data.seek(0)
        return Response(
            file_data.read(),
            mimetype="application/excel",
            headers={"Content-disposition": "attachment; filename=Question Report.xls"})

    # elif current_user.is_admin and request.form['selected_report_type'] == 'DOC':
    #     file_data = StringIO()
    #     document = Document()
    #     document.add_heading('Question Set', level=1)
    #     document.add_paragraph([str(ques_ans[0]) + '\n' + 'Ans: ' + str(ques_ans[1]) +
    #                             '\n' for ques_ans in quest_ans_set])
    #     document.save(file_data)
    #     file_data.seek(0)
    #     return Response(
    #         file_data.read(),
    #         mimetype="application/doc",
    #         headers={"Content-disposition": "attachment; filename=Question Report.doc"})

    elif current_user.is_admin and request.form['selected_report_type'] == 'PDF':
        file_data = StringIO()
        p = canvas.Canvas(file_data, pagesize=A4)
        p.setFont('Helvetica', 14)
        p.drawString(250, 800, "Question Set")
        x = 60
        y = 760
        n = 1
        for each_quest_ans in quest_ans_set:
            p.drawString(x, y, str('Q.%s  ' % n) + str(each_quest_ans[0]))
            n += 1
            y -= 20
            p.drawString(x, y, 'Ans: ' + str(each_quest_ans[1]))
            y -= 30
        p.showPage()
        p.save()
        file_data.seek(0)
        return Response(
            file_data.read(),
            mimetype="application/pdf",
            headers={"Content-disposition": "attachment; filename=Question Report.pdf"})

    else:
        flash('Please log-in with Administrator account to view the control panel')
        return redirect(url_for('index'))


@app.route('/control-center/dashboard')
@login_required
def view_dashboard():
    if current_user.is_admin:
        engine = create_engine('postgresql+psycopg2://arpit:honey@localhost/testonline')
        cur = engine.connect()
        user_marks_details = cur.execute("select username, marks, percentage from user_marks_report, users where id=uid")
        count_users_query = cur.execute("select count(id) from users")
        for each_user in count_users_query:
            count_users = each_user[0]
        passing_users_query = cur.execute("select count(uid) from user_marks_report where percentage > 60.00")
        for each_passing_user in passing_users_query:
            passing_users = each_passing_user[0]
        failing_users_query = cur.execute("select count(uid) from user_marks_report where percentage < 60.00")
        for each_failing_user in failing_users_query:
            failing_users = each_failing_user[0]
        return render_template('dashboard.html', **locals())
    else:
        flash("You need to log-in with Administrator to view dashboard")


@app.route('/manage_questions')
@login_required
def manage_questions():
    form = AddQuestionForm()

    return render_template('add_questions.html', form=form)


@app.route('/edited_question', methods=['GET', 'POST'])
@app.route('/edit_question/<int:ques_id>', methods=['GET', 'POST'])
def edit_question(ques_id=False):
    engine = create_engine('postgresql+psycopg2://arpit:honey@localhost/testonline')

    # print engine
    cnx = engine.connect()
    # x = cnx.execute("select name,count(id) from contact group by name")
    # cnx.close()
    # calling update request=== POST 3 {'csrf_token': u'ImY3NDY3MDJkMzQyNWEwM2I0MmNiOTJlYzE5MGRmNGUxMGU3ODc5NDEi.Db3UTA.GOe-w_VNPaEPSX72uXP2rR6bZyQ', 
    # 'name': u'what is your favourate color', 'save_data': u'Save Question', 'option4': u'pink', 
    # 'option2': u'greeen', 'option3': u'blue', 'option1': u'red'}
    form = AddQuestionForm()
    search_result = Questions.query.filter_by(id=int(ques_id)).first()
    all_option = {}
    for each in search_result.questions_choices:
        print "eachhhhhhhhh=", each
        if 'option1' not in all_option:
            all_option.update({'option1': each.choice})
        elif 'option2' not in all_option:
            all_option.update({'option2': each.choice})
        elif 'option3' not in all_option:
            all_option.update({'option3': each.choice})
        elif 'option4' not in all_option:
            all_option.update({'option4': each.choice})
    print ("all_optionnnnn=====", all_option)
    if request.method=='POST':
        print "calling update request===",request.method,ques_id,request.form.to_dict()
        form_data = request.form.to_dict()
        search_result.question = form_data.get('name')
        search_result.right_choice = form_data.get('right_choice')
        user_ans = UserQuestionAnswer.query.filter_by(user_id=current_user.id,question_id=int(ques_id)).all()
        print "user_ans=====",user_ans
        for each in user_ans:
            cnx.execute("delete from user_question_answer where id =%s",(each.id))
        cnx.close()
        choices = QuestionsChoices.query.filter_by(question_id=int(ques_id)).all()
        print "choices=======",choices
        for each in choices:
            db.session.delete(each)
        db.session.commit()
        #for updating the options
        option1 = False
        option2 = False
        option3 = False
        option4 = False
        if str(form_data.get('right_choice')) == 'option1':
            option1 = True
        elif str(form_data.get('right_choice')) == 'option2':
            option2 = True
        elif str(form_data.get('right_choice')) == 'option3':
            option3 = True
        elif str(form_data.get('right_choice')) == 'option4':
            option4 = True
        opt1 = QuestionsChoices(choice=str(form_data.get('option1')), is_right=option1,main_question=search_result)
        opt2 = QuestionsChoices(choice=str(form_data.get('option2')), is_right=option2, main_question=search_result)
        opt3 = QuestionsChoices(choice=str(form_data.get('option3')), is_right=option3, main_question=search_result)
        opt4 = QuestionsChoices(choice=str(form_data.get('option4')), is_right=option4, main_question=search_result)
        db.session.add(opt1)
        db.session.add(opt2)
        db.session.add(opt3)
        db.session.add(opt4)

        db.session.commit()
        return redirect(url_for('view_all_question'))
        
    return render_template("edit_question.html", form=form, search_result=search_result, all_options=all_option)


@app.route('/delete_question/<int:ques_id>', methods=['GET', 'POST'])
def delete_question(ques_id=False):
    print ("ques_id========", ques_id)
    #first need to remove child table data
    # user_ans=False
    # choices = False
    # user_ans = UserQuestionAnswer.query.filter_by(user_id=current_user.id,question_id=int(ques_id)).all()
    # if user_ans:
    #     choices = QuestionsChoices.query.filter_by(question_id=int(ques_id)).all()
    search_result = Questions.query.filter_by(id=int(ques_id)).first()
    if search_result:
        message = ""
        message += str(search_result.question)
        # db.session.delete(user_ans) if user_ans else True
        # db.session.delete(choices)  if choices  else True
        db.session.delete(search_result)
        db.session.commit()
        flash(message + " " + "Deleted Sucessfully.")
        return redirect(url_for('view_all_question'))
    return "Delete User"


if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
