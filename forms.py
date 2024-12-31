from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('მომხმარებლის სახელი', validators=[DataRequired()])
    password = PasswordField('პაროლი', validators=[DataRequired()])
    submit = SubmitField('შესვლა')

class RegistrationForm(FlaskForm):
    """Form for user registration"""
    username = StringField('მომხმარებლის სახელი', 
                         validators=[
                             DataRequired(message="მომხმარებლის სახელი სავალდებულოა"),
                             Length(min=4, max=20, message="სახელი უნდა იყოს 4-დან 20 სიმბოლომდე")
                         ])
    email = StringField('ელ-ფოსტა', 
                       validators=[
                           DataRequired(message="ელ-ფოსტა სავალდებულოა"),
                           Email(message="გთხოვთ შეიყვანოთ სწორი ელ-ფოსტის მისამართი")
                       ])
    password = PasswordField('პაროლი', 
                           validators=[
                               DataRequired(message="პაროლი სავალდებულოა"),
                               Length(min=6, message="პაროლი უნდა შეიცავდეს მინიმუმ 6 სიმბოლოს")
                           ])
    confirm_password = PasswordField('გაიმეორეთ პაროლი', 
                                   validators=[
                                       DataRequired(message="პაროლის დადასტურება სავალდებულოა"),
                                       EqualTo('password', message="პაროლები არ ემთხვევა")
                                   ])
    submit = SubmitField('რეგისტრაცია')

    def validate_username(self, username):
        if not User.is_valid_username(username.data):
            raise ValidationError('სახელი უნდა შეიცავდეს მხოლოდ ლათინურ ასოებს, ციფრებს და ქვედა ტირეს (_)')
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(f'სახელი "{username.data}" უკვე დაკავებულია. გთხოვთ აირჩიოთ სხვა.')

    def validate_email(self, email):
        if not User.is_valid_email(email.data):
            raise ValidationError('გთხოვთ შეიყვანოთ სწორი ელ-ფოსტის მისამართი')
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(f'ელ-ფოსტა "{email.data}" უკვე დაკავებულია. გთხოვთ აირჩიოთ სხვა.')

    def validate_password(self, password):
        if not User.is_valid_password(password.data):
            raise ValidationError('პაროლი უნდა შეიცავდეს მინიმუმ 6 სიმბოლოს და მინიმუმ 1 ციფრს')

class EducationalMaterialForm(FlaskForm):
    """Form for creating and editing educational materials"""
    title = StringField('მასალის სათაური', 
                       validators=[DataRequired(message="სათაური სავალდებულოა")])
    subject = SelectField('საგანი',
                         choices=[
                             ('math', 'მათემატიკა'),
                             ('physics', 'ფიზიკა'),
                             ('chemistry', 'ქიმია'),
                             ('biology', 'ბიოლოგია'),
                             ('geography', 'გეოგრაფია'),
                             ('history', 'ისტორია'),
                             ('literature', 'ლიტერატურა'),
                             ('english', 'ინგლისური'),
                             ('other', 'სხვა')
                         ])
    grade_level = SelectField('კლასი/დონე',
                            choices=[
                                ('elementary', 'დაწყებითი (1-6 კლასი)'),
                                ('middle', 'საშუალო (7-9 კლასი)'),
                                ('high', 'მაღალი (10-12 კლასი)'),
                                ('university', 'საუნივერსიტეტო'),
                                ('professional', 'პროფესიული'),
                                ('other', 'სხვა')
                            ])
    material_type = SelectField('მასალის ტიპი',
                              choices=[
                                  ('textbook', 'სახელმძღვანელო'),
                                  ('worksheet', 'სავარჯიშოები'),
                                  ('test', 'ტესტები'),
                                  ('presentation', 'პრეზენტაცია'),
                                  ('video', 'ვიდეო მასალა'),
                                  ('other', 'სხვა')
                              ])
    content = TextAreaField('მასალის აღწერა', 
                          validators=[DataRequired(message="აღწერა სავალდებულოა")])
    image = FileField('მასალის სურათი/პრევიუ', 
                     validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'მხოლოდ სურათები!')])
    material_file = FileField('სასწავლო მასალის ფაილი',
                            validators=[FileAllowed(['pdf', 'doc', 'docx', 'ppt', 'pptx', 'zip'], 
                                                  'დაშვებული ფორმატები: PDF, DOC, DOCX, PPT, PPTX, ZIP')])
    submit = SubmitField('მასალის გამოქვეყნება')

class ContactForm(FlaskForm):
    """Form for contact submissions"""
    name = StringField('სახელი', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('ელ-ფოსტა', validators=[DataRequired(), Email()])
    subject = StringField('თემა', validators=[DataRequired(), Length(min=2, max=100)])
    message = TextAreaField('შეტყობინება', validators=[DataRequired(), Length(min=10, max=1000)])
    submit = SubmitField('გაგზავნა')

class CommentForm(FlaskForm):
    content = TextAreaField('კომენტარი', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('დამატება')
