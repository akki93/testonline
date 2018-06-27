from flask_wtf import FlaskForm
from wtforms import IntegerField,StringField, BooleanField, PasswordField, SubmitField, RadioField, SelectField
from wtforms.validators import InputRequired, Email, Length
from wtforms.fields.html5 import DateField
import datetime


class LoginForm(FlaskForm):

    username = StringField("UserName",validators=[InputRequired("Please enter user name."), Length(min=4, max=15)])
    password = PasswordField("Password",validators=[InputRequired("Please enter password."),Length(min=4, max=20)])
    remember = BooleanField("Remember me")
    subject_id = SelectField('Select Subject',validators=[InputRequired("Please select subject.") ],choices=[], coerce=int)

class RegisterForm(FlaskForm):

    username = StringField("UserName",validators=[InputRequired("Please enter user name."), Length(min=4, max=15)])
    password = PasswordField("Password",validators=[InputRequired("Please enter password."),Length(min=4, max=20)])
    email = StringField("Email", validators= [InputRequired(message="Invalid Email"),Email("Email format is wrong"), Length(max=80)])


class PasswordResetForm(FlaskForm):

    new_password = PasswordField("New Password",validators=[InputRequired("Please enter new password"), Length(min=4, max=20)])
    confirm_password = PasswordField("Confirm Password",validators=[InputRequired("Please confirm password."),Length(min=4, max=20)])
    email = StringField("Email", validators= [InputRequired(message="Invalid Email"),Email("Email format is wrong"), Length(max=80)])


class AddQuestionForm(FlaskForm):

    name = StringField("Question",validators=[InputRequired("Question can not be blank."), Length(min=1, max=1500)])
    option1 = StringField("Option 1",validators=[InputRequired("Please enter option1."),Length(min=1, max=200)])
    option2 = StringField("Option 2",validators=[InputRequired("Please enter option2."),Length(min=1, max=200)])
    option3 = StringField("Option 3",validators=[InputRequired("Please enter option3."),Length(min=1, max=200)])
    option4 = StringField("Option 4",validators=[InputRequired("Please enter option4."),Length(min=1, max=200)])
    is_active = BooleanField("Is Active", default=True)
    right_choice = SelectField('Right Choice', choices=[('option1', 'Option1'), ('option2', 'Option2'),('option3', 'Option3'),('option4', 'Option4')])
    exam_id = SelectField('Select Subject', choices=[], coerce=int)
    save_data = SubmitField("Save Question")

class QuizForm(FlaskForm):

    question = StringField("Question")
    answers = RadioField('Label', choices=[])