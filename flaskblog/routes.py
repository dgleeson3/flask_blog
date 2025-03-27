import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, redirect
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, PostForm_Update, ShowSitesForm, AddDevice, ShowDevicesForm
from flaskblog.models import UserAccount, Post, Site, PhoneNumber, OutOfHour, KeypadCode, Device
from flask_login import login_user, current_user, logout_user, login_required
from flaskblog import db
from flask_marshmallow import Marshmallow
from flask import jsonify


# import 2nd set of routes for device
#import routes2

#
#   Functions for now...
#   Find a better location
def my_function(): 
    # Code to be executed when the function is called 
    # this text will be seen on the command prompt
    print("function called my_function - redirect")
    # putting text in the return here will give a dialog box with the details
    #return "Function has been called!"
 #   return redirect(url_for('about'))
 #   return redirect("/adddevice",code=302)
 #   return redirect(url_for('post', post_id=1))
    return redirect(url_for('home'))
    return render_template('login.html', title='Login', form=form)

@app.route("/")
@app.route("/home")
def home():
    if current_user.is_authenticated:
#        return redirect(url_for('home'))
        return redirect(url_for('showsites'))
    form = LoginForm()
    if form.validate_on_submit():
        user = UserAccount.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
#            return redirect(next_page) if next_page else redirect(url_for('home'))
            return redirect(next_page) if next_page else redirect(url_for('showsites'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = UserAccount(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
#        return redirect(url_for('home'))
        return redirect(url_for('showsites'))
    form = LoginForm()
    if form.validate_on_submit():
        user = UserAccount.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
#            return redirect(next_page) if next_page else redirect(url_for('home'))
            return redirect(next_page) if next_page else redirect(url_for('showsites'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
#            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
#    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                            form=form)

############################################################
# Purpose: Save new site into db. After validation in form
#
# 1. post is now site
#
@app.route("/site/new", methods=['GET', 'POST'])
@login_required
def new_site():
    form = PostForm()
    if form.validate_on_submit():
        print("New Site saving in db ")
        print(current_user.id)
        #user_id = session["user_id"]
#        post = Post(title=form.title.data, date_posted='2016-06-22 19:10:25-07', content=form.content.data, user_id=current_user.id)
        site = Site(user_id=current_user.id,site_name=form.title.data, site_contact_details=form.content.data)

        db.session.add(site)
        db.session.commit()
        flash('Your New Site has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_site.html', title='Add New Site',
                           form=form, legend='Add New Site')

#
#  show post given id
#
@app.route("/post/<int:post_id>")
def post(post_id):
    print("post route, show post given id")
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user:
        abort(403)
    # updated form to not show button "Add this as a new site"    
    form = PostForm_Update()               
    if form.validate_on_submit():

        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    print("Start delete_post route ")
    post = Post.query.get_or_404(post_id)

##   We were checking that the person deleting the post was the post owner
##   but it looks like we are comparing 1 to User 1

#    if post.user_id != current_user:
#        print("User is not current_user ?? ")
#        print("current_user is")
#        print(current_user)
#        print("user id is")
#        print(post.user_id )
#        abort(403)

    try:    
        db.session.delete(post)
        db.session.commit()
        print("commit delete request - success  ")

        flash('Your post has been deleted!', 'success')
    except:
        print("Cant commit delete request - FAIL   ")
        return 'There was an issue deleting your post'

    return redirect(url_for('home'))

@app.route("/showsites", methods=['GET', 'POST'])
@login_required
def showsites():
    form = ShowSitesForm()
 #   form.username.data = current_user.username

    sites = Site.query.filter_by(user_id=current_user.id)
    
    print(" /showsites -> Current User id is: ")
    print(current_user.id)

    return render_template('showsites.html', sites=sites, form=form)

 #   return render_template('account.html', title='Account',
 #                          image_file=image_file, form=form)

#@app.route('/adddevice',methods=['GET','POST'])
#@login_required
#def add_device():
 #    form = AddDevice()
 #    if form.validate_on_submit():
#    if request.method == 'POST':
#        # get the selected option, from the form
#        choice= request.form.get("radio_option")   # this will get the value string at the option chosen

        # create a new class object matching the database table
        # elements we want to add.
#        print("The Choice was: ")
#        print(choice)
#    else:
#        print("Method NOT post ")
#        thing = ''
#        return render_template('adddevice.html',thing=thing)


@app.route("/adddevice/<int:site_id>", methods=['POST', 'GET'])
def add_device(site_id):      # site_id is the name of the foreign key (pointing at site table) in the Device table
#@app.route("/adddevice", methods=['POST', 'GET'])
#def add_device():
        
#    print("Site id foreign key is ")
#    print(site.id)
    
    temp = int(3)    # use temporarily to get record saved below

    if request.method == 'POST':
        print("POST request ")
#        thing = ''
#        return render_template('adddevice.html', thing=thing)

        phone_number=request.form['SIM_Phone_Number']
        print("Device Phone NUmber ")
        print(phone_number)
        name=request.form['Local_Name']
        print("Device Local Name ")
        print(name)    
        # device_type_name = request.form['radio_option']

        # print("Device Type name ")

        device_type_name = temp

        print("Device Type name ")

        print(device_type_name)
        print("Site id foreign key is ")
        print(site_id)


        device = Device(site_id=site_id,device_type_name=device_type_name, device_sim_number=phone_number, access_point_name=name )
                
        try:
            db.session.add(device)
            db.session.commit()
#            return redirect('/devicesettings.html')
            thing = ''
            #return render_template('adddevice.html', site_id=site.id)
            print("Your New Device has been saved for Site with id: ")
            print(site_id)
            #return render_template('devicesettings.html')
            #return render_template('devicesettings.html', device_id=device_id, phone_numbers=phone_numbers)
            return 'Your New device has been created'

        except:
            return 'There was an issue adding your New Device'
            #thing = ''
            #return render_template('adddevice.html', site_id=site.id)
            return render_template('devicesettings.html', device_id=device_id, phone_numbers=phone_numbers)

    else:
        print("Method NOT post ")
        #thing = ''
        #return render_template('adddevice.html',thing=thing)
        #return render_template('devicesettings.html')
        return  render_template('adddevice.html', site_id=site_id)


@app.route('/devicesettings_id',methods=['GET','POST'])
@login_required
def device_settings_id():
    return render_template('devicesettings_id.html')

######################################################
# Purpose: 1)  Display devicesettings.html
#          2) If we get a SUbmit button press "Add User"
#             then we add the new record to the database.
#
#
@app.route('/devicesettings/<int:device_id>',methods=['GET','POST'])
@login_required
def device_settings(device_id):
    if request.method == 'POST':
        print("devicesettings - POST ") 
        # get the two new fields from the form
        device_new_name = request.form['content_name']
        device_new_number = request.form['content_number']
        # create a new class object matching the database table
        # elements we want to add.
        print("New Name saving in db, name ")
        print(device_new_name)
        print("New Phone NUmber saving in db, Number ")
        print(device_new_number)
        print("device id saving in db, Number ")
        print(device_id)
#        new_task = Post(title=device_new_name, content=device_new_number)

#        user = User(title=device_new_name, date_posted='2016-06-22 19:10:25-07', content=device_new_number, user_id=current_user.id)
 
        phone_number = PhoneNumber(device_id=device_id, phone_number=device_new_number, user_name=device_new_name)
 

        try:
            db.session.add(phone_number)
            db.session.commit()
            flash('Your New Device Phone NUmber details has been created!', 'success')
            # having added device phone numbers to db now get them all and show the updated list 
            phone_numbers = PhoneNumber.query.filter_by(device_id=device_id)
            return render_template('devicesettings.html', device_id=device_id, phone_numbers=phone_numbers, page='open_number')

        except:
            return 'There was an issue adding your Device details, '

    else:
        print("devicesettings - GET ")        
        phone_numbers = PhoneNumber.query.filter_by(device_id=device_id)
#        phone_number = PhoneNumber.query.all()
        return render_template('devicesettings.html', device_id=device_id, phone_numbers=phone_numbers, page='open_number')

@app.route('/call-function') 
def call_function(): 
    return my_function() 


@app.route("/phonenumber/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_phone_number(id):
    print("Start delete_post route ")
    phonenum = PhoneNumber.query.get_or_404(id)

##   We were checking that the person deleting the post was the post owner
##   but it looks like we are comparing 1 to User 1

#    if post.user_id != current_user:
#        print("User is not current_user ?? ")
#        print("current_user is")
#        print(current_user)
#        print("user id is")
#        print(post.user_id )
#        abort(403)

    try:    
        db.session.delete(phonenum)
        db.session.commit()
        print("commit delete request - success  ")

        flash('Your Phone Number has been deleted!', 'success')
    except:
        print("Cant commit delete request - FAIL   ")
        return 'There was an issue deleting your phone number'

    return redirect(url_for('home'))

#
#  show site given id
#
@app.route("/site/<int:site_id>")
def site(site_id):
    print("site route, show site given id")
    site = Site.query.get_or_404(site_id)
    return render_template('site.html', title=site.site_name , site=site)


@app.route("/site/<int:site_id>/update", methods=['GET', 'POST'])
@login_required
def update_site(site_id):
    site = Site.query.get_or_404(site_id)
    if site.user_id != current_user:
        abort(403)
    # updated form to not show button "Add this as a new site"    
    form = SiteForm_Update()               
    if form.validate_on_submit():

        site.site_name = form.title.data
        site.site_contact_details  = form.content.data
        db.session.commit()
        flash('Your site has been updated!', 'success')
        return redirect(url_for('site', site_id=site.id))
    elif request.method == 'GET':
        form.title.data = site.site_name
        form.content.data = site.site_contact_details
    return render_template('create_site.html', title='Update Site',
                           form=form, legend='Update Site')


@app.route("/site/<int:site_id>/delete", methods=['POST'])
@login_required
def delete_site(site_id):
    print("Start delete_site route ")
    site = Site.query.get_or_404(post_id)

##   We were checking that the person deleting the post was the post owner
##   but it looks like we are comparing 1 to User 1

#    if post.user_id != current_user:
#        print("User is not current_user ?? ")
#        print("current_user is")
#        print(current_user)
#        print("user id is")
#        print(post.user_id )
#        abort(403)

    try:    
        db.session.delete(site)
        db.session.commit()
        print("commit delete request - success  ")

        flash('Your site has been deleted!', 'success')
    except:
        print("Cant commit delete request - FAIL   ")
        return 'There was an issue deleting your site'

    return redirect(url_for('home'))


#
#  show devices given site id
#
# The top row lists a .html page. SO make sure .html page defined.
@app.route("/showdevices/<int:site_id>")
def show_device(site_id):
    form = ShowDevicesForm()
    if form.validate_on_submit():
       print("device route, show devices given site id - POST")
       print(site_id)

       return redirect(url_for('home'))

    elif request.method == 'GET':
       print("showdevices route, show devices given site id - GET")
       devices = Device.query.filter_by(site_id=site_id)
       return render_template('showdevices.html',site=site, site_id=site_id, devices=devices, form=form)



#@app.route("/showdevices/<int:site_id>")
#def show_device(site_id):
#    print("device route, show device given site id")
#    print(site_id)
#    form = ShowSitesForm()
 
#    sites = Site.query.all()
# 
#    device = Device.query.get_or_404(site_id)
#    return render_template('showdevices.html', site=site, form=form)    


#########################################################################################
#  Device Routes........................................................................#
#########################################################################################


## Function to Convert Phone Number to String

# This function takes a phone number as input, handles various formats, and converts it into a standardized string representation. It also addresses invalid input gracefully.

import re

def phone_number_to_string(phone_number):
  #  """Converts a phone number to a string, handling different formats.

 #   Args:
 #       phone_number (str): The phone number to convert.

 #   Returns:
 #       str: The standardized phone number string, or an error message if invalid.
 #   """
    if not isinstance(phone_number, str):
        return "Error: Input must be a string."

    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone_number)

    # Check for valid length after removing non-digits
    if not 7 <= len(digits_only) <= 15: # covers most cases, including with country code
        return "Error: Invalid phone number length."

    # Standardize the format (example: +1-555-555-5555)
    if len(digits_only) == 10:  # US number without country code
        return f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
    elif len(digits_only) == 11: # US number with country code
        return f"+{digits_only[0]}-{digits_only[1:4]}-{digits_only[4:7]}-{digits_only[7:]}"
    else:
        return digits_only # Return as is if the formatting doesn't match, but is still valid length


# Example Usage:
#print(phone_number_to_string("123-456-7890"))  # Output: 123-456-7890
#print(phone_number_to_string("+1-555-123-4567")) # Output: +1-555-123-4567
#print(phone_number_to_string("5551234"))      # Output: 5551234
#print(phone_number_to_string("invalid"))      # Output: Error: Invalid phone number length.
#print(phone_number_to_string(1234567890))     # Output: Error: Input must be a string.





@app.route("/home2")
def home2():
    return redirect(url_for('home'))


######################################################
# Purpose: 1)  A first test from the Device to get details 
#              from the database on the first device in the 
#              device table
#          2) this is how i got it from psql command line db interface
#          select * from device where id =1;  
#

@app.route("/getfirstdevice/<int:device_id_in>", methods=['GET', 'POST'])
def getfirstdevice(device_id_in):
        print("getfirstdevice - Get - details first device ") 
        phones = PhoneNumber.query.filter_by(device_id=device_id_in)
        for phone in phones:
           print(str(phone))
        print(type(phone))        
        
        phone = phones[0] 

#        str_phone = phone_number_to_string(phone)
        str_phone = str(phone)
        print(type(str_phone))
        print(str_phone)
        return(str_phone)
        



######################################################
# Purpose: 1)  A first test from the Device to get details 
#              from the database on the first device in the 
#              device table
#          2) this is how i got it from psql command line db interface
#          select * from device where id =1;  
#

@app.route("/get_first_device/<int:device_id_in>", methods=['GET'])
def get_first_device(device_id_in):
        print("get_first_device - Get - start ") 
        phones = PhoneNumber.query.filter_by(device_id=device_id_in)
        for phone in phones:
           print(str(phone))
        print(type(phone))        
        
        phone = phones[0] 

#        str_phone = phone_number_to_string(phone)
        str_phone = str(phone)
        print(type(str_phone))
        print(str_phone)
        return(str_phone)

######################################################
# Purpose: 1)  A first test using jsonify
# 

@app.route("/test", methods=['GET'])
def test():
    return jsonify({'msg': 'Hello World'})

