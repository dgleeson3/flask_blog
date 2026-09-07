from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flaskblog.models import UserAccount


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = UserAccount.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = UserAccount.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RequestResetForm(FlaskForm):
    """
    This form is used to request a password reset.
    The user just needs to provide their email address.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class UpdateAccountForm(FlaskForm):
    # Username field (required)
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=20)]
    )

    # Email field (required)
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )

    # Profile picture update (optional)
    picture = FileField(
        'Update Profile Picture',
        validators=[FileAllowed(['jpg', 'png'])]
    )

    # New password (optional)
    password = PasswordField('New Password')

    # Confirm new password (only validates if password is entered)
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[EqualTo('password', message="Passwords must match.")]
    )

    # Submit button
    submit = SubmitField('Update')

    def validate_username(self, username):
        """
        Validate the username only if it is different from the current user's username.
        Checks if the new username already exists in the database.
        """
        if username.data != current_user.username:
            user = UserAccount.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        """
        Validate the email only if it is different from the current user's email.
        Checks if the new email already exists in the database.
        """
        if email.data != current_user.email:
            user = UserAccount.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already in use. Please choose a different one.')


class PostForm(FlaskForm):
    title = StringField('Site Name(Site Owner)', validators=[DataRequired()])
    content = TextAreaField('Site Owner Contact Details', validators=[DataRequired()])
    submit = SubmitField('Add a New Site')


class PostForm_Update(FlaskForm):
    title = StringField('Site Name(Site Owner)', validators=[DataRequired()])
    content = TextAreaField('Product at Site', validators=[DataRequired()])
    submit = SubmitField('Update')



class ShowSitesForm(FlaskForm):
#    title = StringField('Site Name(Site Owner)', validators=[DataRequired()])
#    content = TextAreaField('Product at Site', validators=[DataRequired()])
    submit = SubmitField('Add a New Site')

class ShowDevicesForm(FlaskForm):
#    title = StringField('Site Name(Site Owner)', validators=[DataRequired()])
#    content = TextAreaField('Product at Site', validators=[DataRequired()])
    submit = SubmitField('Add a New Device')


class AddDevice(FlaskForm):
#    title = StringField('Site Name(Site Owner)', validators=[DataRequired()])
#    content = TextAreaField('Product at Site', validators=[DataRequired()])
#    option = RadioField(choices=[('dog', 'Dog'), ('cat', 'Cat'), ('bird', 'Bird'), ('alien', 'Alien')])
    submit = SubmitField('Add this Device to Site')    
