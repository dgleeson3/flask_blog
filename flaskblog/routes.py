import os
import secrets
import re
import pandas as pd
from PIL import Image
from flask import (render_template, url_for, flash, redirect, request, abort,
                   jsonify, current_app, send_file)
from flaskblog import app, db, bcrypt
from flaskblog.forms import (
    RegistrationForm, LoginForm, UpdateAccountForm, PostForm,
    PostForm_Update, ShowSitesForm, AddDevice, ShowDevicesForm, RequestResetForm
)
from flaskblog.models import (
    UserAccount, Post, Site, PhoneNumber, OutOfHour,
    KeypadCode, Device, CallOutPhoneNumber, AutomaticSchedule, LiveDiagnostics, CurrentDiagnostics
)
from flask_login import login_user, current_user, logout_user, login_required
from io import BytesIO
from datetime import datetime

from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.orm.attributes import flag_modified
# -----------------------------------------------------------------------------
# Function: my_function
# Description: This helper function prints a debug message and redirects the user to the home route.
# -----------------------------------------------------------------------------
def my_function():
    print("my_function called - redirect")  # Debug: Notifies that my_function was called.
    return redirect(url_for('home'))         # Redirects the client to the 'home' route.


# -----------------------------------------------------------------------------
# Route: Home Page
# Description: This route handles both "/" and "/home" URL patterns for GET and POST methods.
#              - If the user is authenticated, they are redirected to 'showsites'.
#              - If not authenticated, the login form is displayed.
# -----------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    # If the user is already logged in, redirect them to the 'showsites' page.
    if current_user.is_authenticated:
        return redirect(url_for('showsites'))
    
    # Instantiate the login form.
    form = LoginForm()
    
    # Process form submission.
    if form.validate_on_submit():
        # Query the database for a user with the provided email address.
        user = UserAccount.query.filter_by(email=form.email.data).first()
        # If a user is found and the provided password matches the stored hash:
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)  # Log the user in.
            next_page = request.args.get('next')  # Retrieve 'next' parameter if it exists.
            # Redirect to the next page if set, otherwise go to 'showsites'.
            return redirect(next_page) if next_page else redirect(url_for('showsites'))
        else:
            # If authentication fails, flash a danger message for the user.
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    # Render the login template with the form.
    return render_template('login.html', title='Login', form=form)


# -----------------------------------------------------------------------------
# Route: About Page
# Description: Renders the "About" page. This page is likely static.
# -----------------------------------------------------------------------------
@app.route("/about")
def about():
    return render_template('about.html', title='About')


# -----------------------------------------------------------------------------
# Route: Register
# Description: Handles the user registration process. If a user is logged in, they are 
#              redirected to the home page.
# -----------------------------------------------------------------------------
@app.route("/register", methods=['GET', 'POST'])
def register():
    # Redirect authenticated users away from registration page.
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Encrypt the password using bcrypt.
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Special condition for administrator assignment based on username
        if 'x2450cc28' in form.username.data:
            user = UserAccount(username=form.username.data,
                               email=form.email.data,
                               password=hashed_password, administrator=1)
        else:
            user = UserAccount(username=form.username.data,
                               email=form.email.data,
                               password=hashed_password)
        db.session.add(user)    # Add the new user to the session.
        db.session.commit()     # Commit the session to save the user in the database.
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    
    # Render the registration template with the form.
    return render_template('register.html', title='Register', form=form)


# -----------------------------------------------------------------------------
# Route: Login
# Description: Handles the login process. If the user is already authenticated, they 
#              are redirected to 'showsites'. Upon a successful login, the user is also 
#              redirected to 'showsites' or their intended next page.
# -----------------------------------------------------------------------------
@app.route("/login", methods=['GET', 'POST'])
def login():
    # Prevent logged-in users from accessing the login page.
    if current_user.is_authenticated:
        return redirect(url_for('showsites'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Retrieve the user from the database matching the provided email.
        user = UserAccount.query.filter_by(email=form.email.data).first()
        # Validate user existence and password.
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)  # Log the user in.
            next_page = request.args.get('next')
            # Redirect to next page if provided; otherwise, go to 'showsites'.
            return redirect(next_page) if next_page else redirect(url_for('showsites'))
        else:
            # Inform the user of an unsuccessful login attempt.
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    # Render the login page with the login form.
    return render_template('login.html', title='Login', form=form)


# -----------------------------------------------------------------------------
# Route: Logout
# Description: Logs out the current user and then redirects them to the login page.
# -----------------------------------------------------------------------------
@app.route("/logout")
def logout():
    logout_user()  # Log out the current user.
    return redirect(url_for('login'))  # Redirect to the login page.


# -----------------------------------------------------------------------------
# Function: save_picture
# Description: Processes an uploaded image:
#              - Generates a random filename.
#              - Resizes the image to the specified output size.
#              - Saves the image to the defined path.
# Returns:
#              - The filename of the saved picture.
# -----------------------------------------------------------------------------
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)  # Generate a random 8-byte hex token.
    _, f_ext = os.path.splitext(form_picture.filename)  # Retrieve the file extension.
    picture_fn = random_hex + f_ext  # Combine token with file extension.
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    
    # Set the desired output dimensions.
    output_size = (125, 125)
    i = Image.open(form_picture)  # Open the image.
    i.thumbnail(output_size)      # Resize while maintaining aspect ratio.
    i.save(picture_path)          # Save the resized image to disk.
    return picture_fn             # Return the new filename.


# -----------------------------------------------------------------------------
# Route: Account
# Description: Displays and updates the account settings for the current user.
#              Supports:
#              - Profile picture update.
#              - Changing username, email, and password.
# -----------------------------------------------------------------------------
@app.route("/account", methods=['GET', 'POST'])
@login_required  # Ensures the user is logged in before accessing this route.
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        # If a new profile picture is uploaded, save it.
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            # Uncomment the line below to update the current user's image file.
            # current_user.image_file = picture_file

        # Update the user's username and email.
        current_user.username = form.username.data
        current_user.email = form.email.data

        # If the user provided a new password, hash it before storing.
        if form.password.data:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            current_user.password = hashed_password

        db.session.commit()  # Save all changes to the database.
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))

    elif request.method == 'GET':
        # Pre-fill the form fields with the current user's existing data.
        form.username.data = current_user.username
        form.email.data = current_user.email

    # Render the account page with the update form.
    return render_template('account.html', title='Account', form=form)


# -----------------------------------------------------------------------------
# Function: sending_email
# Description: Sends an HTML email using the SMTP protocol.
#              The sender uses a hardcoded Gmail account and password.
# Parameters:
#              - receiver_email: The recipient's email address.
#              - subject: Subject line for the email.
#              - body: HTML content of the email.
# -----------------------------------------------------------------------------
def sending_email(receiver_email, subject, body):
    sender_email = "newsongaboutcrazy@gmail.com"
    # Hardcoded Gmail application password (not recommended for production use)
    password = ""
    
    # Create a multipart email message.
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))
    
    try:
        # Connect to Gmail's SMTP server using TLS encryption.
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Start TLS encryption.
        server.login(sender_email, password)  # Log into the SMTP server.
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()  # Disconnect from the server.
        print("Email Sent Successfully")
    except Exception as e:
        # Output the exception if email sending fails.
        print(f"Failed to send email: {e}")


# -----------------------------------------------------------------------------
# Function: send_reset_email
# Description: Generates a secure token for a user to reset their password and sends an
#              email with a reset link that includes this token.
# Parameters:
#              - user: The user object for whom the reset email is sent.
# -----------------------------------------------------------------------------
def send_reset_email(user):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = s.dumps(user.email, salt='password-reset-salt')
    # Generate a reset URL which includes the token as a parameter.
    reset_url = url_for('reset_with_token', token=token, _external=True)
    subject = "Password Reset Request"
    body = f"""
    <p>To reset your password, visit the following link:</p>
    <p><a href="{reset_url}">{reset_url}</a></p>
    <p>If you did not request a password reset, please ignore this email.</p>
    """
    # Call the function to send the email.
    sending_email(user.email, subject, body)
# -----------------------------------------------------------------------------
# Route: /forgot_password
# Description: Displays a form for requesting a password reset.
#              If an account with the provided email exists, sends a reset
#              email with instructions and then redirects the user to the login page.
# -----------------------------------------------------------------------------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = RequestResetForm()  # Instantiate the password reset request form.
    if form.validate_on_submit():
        # Look up the user by the email entered in the form.
        user = UserAccount.query.filter_by(email=form.email.data).first()
        if user:
            # If a valid user is found, send a password reset email.
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))  # Redirect to the login page.
        else:
            # Notify the user if no account exists with the entered email.
            flash('No account found with that email address.', 'warning')
    # Render the forgot password template with the request form.
    return render_template('forgot_password.html', form=form)


# -----------------------------------------------------------------------------
# Route: /reset/<token>
# Description: Displays a form for the user to enter a new password.
#              The token in the URL is used to verify the user's identity.
# -----------------------------------------------------------------------------
@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        # Attempt to deserialize the token to retrieve the email.
        # The token is valid for 1 hour.
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        # If token has expired, notify the user and redirect to the forgot password page.
        flash("The reset link has expired.", "danger")
        return redirect(url_for('forgot_password'))
    except BadSignature:
        # If token is invalid, inform the user and redirect.
        flash("The reset link is invalid.", "danger")
        return redirect(url_for('forgot_password'))
    
    # Retrieve the user associated with the email from the token.
    user = UserAccount.query.filter_by(email=email).first()
    if not user:
        flash("No account found for this email.", "warning")
        return redirect(url_for('forgot_password'))
    
    if request.method == "POST":
        # Retrieve the new password and its confirmation from the form.
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        # Validate that both password fields are provided and match.
        if not password or not confirm_password or password != confirm_password:
            flash("Passwords do not match or are missing.", "danger")
            return redirect(url_for('reset_with_token', token=token))
        
        # Encrypt the new password using Flask-Bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user.password = hashed_password  # Update the user's password.
        db.session.commit()  # Commit changes to the database.
        flash("Your password has been successfully reset.", "success")
        return redirect(url_for('login'))
    
    # Render the reset password template, passing in the token for verification.
    return render_template('reset_with_token.html', token=token)


# -----------------------------------------------------------------------------
# Route: New Site
# Description: Allows a logged in user to create a new site.
#              The form collects the site name and contact details.
# -----------------------------------------------------------------------------
@app.route("/site/new", methods=['GET', 'POST'])
@login_required
def new_site():
    form = PostForm()  # The form used for site creation.
    if form.validate_on_submit():
        # Create a new Site object using the form data.
        site = Site(user_id=current_user.id,
                    site_name=form.title.data,
                    site_contact_details=form.content.data)
        db.session.add(site)  # Add the new site to the session.
        db.session.commit()   # Save the new site in the database.
        flash('Your new site has been created!', 'success')
        return redirect(url_for('home'))
    # Render the template for site creation with the form.
    return render_template('create_site.html', title='Add New Site', form=form, legend='Add New Site')


# -----------------------------------------------------------------------------
# Route: Delete Site
# Description: Allows a logged in user to delete a site.
#              Checks that the site belongs to the current user before deletion.
# -----------------------------------------------------------------------------
@app.route("/site/<int:site_id>/delete", methods=['POST'])
@login_required
def delete_site(site_id):
    site = Site.query.get_or_404(site_id)  # Retrieve site or return 404 if not found.
    # Verify that the site belongs to the current user.
    if site.user_id != current_user.id:
        flash("You are not authorized to delete this site.", "danger")
        return redirect(url_for('home'))
    
    db.session.delete(site)  # Delete the site.
    db.session.commit()      # Commit the deletion.
    
    flash("The site has been successfully deleted.", "success")
    return redirect(url_for('home'))


# -----------------------------------------------------------------------------
# Route: View Post
# Description: Displays a single post identified by post_id.
# -----------------------------------------------------------------------------
@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)  # Retrieve the post or show 404 if not found.
    return render_template('post.html', title=post.title, post=post)


# -----------------------------------------------------------------------------
# Route: Update Post
# Description: Allows a logged in user to update an existing post.
#              Only the owner of the post is allowed to update it.
# -----------------------------------------------------------------------------
@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Check if the current user is the owner of the post.
    if post.user_id != current_user:
        abort(403)  # Return a Forbidden error if not authorized.
    form = PostForm_Update()  # Form for updating the post.
    if form.validate_on_submit():
        post.title = form.title.data  # Update title.
        post.content = form.content.data  # Update content.
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        # Pre-fill the form with the existing post data.
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')


# -----------------------------------------------------------------------------
# Route: Delete Post
# Description: Allows a logged in user to delete a specific post.
# -----------------------------------------------------------------------------
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    try:
        db.session.delete(post)  # Attempt to delete the post.
        db.session.commit()
        flash('Your post has been deleted!', 'success')
    except:
        # If deletion fails, return an error message.
        return 'There was an issue deleting your post'
    return redirect(url_for('home'))


# -----------------------------------------------------------------------------
# Route: Show Sites
# Description: Displays all sites that belong to the current user.
# -----------------------------------------------------------------------------
@app.route("/showsites", methods=['GET', 'POST'])
@login_required
def showsites():
    form = ShowSitesForm()  # Form for filtering or interacting with sites.
    sites = Site.query.filter_by(user_id=current_user.id)  # Retrieve current user's sites.
    return render_template('showsites.html', sites=sites, form=form)


# -----------------------------------------------------------------------------
# Route: Add Device
# Description: Adds a new device to a given site.
#              Gathers device details from the form and sets defaults based on device type.
# -----------------------------------------------------------------------------
@app.route("/adddevice/<int:site_id>", methods=['GET', 'POST'])
@login_required
def add_device(site_id):
    if request.method == 'POST':
        # Retrieve device details from form data.
        phone_number = request.form['SIM_Phone_Number']
        name = request.form['Local_Name']
        device_type_name = request.form['radio_option']
        # Set the default image link based on device type.
        img_link = "../static/profile_pics/voyager-voice.png" if "Voyager Voice" in device_type_name else "../static/profile_pics/switch4G_portfolio.png"
        
        # Create a Device instance with different attributes depending on its type.
        if device_type_name == "Voyager Voice 2 button Intercom":
            device = Device(
                device_type_name=device_type_name,
                site_id=site_id,
                device_sim_number=phone_number,
                access_point_name=name,
                photo_url=img_link,
                number_button=2
            )
        elif device_type_name == "Voyager Voice 4 button Intercom":
            device = Device(
                device_type_name=device_type_name,
                site_id=site_id,
                device_sim_number=phone_number,
                access_point_name=name,
                photo_url=img_link,
                number_button=4
            )
        elif device_type_name == "Voyager Voice Appartment Intercom":
            device = Device(
                device_type_name=device_type_name,
                site_id=site_id,
                device_sim_number=phone_number,
                access_point_name=name,
                photo_url=img_link,
                number_apartment=50
            )
        else:
            # For any other device types, use the default settings.
            device = Device(
                device_type_name=device_type_name,
                site_id=site_id,
                device_sim_number=phone_number,
                access_point_name=name,
                photo_url=img_link
            )
        try:
            db.session.add(device)  # Add the new device to the session.
            db.session.commit()       # Save to the database.
            return redirect(url_for('show_device', site_id=site_id))
        except Exception as e:
            # If an error occurs, optionally log the error and redirect.
            return redirect(url_for('show_device', site_id=site_id))
    else:
        # For GET requests, render the device creation form.
        return render_template('adddevice.html', site_id=site_id)
    

# -----------------------------------------------------------------------------
# Route: Delete Device Settings 
# Description: Deletes a device, ensuring that the device belongs to the logged-in user.
# -----------------------------------------------------------------------------
@app.route("/deletedevice/<int:device_id>", methods=['POST'])
@login_required
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)  # Retrieve the device or 404 if not found.
    # Check whether the device's site belongs to the current user.
    if device.site.user_id != current_user.id:
        flash("You are not authorized to delete this device.", "danger")
        return redirect(url_for('home'))
    
    db.session.delete(device)  # Delete the device.
    db.session.commit()        # Commit changes.
    
    flash("The device has been successfully deleted.", "success")
    return redirect(url_for('show_device', site_id=device.site_id))


# -----------------------------------------------------------------------------
# Route: Device Settings (Placeholder)
# Description: Renders a placeholder page for device settings.
# -----------------------------------------------------------------------------
@app.route('/devicesettings_id', methods=['GET', 'POST'])
@login_required
def device_settings_id():
    return render_template('devicesettings_id.html')


# -----------------------------------------------------------------------------
# Function: max_call_outs_for_device
# Description: Calculates the maximum number of call-out contacts allowed for a device.
#              - For multi-button devices: maximum contacts equal number of buttons * 3.
#              - For other devices: default to 5 contacts.
# -----------------------------------------------------------------------------
def max_call_outs_for_device(device_info):
    if device_info.device_type_name in ["Voyager Voice 2 button Intercom", "Voyager Voice 4 button Intercom"]:
        return device_info.number_button * 3
    else:
        return 5


# -----------------------------------------------------------------------------
# Function: serialize_call_out
# Description: Serializes a call-out contact record into a dictionary format for APIs or JSON responses.
# -----------------------------------------------------------------------------
def serialize_call_out(call_out):
    return {
        "id": call_out.id,
        "device_id": call_out.device_id,
        "phone_number": call_out.phone_number,
        "user_name": call_out.user_name,
        "order": call_out.order,
        "button_device": call_out.button_device,
        "apartment_device": call_out.apartment_device
    }

# -------------------------------------------------------------------------
# 1. Route: Update Keypad Code
# Description: This route handles the update of a keypad code for a specific device.
#              It retrieves the keypad code from the form submission and updates
#              the database with a new KeypadCode entry.
@app.route('/devicesettings/<int:device_id>/update_keypad', methods=['POST'])
@login_required
def update_keypad(device_id):
    # Retrieve the submitted keypad code from the form data.
    keypad_code = request.form.get('keypadCode')
    if keypad_code:
        # Create a new KeypadCode entry with the provided device ID and keypad code.
        keypad_entry = KeypadCode(device_id=device_id, key_code=keypad_code)
        try:
            # Attempt to add the new keypad code to the session and commit to the database.
            db.session.add(keypad_entry)
            db.session.commit()
            flash('Keypad code updated successfully!', 'success')
        except Exception as e:
            # If an error occurs, display an error message.
            flash('Failed to update keypad code.', 'danger')
    # Redirect back to the device settings page and jump to the "keypad" section.
    return redirect(url_for('device_settings', device_id=device_id) + '#keypad')


# -------------------------------------------------------------------------
# 2. Route: Add Call Out Contact (with simple order management)
# Description: This route allows users to add a call-out contact for a device.
#              The logic varies according to the device type:
#              - For multi-button devices: verifies the button number and maximum entries per button.
#              - For apartment-based intercoms: verifies the apartment number and maximum entries.
#              - For simple devices: enforces a max of 5 call-out contacts.
@app.route('/devicesettings/<int:device_id>/add_call_out', methods=['POST'])
@login_required
def add_call_out(device_id):
    # Retrieve the contact name, phone number, and optional order from form data.
    contact_name = request.form.get('content_name')
    contact_number = request.form.get('content_number')
    contact_order = request.form.get('content_order')  # Retrieve the order value

    # Basic validation: Ensure name and number are provided.
    if not (contact_name and contact_number):
        flash('Name and phone number are required.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')

    # Attempt to convert the order to an integer; default to 0 if conversion fails.
    try:
        contact_order = int(contact_order)
    except (TypeError, ValueError):
        contact_order = 0  # Set a default if invalid value is provided

    # Retrieve the device information from the database.
    device_info = Device.query.get(device_id)

    # --- Multi-button devices (2 or 4 buttons) ---
    if device_info.device_type_name in ["Voyager Voice 2 button Intercom", "Voyager Voice 4 button Intercom"]:
        # Retrieve the button number from form data and validate it.
        try:
            call_out_button = int(request.form.get('content_button'))
        except (ValueError, TypeError):
            flash('Invalid button value.', 'danger')
            return redirect(url_for('device_settings', device_id=device_id) + '#charts')

        # Ensure the button number is within the valid range.
        if call_out_button < 1 or call_out_button > device_info.number_button:
            flash('Invalid button number.', 'danger')
            return redirect(url_for('device_settings', device_id=device_id) + '#charts')

        # Check if the maximum number of call-out entries (3) for this button has already been reached.
        existing = CallOutPhoneNumber.query.filter_by(
            device_id=device_id, button_device=call_out_button
        ).all()
        if len(existing) >= 3:
            flash(f'Button {call_out_button} already has the maximum call out entries (3).', 'danger')
            return redirect(url_for('device_settings', device_id=device_id) + '#charts')

        # Create a new CallOutPhoneNumber entry with the button parameter and order.
        call_out_entry = CallOutPhoneNumber(
            device_id=device_id,
            user_name=contact_name,
            phone_number=contact_number,
            button_device=call_out_button,
            order=contact_order
        )

        try:
            db.session.add(call_out_entry)
            db.session.commit()
            flash('Call Out contact created successfully!', 'success')
        except Exception:
            flash('Failed to create Call Out contact.', 'danger')
        # Redirect back to the device settings page, scrolling to the "charts" section.
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')

    # --- Apartment-based intercoms ---
    elif device_info.device_type_name == "Voyager Voice Appartment Intercom":
        # Retrieve the apartment number and validate it.
        try:
            call_out_apartment = int(request.form.get('content_apartment'))
        except (ValueError, TypeError):
            flash('Invalid apartment value.', 'danger')
            return redirect(url_for('device_settings', device_id=device_id) + '#charts')

        # Ensure the apartment number is within the valid range.
        if call_out_apartment < 1 or call_out_apartment > device_info.number_apartment:
            flash('Invalid apartment number.', 'danger')
            return redirect(url_for('device_settings', device_id=device_id) + '#charts')

        # Check if the maximum number of call-out entries (3) for this apartment has already been reached.
        existing = CallOutPhoneNumber.query.filter_by(
            device_id=device_id, apartment_device=call_out_apartment
        ).all()
        if len(existing) >= 3:
            flash(f'Apartment {call_out_apartment} already has the maximum call out entries (3).', 'danger')
            return redirect(url_for('device_settings', device_id=device_id) + '#charts')

        # Create the CallOut entry with apartment parameters and order.
        call_out_entry = CallOutPhoneNumber(
            device_id=device_id,
            user_name=contact_name,
            phone_number=contact_number,
            apartment_device=call_out_apartment,
            order=contact_order
        )

        try:
            db.session.add(call_out_entry)
            db.session.commit()
            flash('Call Out contact created successfully!', 'success')
        except Exception:
            flash('Failed to create Call Out contact.', 'danger')
        # Redirect and pass the apartment value to auto-select it.
        return redirect(url_for('device_settings', device_id=device_id, apartment=call_out_apartment) + '#charts')

    # --- Simple devices (no apartment or button) ---
    else:
        max_call_out = 5  # Define the maximum number of call-out contacts allowed.
        existing = CallOutPhoneNumber.query.filter_by(device_id=device_id).all()
        if len(existing) >= max_call_out:
            flash(f'You cannot add more than {max_call_out} Call Out contacts for this device.', 'danger')
            return redirect(url_for('device_settings', device_id=device_id) + '#charts')

        # Create a simple call-out entry without additional parameters.
        call_out_entry = CallOutPhoneNumber(
            device_id=device_id,
            user_name=contact_name,
            phone_number=contact_number,
            order=contact_order
        )

        try:
            db.session.add(call_out_entry)
            db.session.commit()
            flash('Call Out contact created successfully!', 'success')
        except Exception:
            flash('Failed to create Call Out contact.', 'danger')
        # Standard redirect to device settings.
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')


# -------------------------------------------------------------------------
# 3. Route: Add Regular Phone Number
# Description: This route allows a user to add a regular phone number contact to a device.
#              It also validates that no more than 200 phone numbers are added per device.
@app.route('/devicesettings/<int:device_id>/add_phone', methods=['POST'])
@login_required
def add_phone(device_id):
    # Retrieve the new phone contact details from the form.
    device_new_name = request.form['content_name']
    device_new_number = request.form['content_number']
    device_output = int(request.form.get('content_output', 1))  # Use provided output or default to 1

    # Check the current count of phone numbers for this device; limit to 200.
    count_phone_numbers = PhoneNumber.query.filter_by(device_id=device_id).count()
    if count_phone_numbers >= 200:
        flash('You cannot add more than 200 phone numbers for this device.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + '#users')

    # Create a new PhoneNumber entry with the given details.
    phone_number = PhoneNumber(
        device_id=device_id,
        phone_number=device_new_number,
        user_name=device_new_name,
        output=device_output
    )
    try:
        db.session.add(phone_number)
        db.session.commit()
        flash('Your new device phone number details have been created!', 'success')
        return redirect(url_for('device_settings', device_id=device_id) + '#users')
    except Exception as e:
        flash('There was an issue adding your device details', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + '#users')


# -------------------------------------------------------------------------
# Route: GET Device Settings Page
# Description: This route renders the device settings page, collecting various device-specific
#              details such as keypad codes, phone numbers, call-out contacts, and diagnostic data.
@app.route('/devicesettings/<int:device_id>', methods=['GET'])
@login_required
def device_settings(device_id):
    # Retrieve various device settings and data from the database.
    keypad_code = KeypadCode.query.filter_by(device_id=device_id)
    phone_numbers = PhoneNumber.query.filter_by(device_id=device_id)
    device_info = Device.query.get(device_id)
    call_out = CallOutPhoneNumber.query.filter_by(device_id=device_id).order_by(CallOutPhoneNumber.order).all()
    calls_out_json = [serialize_call_out(co) for co in call_out]  # Serialize call-out data for JSON use.
    ooh = OutOfHour.query.filter_by(device_id=device_id).first()
    a_s = AutomaticSchedule.query.filter_by(device_id=device_id)
    live_diags = LiveDiagnostics.query.filter_by(device_id=device_id)
    current_diags = CurrentDiagnostics.query.filter_by(device_id=device_id)
    stored_diags = CurrentDiagnostics.query.filter_by(device_id=device_id)
    
    # If OutOfHour settings do not exist, set default value.
    if not ooh:
        ooh = 0

    # Filter call-out entries based on the device type.
    if device_info.device_type_name in ["Voyager Voice 2 button Intercom", "Voyager Voice 4 button Intercom"]:
        entries = [co for co in call_out if co.button_device == 1]
    elif device_info.device_type_name == "Voyager Voice Appartment Intercom":
        entries = [co for co in call_out if co.apartment_device == 1]
    else:
        entries = call_out

    # Determine allowed order values for new call-out contacts.
    count = len(entries)
    allowed_orders = list(range(1, min(count + 2, 6)))
    used_orders = [co.order for co in entries]
    default_order = next((val for val in allowed_orders if val not in used_orders), allowed_orders[-1])

    # Render the device settings template with all necessary data.
    return render_template('devicesettings.html',
                           device_id=device_id,
                           calls_out=call_out,
                           calls_out_json=calls_out_json,  # JSON data provided to the template.
                           phone_numbers=phone_numbers,
                           keypad_code=keypad_code,
                           device_info=device_info,
                           allowed_orders=allowed_orders,
                           default_order=default_order,
                           page='open_number',
                           ooh=ooh,
                           a_s=a_s,
                           live_diags=live_diags,
                           current_diags=current_diags,
                           stored_diags=stored_diags)


# -------------------------------------------------------------------------
# Route: Edit Call In (Phone Number)
# Description: Handles updating a Call In user's details.
@app.route('/edit_call_in/<int:phone_number_id>', methods=['GET', 'POST'])
@login_required
def edit_call_in(phone_number_id):
    # Retrieve the phone number entry or return 404 if not found.
    phone_number = PhoneNumber.query.get_or_404(phone_number_id)
    
    if request.method == 'POST':
        # Get updated values from the form.
        phone_number.user_name = request.form.get('content_name')
        phone_number.phone_number = request.form.get('content_number')
        phone_number.output = request.form.get('content_output')
        
        try:
            # Save changes to the database.
            db.session.commit()
            flash('User details updated successfully!', 'success')
        except Exception as e:
            print(f"Error updating user details: {e}")
            flash('Error updating user details.', 'danger')
        # Redirect back to the device settings page, focusing on the 'users' tab.
        return redirect(url_for('device_settings', device_id=phone_number.device_id) + '#users')
    
    # For GET request, render the edit page with the current user details.
    return render_template('edit_call_in.html', phone_number=phone_number)

# -------------------------------------------------------------------------
# Route: API - Get Phone Stats
# Description: Returns JSON with total in/out phone number counts for a device.
@app.route('/api/phone_stats/<int:device_id>', methods=['GET'])
@login_required
def get_phone_stats(device_id):
    count_in = PhoneNumber.query.filter_by(device_id=device_id).count()
    count_out = CallOutPhoneNumber.query.filter_by(device_id=device_id).count()
    return jsonify({
        'total_numbers_in': count_in,
        'total_numbers_out': count_out
    })

# -------------------------------------------------------------------------
# Route: Delete Keypad Code
# Description: Deletes a specified keypad code.
@app.route('/delete_keypad_code/<int:keypad_code_id>', methods=['POST'])
@login_required
def delete_keypad_code(keypad_code_id):
    keypad_code_to_delete = KeypadCode.query.get(keypad_code_id)
    if keypad_code_to_delete:
        try:
            db.session.delete(keypad_code_to_delete)
            db.session.commit()
            flash('Keypad code deleted successfully!', 'success')
        except Exception as e:
            print(f"Error deleting keypad code: {e}")
            flash('Failed to delete keypad code.', 'danger')
    else:
        flash('Keypad code not found.', 'danger')
    return redirect(url_for('device_settings', device_id=keypad_code_to_delete.device_id if keypad_code_to_delete else keypad_code_to_delete.device_id) + '#keypad')

# ------------------------------------------------------------------------
# Route: Delete Call In Number
# Description: Deletes a call in phone number.
@app.route('/delete_call_in/<int:number_id>', methods=['POST'])
@login_required
def delete_call_in(number_id):
    number_to_delete = PhoneNumber.query.get(number_id)
    if number_to_delete:
        try:
            db.session.delete(number_to_delete)
            db.session.commit()
            flash('Call in number deleted successfully!', 'success')
        except Exception as e:
            print(f"Error deleting call in number: {e}")
            flash('Failed to delete call in number.', 'danger')
    else:
        flash('Call in number not found.', 'danger')
    return redirect(url_for('device_settings', device_id=number_to_delete.device_id if number_to_delete else number_to_delete.device_id)+ '#users')

# -------------------------------------------------------------------------
# Route: Delete Call Out Number
# Description: Deletes a call out phone number.
@app.route('/delete_call_out/<int:number_id>', methods=['POST'])
@login_required
def delete_call_out(number_id):
    number_to_delete = CallOutPhoneNumber.query.get(number_id)
    if number_to_delete is None:
        flash('Call out number not found.', 'danger')
        return redirect(url_for('home'))  # or wherever you prefer

    device_id = number_to_delete.device_id
    device_info = Device.query.get(device_id)

    try:
        db.session.delete(number_to_delete)
        db.session.commit()
        flash('Call out number deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete call out number.', 'danger')

    # If this is an apartment intercom, pass ?apartment=xxx to auto-show that apartment
    if device_info and device_info.device_type_name == "Voyager Voice Appartment Intercom":
        return redirect(
            url_for('device_settings', device_id=device_id, apartment=number_to_delete.apartment_device) + '#charts'
        )
    else:
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')


# -------------------------------------------------------------------------
# Route: Call Function
# Description: Calls the 'my_function' and returns its response.
@app.route('/call-function')
@login_required
def call_function():
    return my_function()

# -------------------------------------------------------------------------
# Route: Delete Phone Number
# Description: Deletes a phone number (by post id).
@app.route("/phonenumber/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_phone_number(id):
    phonenum = PhoneNumber.query.get_or_404(id)
    try:
        db.session.delete(phonenum)
        db.session.commit()
        flash('Your phone number has been deleted!', 'success')
    except:
        return 'There was an issue deleting your phone number'
    return redirect(url_for('home'))

# -------------------------------------------------------------------------
# Route: View Site
# Description: Displays details for a specific site.
@app.route("/site/<int:site_id>")
@login_required
def site(site_id):
    site_obj = Site.query.get_or_404(site_id)
    return render_template('site.html', title=site_obj.site_name, site=site_obj)

# -------------------------------------------------------------------------
# Route: Update Site
# Description: Updates site information.
@app.route("/site/<int:site_id>/update", methods=['GET', 'POST'])
@login_required
def update_site(site_id):
    site_obj = Site.query.get_or_404(site_id)
    if site_obj.user_id != current_user:
        abort(403)
    form = SiteForm_Update()
    if form.validate_on_submit():
        site_obj.site_name = form.title.data
        site_obj.site_contact_details = form.content.data
        db.session.commit()
        flash('Your site has been updated!', 'success')
        return redirect(url_for('site', site_id=site_obj.id))
    elif request.method == 'GET':
        form.title.data = site_obj.site_name
        form.content.data = site_obj.site_contact_details
    return render_template('create_site.html', title='Update Site', form=form, legend='Update Site')


# -------------------------------------------------------------------------
# Route: Show Devices
# Description: Displays devices for a specific site.
@app.route("/showdevices/<int:site_id>")
@login_required
def show_device(site_id):
    form = ShowDevicesForm()
    if form.validate_on_submit():
        return redirect(url_for('home'))
    elif request.method == 'GET':
        site_obj = Site.query.get(site_id)
        devices = Device.query.filter_by(site_id=site_id).all()
        return render_template('showdevices.html',
                               site=site_obj,
                               site_id=site_id,
                               devices=devices,
                               form=form)

# -------------------------------------------------------------------------
# Route: Set Pulse Time
# Description: Updates the pulse time for a device.
@app.route('/set_pulse_time/<int:device_id>', methods=['GET', 'POST'])
@login_required
def set_pulse_time(device_id):
    device = Device.query.filter_by(id=device_id).first()
    if not device:
        flash("Device not found.", "error")
        return redirect(url_for('device_settings', device_id=device_id) + '#settings')
    if request.method == 'POST':
        pulse_time = request.form.get('pulse_time')
        if pulse_time:
            try:
                pulse_time = int(pulse_time)
            except ValueError:
                flash("Pulse time must be an integer.", "error")
                return redirect(url_for('device_settings', device_id=device_id)+ '#settings')
            device.pulse_time = pulse_time
            db.session.commit()
            flash("Pulse time updated successfully.", "success")
        else:
            flash("Please enter a pulse time.", "error")
        return redirect(url_for('device_settings', device_id=device_id, actif=1)+ '#settings')
    return redirect(url_for('device_settings', device_id=device_id)+ '#settings')

# -------------------------------------------------------------------------
# Route: Manage Security Code
# Description: Enables, disables, or changes the security code for a device.
@app.route('/manage_security_code/<int:device_id>', methods=['GET', 'POST'])
@login_required
def manage_security_code(device_id):
    device = Device.query.filter_by(id=device_id).first()
    if not device:
        flash("Device not found.", "error")
        return redirect(url_for('device_settings', device_id=device_id)+ '#settings')
    if request.method == 'POST':
        status = request.form.get('security_code_status')
        new_code = request.form.get('new_security_code', '').strip()
        if status == 'disable':
            device.security_code_enable = False
            db.session.commit()
            flash("Security code has been disabled.", "success")
        elif status in ['enable', 'change']:
            if not new_code:
                flash("Please enter the new security code.", "error")
                return redirect(url_for('device_settings', device_id=device_id)+ '#settings')
            device.security_code_enable = True
            device.security_code = new_code
            db.session.commit()
            if status == 'enable':
                flash("Security code has been enabled.", "success")
            else:
                flash("Security code has been changed.", "success")
        else:
            flash("Invalid option.", "error")
    return redirect(url_for('device_settings', device_id=device_id)+ '#settings')

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------------------------------------------------------
# Route: Import Excel Data
# Description: Imports phone numbers from an uploaded Excel file.
@app.route('/import_excel_in/<int:device_id>', methods=['POST'])
@login_required
def import_excel_in(device_id):
    # Check if the file part exists in the request
    if 'excel_file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + '#users')
    
    file = request.files['excel_file']
    
    # Check if a file was selected
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + '#users')
    
    # Check for allowed file type (.xlsx or .xls)
    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload a .xlsx or .xls file.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + '#users')
    
    # Get the excel type from the form (if available)
    excel_type = request.form.get('excel_type')
    
    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(file)
        
        # Define required columns based on the excel type
        if excel_type == 'call_out':
            required_columns = ['user_name', 'phone_number']
        else:
            required_columns = ['user_name', 'phone_number', 'output']
        
        # Check if the required columns exist in the DataFrame
        if not all(col in df.columns for col in required_columns):
            flash(f'The Excel file must contain columns: {", ".join(required_columns)}.', 'danger')
            return redirect(url_for('device_settings', device_id=device_id) + '#users')
        
        # Remove rows where all values are NaN
        df = df.dropna(how='all')
        
        # Count the number of rows in the Excel file
        new_rows_count = len(df)
        
        # Count the current number of phone numbers in the database
        if excel_type == 'call_out':
            current_count = CallOutPhoneNumber.query.filter_by(device_id=device_id).count()
        else:
            current_count = PhoneNumber.query.filter_by(device_id=device_id).count()
        
        # Verify that the sum of existing phone numbers and new rows does not exceed 200
        if current_count + new_rows_count > 200:
            flash(f'Import aborted: adding {new_rows_count} rows would exceed the limit of 200 phone numbers.', 'danger')
            return redirect(url_for('device_settings', device_id=device_id) + '#users')
        
        # Compile a regex to validate user names (letters and spaces only)
        name_regex = re.compile(r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$')
        
        # Validate and transform each row
        for index, row in df.iterrows():
            # Process and validate user_name: trim spaces, non-empty, <= 20 chars, only letters/spaces
            name = str(row['user_name']).strip()
            if not name:
                flash(f'User name is empty in row {index+1}.', 'danger')
                return redirect(url_for('device_settings', device_id=device_id) + '#users')
            if len(name) > 20:
                flash(f'User name in row {index+1} exceeds 20 characters.', 'danger')
                return redirect(url_for('device_settings', device_id=device_id) + '#users')
            if not name_regex.fullmatch(name):
                flash(f'User name in row {index+1} contains invalid characters. Only letters and spaces are allowed.', 'danger')
                return redirect(url_for('device_settings', device_id=device_id) + '#users')
            
            # Process and validate phone_number
            raw_phone = row['phone_number']
            try:
                # If the phone number is numeric (int or float), convert it properly.
                if isinstance(raw_phone, (int, float)):
                    # Convert to integer and then format as a 10-digit string (padded with zeros if necessary)
                    phone = f"{int(raw_phone):010d}"
                else:
                    phone = str(raw_phone).strip()
            except Exception as e:
                flash(f'Error processing phone number in row {index+1}: {str(e)}', 'danger')
                return redirect(url_for('device_settings', device_id=device_id) + '#users')
            
            # Ensure phone consists only of digits and has exactly 10 digits
            if not phone.isdigit():
                flash(f'Phone number in row {index+1} must contain only digits.', 'danger')
                return redirect(url_for('device_settings', device_id=device_id) + '#users')
            if len(phone) != 10:
                flash(f'Phone number in row {index+1} must have exactly 10 digits. Found {len(phone)} digits.', 'danger')
                return redirect(url_for('device_settings', device_id=device_id) + '#users')
            # Update the DataFrame with the processed phone number
            df.at[index, 'phone_number'] = phone
            
            # For non-call_out, validate the output column
            if excel_type != 'call_out':
                try:
                    output_value = int(row['output'])
                except ValueError:
                    flash(f'Invalid output value in row {index+1}.', 'danger')
                    return redirect(url_for('device_settings', device_id=device_id) + '#users')
                if output_value not in [1, 2]:
                    flash(f'Output in row {index+1} must be either 1 or 2.', 'danger')
                    return redirect(url_for('device_settings', device_id=device_id) + '#users')
        
        # All validations passed; add each row to the database
        for index, row in df.iterrows():
            if excel_type == 'call_out':
                new_call = CallOutPhoneNumber(
                    device_id=device_id,
                    user_name=str(row['user_name']).strip(),
                    phone_number=str(row['phone_number'])
                )
                db.session.add(new_call)
            else:
                new_phone = PhoneNumber(
                    device_id=device_id,
                    user_name=str(row['user_name']).strip(),
                    phone_number=str(row['phone_number']),
                    output=int(row['output'])
                )
                db.session.add(new_phone)
        
        db.session.commit()
        flash('Excel file imported successfully!', 'success')
        return redirect(url_for('device_settings', device_id=device_id) + '#users')
    
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + '#users')
    
@app.route('/import_excel_out/<int:device_id>', methods=['POST'])
@login_required
def import_excel_out(device_id):
    if 'excel_file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id))
    
    file = request.files['excel_file']
    
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id))
    
    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload a .xlsx or .xls file.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id))
    
    # Get the excel type from the form (if available)
    excel_type = request.form.get('excel_type')
    
    try:
        # Read the Excel file in memory
        df = pd.read_excel(file)
        
        # Define required columns based on the excel_type
        if excel_type == 'call_out':
            required_columns = ['user_name', 'phone_number']
        else:
            required_columns = ['user_name', 'phone_number', 'output']
        
        # Check if required columns exist
        if not all(col in df.columns for col in required_columns):
            flash(f'The Excel file must contain columns: {", ".join(required_columns)}.', 'danger')
            return redirect(url_for('device_settings', device_id=device_id))
        
        # Remove rows where all values are NaN
        df = df.dropna(how='all')
        
        # Validate each row
        for index, row in df.iterrows():
            for col in required_columns:
                if pd.isnull(row[col]):
                    flash(f'Empty field found in column "{col}" in row {index+1}.', 'danger')
                    return redirect(url_for('device_settings', device_id=device_id))
            
            phone_str = str(row['phone_number'])
            if not (8 <= len(phone_str) <= 12):
                flash(f'Phone number in row {index+1} must be between 8 and 12 characters.', 'danger')
                return redirect(url_for('device_settings', device_id=device_id))
            
            if excel_type != 'call_out':
                output_value = row['output']
                if output_value not in [1, 2]:
                    flash(f'Output in row {index+1} must be either 1 or 2.', 'danger')
                    return redirect(url_for('device_settings', device_id=device_id))
        
        # All validations passed: add each row to the database
        for index, row in df.iterrows():
            if excel_type == 'call_out':
                new_call = CallOutPhoneNumber(
                    device_id=device_id,
                    user_name=row['user_name'],
                    phone_number=str(row['phone_number'])
                )
                db.session.add(new_call)
            else:
                new_phone = PhoneNumber(
                    device_id=device_id,
                    phone_number=str(row['phone_number']),
                    user_name=row['user_name'],
                    output=int(row['output'])
                )
                db.session.add(new_phone)
        
        db.session.commit()
        flash('Excel file imported successfully!', 'success')
        return redirect(url_for('device_settings', device_id=device_id))
    
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'danger')
        return redirect(url_for('device_settings', device_id=device_id))


# -------------------------------------------------------------------------
# Route: Download Phone Numbers
# Description: Downloads the phone numbers as an Excel file.
#              Depending on the excel_type parameter, it exports either
#              call-out numbers or regular phone numbers.
@app.route('/download_phone_numbers/<int:device_id>', methods=['GET'])
@login_required
def download_phone_numbers(device_id):
    # Retrieve the 'excel_type' query parameter to determine which set of phone numbers to export.
    excel_type = request.args.get('excel_type')
    
    if excel_type == 'call_out':
        # For call-out contacts, query phone numbers specific to call out.
        phone_numbers = CallOutPhoneNumber.query.filter_by(device_id=device_id).all()
        data = {
            'user_name': [pn.user_name for pn in phone_numbers],
            'phone_number': [pn.phone_number for pn in phone_numbers]
        }
    else:
        # For regular phone numbers, query the PhoneNumber table.
        phone_numbers = PhoneNumber.query.filter_by(device_id=device_id).all()
        data = {
            'user_name': [pn.user_name for pn in phone_numbers],
            'phone_number': [pn.phone_number for pn in phone_numbers],
            'output': [pn.output for pn in phone_numbers]
        }
    
    # Convert the data dictionary into a Pandas DataFrame.
    df = pd.DataFrame(data)
    
    # Define a temporary folder in the application root for storing the download.
    temp_folder = os.path.join(current_app.root_path, 'downloads')
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    
    # Define the filename based on the device_id.
    filename = f'phone_numbers_{device_id}.xlsx'
    full_path = os.path.join(temp_folder, filename)
    
    # Save the DataFrame to an Excel file with the specified sheet name.
    df.to_excel(full_path, index=False, sheet_name='PhoneNumbers', engine='openpyxl')
    
    # Use Flask's send_file to send the file as an attachment to the client.
    return send_file(full_path, as_attachment=True)


# -------------------------------------------------------------------------
# Route: Download manage_ooh
# Description: Updates the Out Of Hours (OOH) configuration for a device.
#              Processes form input for toggling OOH, time ranges, and alternative phone number.
@app.route('/manage_ooh/<int:device_id>', methods=['POST'])
@login_required
def update_ooh(device_id):
    # Retrieve form values.
    ooh_enable = request.form.get('oohModeToggle')
    global_start = request.form.get('globalStart')
    global_end = request.form.get('globalEnd')
    alternate_number = request.form.get('alternateNumber', '').strip()

    # Attempt to find an existing OutOfHour configuration for the device.
    ooh = OutOfHour.query.filter_by(device_id=device_id).first()
    if not ooh:
        ooh = OutOfHour(device_id=device_id)
    
    # If no OOH mode is enabled, disable OOH and update the database.
    if not ooh_enable:
        ooh.out_of_hours_enabled = False
        db.session.add(ooh)
        db.session.commit()
        flash("Out Of Hours configuration disabled successfully.", "success")
        return redirect(url_for('device_settings', device_id=device_id) + '#ooh')
    
    # Set OOH mode on.
    ooh.out_of_hours_enabled = True

    # Process the active days by checking for each day in the form.
    days = []
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        if request.form.get(day + 'Active'):
            days.append(day.capitalize())
    # Join the days into a comma-separated string.
    ooh.days = ','.join(days)

    # Set the start and end time for the OOH configuration.
    ooh.start_time = global_start
    ooh.end_time = global_end

    # If no alternate phone number is provided, set a default value.
    if not alternate_number:
        ooh.alternative_phone_no = "0000"
    else:
        ooh.alternative_phone_no = alternate_number

    # Update the database.
    db.session.add(ooh)
    db.session.commit()
    flash("Out Of Hours configuration updated successfully.", "success")
    return redirect(url_for('device_settings', device_id=device_id) + '#ooh')


# -------------------------------------------------------------------------
# Route: Create New Keypad Code
# Description: Creates a new keypad code with four code type options.
#              Supports day-limited and temporary codes by retrieving additional
#              time or day parameters from the form.
@app.route('/device/<int:device_id>/keypad/new', methods=['GET', 'POST'])
@login_required
def new_keypad_code(device_id):
    if request.method == 'POST':
        # Maximum number of keypad codes allowed per device.
        MAX_KEYPAD_CODES = 10
        
        # Check the current count of keypad codes for the device.
        existing_count = KeypadCode.query.filter_by(device_id=device_id).count()
        if existing_count >= MAX_KEYPAD_CODES:
            flash("You cannot create more than 10 keypad codes for this device.", "error")
            return redirect(url_for('device_settings', device_id=device_id) + '#keypad')
        
        # Retrieve and validate the keypad code; must be exactly 4 numeric digits.
        code = request.form.get('keypadCode', '').strip()
        if len(code) != 4 or not code.isdigit():
            flash("Keypad code must be exactly 4 numeric digits.", "error")
            return redirect(url_for('device_settings', device_id=device_id) + '#keypad')
        
        # Retrieve the code type; default to "24_7" if none provided.
        code_type = request.form.get('codeType', '24_7')
        days = None
        start_time = None
        end_time = None
        temp_days = None
        
        # If the code type is day-limited, retrieve days and time range.
        if code_type in ['day_limited', 'day_limited_temp']:
            day_list = []
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                if request.form.get(day):
                    day_list.append(day.capitalize())
            days = ','.join(day_list)
            start_time = request.form.get('startTime', '').strip()
            end_time = request.form.get('endTime', '').strip()
            # Check that time fields are provided.
            if not start_time or not end_time:
                flash("For a day-limited code, you must provide a valid time range.", "error")
                return redirect(url_for('device_settings', device_id=device_id) + '#keypad')
        
        # If the code type is temporary, retrieve the temporary duration.
        if code_type in ['24_7_temp', 'day_limited_temp']:
            try:
                temp_days = int(request.form.get('numDays', '').strip())
                if temp_days <= 0:
                    flash("Number of days must be a positive integer.", "error")
                    return redirect(url_for('device_settings', device_id=device_id) + '#keypad')
            except ValueError:
                flash("Invalid number of days.", "error")
                return redirect(url_for('device_settings', device_id=device_id) + '#keypad')
        
        # Retrieve the output value from the form; defaults to "1".
        output = request.form.get('output', '1').strip()
        
        # Create a new KeypadCode object with all the fields gathered.
        new_code = KeypadCode(
            device_id=device_id,
            key_code=code,
            code_type=code_type,
            days=days,
            start_time=start_time,
            end_time=end_time,
            output=output,
            temp_days=temp_days
        )
        db.session.add(new_code)
        db.session.commit()
        
        flash("Keypad code created successfully!", "success")
        return redirect(url_for('device_settings', device_id=device_id) + '#keypad')
    
    # For GET requests, simply redirect back to the device settings page.
    return redirect(url_for('device_settings', device_id=device_id) + '#keypad')


# -------------------------------------------------------------------------
# Route: New Automatic Schedule.
# Description: Creates a new automatic schedule for a device.
#              Validates time formats, days selection, and limits the number
#              of schedules to 10 per device.
@app.route('/device/<int:device_id>/automatic_schedule/new', methods=['GET', 'POST'])
@login_required
def new_automatic_schedule(device_id):
    if request.method == 'POST':
        # Limit the number of schedules per device to 10.
        existing_count = AutomaticSchedule.query.filter_by(device_id=device_id).count()
        if existing_count >= 10:
            flash("You cannot create more than 10 automatic schedules for this device.", "error")
            return redirect(url_for('device_settings', device_id=device_id) + '#as')

        # Debug print to show the received form data.
        print("Données reçues dans request.form:", request.form)

        # Retrieve and parse the 'output' value.
        output = request.form.get('output', '1').strip()
        try:
            output = int(output)
        except ValueError:
            output = 1

        # Retrieve start_time and end_time directly from the form.
        start_time = request.form.get('startTime', '').strip()
        end_time = request.form.get('endTime', '').strip()

        # If start or end time is missing, attempt to build it from hour and minute fields.
        if not start_time or not end_time:
            start_hour = request.form.get('startTimeHour', '').strip()
            start_minute = request.form.get('startTimeMinute', '').strip()
            end_hour = request.form.get('endTimeHour', '').strip()
            end_minute = request.form.get('endTimeMinute', '').strip()

            print("startTimeHour:", start_hour)
            print("startTimeMinute:", start_minute)
            print("endTimeHour:", end_hour)
            print("endTimeMinute:", end_minute)

            if start_hour and start_minute:
                start_time = f"{start_hour}:{start_minute}"
            if end_hour and end_minute:
                end_time = f"{end_hour}:{end_minute}"

        print("startTime combiné:", start_time)
        print("endTime combiné:", end_time)

        # Validate that time is in a proper HH:MM format.
        def is_valid_time_format(time_str):
            if not time_str:
                return False
            try:
                hours, minutes = map(int, time_str.split(':'))
                # Ensure hours and minutes are in valid ranges and the format is exactly HH:MM.
                return 0 <= hours <= 23 and 0 <= minutes <= 59 and len(time_str) == 5
            except (ValueError, AttributeError):
                return False

        if not is_valid_time_format(start_time) or not is_valid_time_format(end_time):
            flash("Invalid time format for 'Open At' or 'Close At'. Please use the format HH:MM (e.g., 14:30).", "error")
            return redirect(url_for('device_settings', device_id=device_id) + '#as')

        # Retrieve and validate the number of days.
        days = request.form.get('numDays')
        if days:
            try:
                days = int(days)
                if days < 1:
                    flash("Number of days must be a positive integer.", "error")
                    return redirect(url_for('device_settings', device_id=device_id) + '#as')
            except ValueError:
                days = None

        # Process the selected days from a list; require at least one day.
        selected_days = request.form.getlist('days')
        if selected_days:
            selected_days = [day.capitalize() for day in selected_days]
            n_days = ','.join(selected_days)
        else:
            flash("At least one day must be selected.", "error")
            return redirect(url_for('device_settings', device_id=device_id) + '#as')

        # Create a new AutomaticSchedule object with the gathered parameters.
        new_schedule = AutomaticSchedule(
            device_id=device_id,
            output=output,
            start_time=start_time,
            end_time=end_time,
            n_days=n_days,
            days=days
        )

        try:
            db.session.add(new_schedule)
            db.session.commit()
            flash("Automatic schedule created successfully!", "success")
            return redirect(url_for('device_settings', device_id=device_id) + '#as')
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating automatic schedule: {str(e)}", "error")
            return redirect(url_for('device_settings', device_id=device_id) + '#as')
    
    # For non-POST requests, redirect back to the device settings page.
    return redirect(url_for('device_settings', device_id=device_id) + '#as')


# -------------------------------------------------------------------------
# Route: Delete Automatic Schedule.
# Description: Delete an existing automatic schedule.
@app.route('/automatic_schedule/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete_automatic_schedule(schedule_id):
    # Retrieve the schedule or return a 404 error if not found.
    schedule = AutomaticSchedule.query.get_or_404(schedule_id)
    # Get the device_id for redirection after deletion.
    device_id = schedule.device_id
    # Delete the schedule and commit the change.
    db.session.delete(schedule)
    db.session.commit()
    flash("Automatic schedule deleted successfully!", "success")
    # Redirect back to the device settings page, scrolling to the 'as' (automatic schedule) section.
    return redirect(url_for('device_settings', device_id=device_id) + '#as')


# -------------------------------------------------------------------------
# Route: Admin Page.
# Description: Render the admin page for a device.
@app.route('/admin-page/<int:device_id>')
@login_required
def admin_page(device_id):
    # Check if the current user has administrator privileges.
    if not current_user.administrator:
        flash("You are not authorized to access this page.", "danger")
        return redirect(url_for('home'))
    # Render the admin page template with the device_id.
    return render_template('admin_page.html', device_id=device_id)


# -------------------------------------------------------------------------
# Function: allowed_file.
# Description: Check if the file has an allowed extension (xls or xlsx).
def allowed_file(filename):
    # Valid file extensions.
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}


# -------------------------------------------------------------------------
# Function: get_first_row_as_strings.
# Description: Reads an Excel file and returns the first row as a list of strings.
def get_first_row_as_strings(excel_file_path):
    # Read the Excel file into a DataFrame.
    df = pd.read_excel(excel_file_path)
    # Extract the first row as a list.
    first_row = df.iloc[0].tolist()
    # Convert all values in the first row to strings.
    first_row_strings = [str(item) for item in first_row]
    return first_row_strings


# -------------------------------------------------------------------------
# Function: split_diag.
# Description: Split diagnostic string and extract diagnostic values using a regex pattern.
def split_diag(diag_str):
    # Regular expression pattern to capture different diagnostic metrics.
    pattern = (
        r'^(.*?)\s*NV:\s*'              # Capture software version or identifier before NV:
        r'SS too low:\s*(\d+)\s*'        # Capture "Signal strength too low" count.
        r'Not checking SS:\s*(\d+)\s*'    # Capture "Not checking signal strength" count.
        r'Cant register:\s*(\d+)\s*'      # Capture "Cannot register" count.
        r'OS Problem:\s*(\d+)\s*'         # Capture "OS Problem" count.
        r'State stuck:\s*(\d+)'           # Capture "State stuck" count.
    )
    match = re.match(pattern, diag_str)
    if match:
        # Extract the captured values: first group as a string and subsequent groups as integers.
        extracted_values = [match.group(1).strip()] + [int(match.group(i)) for i in range(2, 7)]
        return extracted_values
    else:
        # Return an error indicator if the format does not match.
        return ["Format incorrect"]


# -------------------------------------------------------------------------
# Function: split_live_diag_live.
# Description: Split a live diagnostic string into lines and extract relevant values.
def split_live_diag_live(diag_str):
    # Split the diagnostic string into non-empty, stripped lines.
    lines = [line.strip() for line in diag_str.splitlines() if line.strip()]
    result = []
    # Process each line.
    for line in lines:
        if line.startswith("Signal Level"):
            # Search for signal level and mode in the line.
            m = re.search(r'Signal Level\s+(\d+)\s+Mode is\s+(\S+)', line)
            if m:
                result.append(m.group(1))  # Append signal level.
                result.append(m.group(2))  # Append mode.
        elif line.startswith("SIM Number:"):
            # Extract SIM number by splitting the line.
            parts = line.split("SIM Number:")
            if len(parts) > 1:
                result.append(parts[1].strip())
        elif line == "Relay:":
            # Skip the line if it contains only "Relay:".
            continue
        elif ':' in line:
            # For any line with a colon, split by the first colon and take the right-hand part.
            parts = line.split(":", 1)
            result.append(parts[1].strip())
        else:
            # Append the line as is.
            result.append(line)
    return result


# -------------------------------------------------------------------------
# Route: Live Diagnostics.
# Description: Process an uploaded file containing live diagnostics data.
@app.route('/diag-live/<int:device_id>', methods=['POST'])
@login_required
def diag_live(device_id):
    # Retrieve the device information.
    device_info = Device.query.get_or_404(device_id)
    # Restrict access to administrators.
    if not current_user.administrator:
        flash("You are not authorized to access this page.", "danger")
        return redirect(url_for('home'))

    # Ensure that a file was uploaded in the request.
    if 'file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + "#diag")

    file = request.files['file']
    if file.filename == '':
        flash('No selected file.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + "#diag")
    
    if file and allowed_file(file.filename):
        try:
            # Extract the first row from the Excel file as strings.
            data = get_first_row_as_strings(file)
            # Assume the last column contains the live diagnostic string.
            chaine = data[-1]
            # Remove the last element from the data list.
            data = data[:-1]
            # Split and process the live diagnostic string.
            result = split_live_diag_live(chaine)
            # Create a new LiveDiagnostics record with parsed values.
            diagnostic = LiveDiagnostics(
                device_id=device_info.id,
                device_type=device_info.device_type_name,
                sw_version=result[0],
                date_diag=datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                instantaneous_band=result[2],
                instantaneous_signal_strength=result[1],
                state_of_relay_1=result[4],
                state_of_relay_2=result[5],
                stored_device_phone_number=result[3]
            )
            db.session.add(diagnostic)
            db.session.commit()
            flash("Live diagnostics data uploaded successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error processing file: {str(e)}", "danger")
        # Redirect back to the diagnostics section of the device settings page.
        return redirect(url_for('device_settings', device_id=device_id) + "#diag")
    else:
        flash("Invalid file extension. Please upload a .xlsx or .xls file.", "danger")
        return redirect(url_for('device_settings', device_id=device_id) + "#diag")


# -------------------------------------------------------------------------
# Route: Current Diagnostics.
# Description: Process an uploaded file containing current diagnostics data.
@app.route('/diag-current/<int:device_id>', methods=['POST'])
@login_required
def diag_current(device_id):
    # Retrieve device details.
    device_info = Device.query.get_or_404(device_id)
    # Restrict access to administrators.
    if not current_user.administrator:
        flash("You are not authorized to access this page.", "danger")
        return redirect(url_for('home'))
    
    # Verify that a file has been uploaded.
    if 'file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + "#diag")
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file.', 'danger')
        return redirect(url_for('device_settings', device_id=device_id) + "#diag")
    
    if file and allowed_file(file.filename):
        try:
            # Read and process the first row of the Excel file.
            data = get_first_row_as_strings(file)
            chaine = data[-1]
            data = data[:-1]
            diag_input = chaine
            # Split and parse the diagnostic string.
            result = split_diag(diag_input)
            # Create a new CurrentDiagnostics record with the parsed values.
            diagnostic = CurrentDiagnostics(
                device_id=device_info.id,
                device_type=device_info.device_type_name,
                sw_version=result[0],
                date_diag=datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                count_signal_strength_too_low=result[1],
                count_not_checking_signal_strength=result[2],
                count_cannot_register=result[3],
                count_os_problem=result[4],
                count_state_stuck=result[5]
            )
            db.session.add(diagnostic)
            db.session.commit()
            flash("Current diagnostics data uploaded successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error processing file: {str(e)}", "danger")
        return redirect(url_for('device_settings', device_id=device_id) + "#diag")
    else:
        flash("Invalid file extension. Please upload a .xlsx or .xls file.", "danger")
        return redirect(url_for('device_settings', device_id=device_id) + "#diag")


 # -------------------------------------------------------------------------
# Route: Ring Time.
# Description: Change Ring Time.
@app.route('/set_ring_time/<int:device_id>', methods=['GET', 'POST'])
@login_required
def set_ring_time(device_id):
    # Look up the device using the provided device_id.
    device = Device.query.filter_by(id=device_id).first()
    if not device:
        # If the device is not found, display an error message and redirect.
        flash("Device not found.", "error")
        return redirect(url_for('device_settings', device_id=device_id) + '#settings')
    
    if request.method == 'POST':
        # Retrieve the new ring time from the form.
        ring_time = request.form.get('ring_time')
        if ring_time:
            try:
                # Attempt to convert the ring time to an integer.
                ring_time = int(ring_time)
            except ValueError:
                # If the conversion fails, flash an error message and redirect.
                flash("Ring time must be an integer.", "error")
                return redirect(url_for('device_settings', device_id=device_id) + '#settings')
            # Update the device's ring time in the database.
            device.ring_time = ring_time
            db.session.commit()
            flash("Ring time updated successfully.", "success")
        else:
            # If no ring time was provided in the form, flash an error message.
            flash("Please enter a ring time.", "error")
        # Redirect back to the device settings page, with an additional parameter for active status.
        return redirect(url_for('device_settings', device_id=device_id, actif=1) + '#settings')
    # For non-POST requests, simply redirect back to the settings section.
    return redirect(url_for('device_settings', device_id=device_id) + '#settings')


# -------------------------------------------------------------------------
# Route: Talk Time.
# Description: Change Talk Time.
@app.route('/set_talk_time/<int:device_id>', methods=['GET', 'POST'])
@login_required
def set_talk_time(device_id):
    # Retrieve the device based on the device_id.
    device = Device.query.filter_by(id=device_id).first()
    if not device:
        flash("Device not found.", "error")
        return redirect(url_for('device_settings', device_id=device_id) + '#settings')
    
    if request.method == 'POST':
        # Get the new talk time from the submitted form.
        talk_time = request.form.get('talk_time')
        if talk_time:
            try:
                # Convert the talk time to an integer.
                talk_time = int(talk_time)
            except ValueError:
                # If conversion fails, show an error message.
                flash("Talk time must be an integer.", "error")
                return redirect(url_for('device_settings', device_id=device_id) + '#settings')
            # Update the device's talk time attribute.
            device.talk_time = talk_time
            db.session.commit()
            flash("Talk time updated successfully.", "success")
        else:
            # If no value is provided, display an error message.
            flash("Please enter a talk time.", "error")
        # Redirect the user back to the settings page with a parameter to indicate active settings.
        return redirect(url_for('device_settings', device_id=device_id, actif=1) + '#settings')
    # For non-POST requests, perform a simple redirection.
    return redirect(url_for('device_settings', device_id=device_id) + '#settings')


# -------------------------------------------------------------------------
# Route: Call Out Number EDIT.
# Description: Edits a Call Out contact (with apartment redirect if applicable).
@app.route('/edit_call_out/<int:number_id>', methods=['GET', 'POST'])
@login_required
def edit_call_out(number_id):
    # Retrieve the call-out entry using its unique ID or return 404 if not found.
    call_out_entry = CallOutPhoneNumber.query.get_or_404(number_id)
    # Retrieve the device information associated with the call-out.
    device_info = Device.query.get_or_404(call_out_entry.device_id)

    if request.method == 'POST':
        # Retrieve new contact details from the form.
        contact_name = request.form.get('content_name')
        contact_number = request.form.get('content_number')
        
        if not (contact_name and contact_number):
            # Ensure that both name and number fields are provided.
            flash('Both name and phone number are required.', 'danger')
            return redirect(url_for('device_settings', device_id=call_out_entry.device_id) + '#charts')
        
        # Update the existing call-out entry with the new details.
        call_out_entry.user_name = contact_name
        call_out_entry.phone_number = contact_number
        
        try:
            # Commit the changes to the database.
            db.session.commit()
            flash('Call Out contact updated successfully!', 'success')
        except Exception as e:
            # Log error, roll back the session, and show an error message.
            print(f"Error updating call out contact: {e}")
            db.session.rollback()
            flash('Failed to update Call Out contact.', 'danger')

        # For apartment intercom devices, include an apartment parameter in the redirect.
        if device_info.device_type_name == "Voyager Voice Appartment Intercom":
            return redirect(url_for('device_settings',
                                    device_id=call_out_entry.device_id,
                                    apartment=call_out_entry.apartment_device) + '#charts')
        else:
            # Standard redirect if not an apartment intercom.
            return redirect(url_for('device_settings', device_id=call_out_entry.device_id) + '#charts')
    
    # For GET requests, render the form to edit the call-out contact.
    return render_template('edit_call_out.html', call_out=call_out_entry)


# -------------------------------------------------------------------------
# Route: Call Out Number EDIT button.
# Description: Edits the name of a Call Out button for a specific device.
@app.route('/edit_button_name/<int:device_id>', methods=['POST'])
@login_required
def edit_button_name(device_id):
    # Retrieve the new name entered by the user
    new_name = request.form.get('new_name')
    # Retrieve and convert the button number from the form
    try:
        button_num = int(request.form.get('button_num'))
    except (ValueError, TypeError):
        # Flash an error if the button number is invalid
        flash("Invalid button number.", "danger")
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')
    
    # Retrieve the device record; return 404 if not found
    device = Device.query.get_or_404(device_id)
    
    # Validate the button number within allowed range
    if button_num < 1 or button_num > device.number_button:
        flash("Invalid button number.", "danger")
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')
    
    # Ensure the names_array field is properly initialized for the number of buttons
    if not device.names_array or len(device.names_array) < device.number_button:
        device.names_array = ['No Name'] * device.number_button
    
    # Update the button name at the corresponding index (adjust for 0-based index)
    device.names_array[button_num - 1] = new_name
    # Mark the field as modified to ensure SQLAlchemy detects the update
    flag_modified(device, "names_array")
    
    try:
        # Commit changes to the database
        db.session.commit()
        flash("Button name updated successfully!", "success")
    except Exception as e:
        # Roll back if there is an error and show a failure message
        db.session.rollback()
        flash("Failed to update button name.", "danger")
    
    # Redirect back to the device settings with the charts section visible
    return redirect(url_for('device_settings', device_id=device_id) + '#charts')


# -------------------------------------------------------------------------
# Function: serialize_call_out.
# Description: Converts a CallOutPhoneNumber object into a dictionary format.
def serialize_call_out(call_out):
    return {
        "id": call_out.id,
        "device_id": call_out.device_id,
        "phone_number": call_out.phone_number,
        "user_name": call_out.user_name,
        "order": call_out.order,
        "button_device": call_out.button_device,
        "apartment_device": call_out.apartment_device
    }


# -------------------------------------------------------------------------
# Route: Call Out Number EDIT appartement.
# Description: Edits an apartment name (for apartment intercom devices).
@app.route('/rename_apartment/<int:device_id>', methods=['POST'])
@login_required
def rename_apartment(device_id):
    # Retrieve the device information; return 404 if not found.
    device_info = Device.query.get_or_404(device_id)
    
    # Ensure that this device is an apartment intercom.
    if device_info.device_type_name != "Voyager Voice Appartment Intercom":
        flash("This device does not support apartment renaming.", "danger")
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')

    # Retrieve and convert the apartment number from the form.
    try:
        apartment_number = int(request.form.get('apartment_number'))
    except (ValueError, TypeError):
        flash("Invalid apartment number.", "danger")
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')

    # Retrieve the new apartment name and validate its length.
    new_name = request.form.get('new_name')
    if not new_name or len(new_name) > 50:
        flash("Invalid name. Must be between 1 and 50 characters.", "danger")
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')

    # Validate the apartment number within allowed range.
    if apartment_number < 1 or apartment_number > device_info.number_apartment:
        flash("Invalid apartment number.", "danger")
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')

    # Ensure names_array is initialized properly for apartment intercoms.
    if not device_info.names_array or len(device_info.names_array) < device_info.number_apartment:
        device_info.names_array = ['No Name'] * device_info.number_apartment

    # Update the apartment name (using 0-based indexing).
    device_info.names_array[apartment_number - 1] = new_name
    flag_modified(device_info, "names_array")

    try:
        # Commit changes to the database.
        db.session.commit()
        flash(f"Apartment {apartment_number} renamed to {new_name}!", "success")
    except Exception:
        db.session.rollback()
        flash("Failed to rename apartment.", "danger")

    # Redirect with an apartment parameter to maintain focus in the UI.
    return redirect(url_for('device_settings', device_id=device_id, apartment=apartment_number) + '#charts')


# -------------------------------------------------------------------------
# Route: All Apartment View.
# Description: Displays a view that shows all apartment call out contacts for the device.
@app.route('/devicesettings/<int:device_id>/all_apartments', methods=['GET'])
@login_required
def all_apartments_view(device_id):
    # Retrieve the device record.
    device_info = Device.query.get_or_404(device_id)

    # Check if the device is indeed an apartment intercom.
    if device_info.device_type_name != "Voyager Voice Appartment Intercom":
        flash("This device is not an apartment intercom.", "danger")
        return redirect(url_for('device_settings', device_id=device_id) + '#charts')

    # Retrieve all call out contacts for this device.
    calls_out = CallOutPhoneNumber.query.filter_by(device_id=device_id).all()

    # Render a template that displays all apartment information.
    return render_template(
        "all_apartments_call_out.html",
        device_info=device_info,
        calls_out=calls_out
    )
