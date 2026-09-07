# -*- coding: utf-8 -*-
# Importing necessary modules for database functionality and user session management
from flask_sqlalchemy import SQLAlchemy
from flaskblog import db, login_manager
from flask_login import UserMixin

# -----------------------------------------------------------------------------
# User Loader function for Flask-Login
# This function tells Flask-Login how to load a user from a user_id.
# -----------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    # Look up and return the user by their unique identifier from the database.
    return UserAccount.query.get(int(user_id))
    # Alternative implementation (commented out):
    # return User.objects(pk=user_id).first()

# -----------------------------------------------------------------------------
# Database Model: CallOutPhoneNumber
# This model maps to the 'call_out_phone_numbers' table and holds contact information 
# for call-out phone numbers, along with associated device and order details.
# -----------------------------------------------------------------------------
class CallOutPhoneNumber(db.Model):
    __tablename__ = 'call_out_phone_numbers'

    # Primary key with auto-increment
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key that links to the 'device' table
    device_id = db.Column(db.ForeignKey('device.id'))
    
    # Holds the phone number data as a string
    phone_number = db.Column(db.String)
    
    # User name associated with the phone number
    user_name = db.Column(db.String)
    
    # Order in which phone numbers are arranged (default is 0)
    order = db.Column(db.Integer, default=0)
    
    # Button and apartment device indicators (default value 0)
    button_device = db.Column(db.Integer, default=0)
    apartment_device = db.Column(db.Integer, default=0)

    # Establishing relationship with the Device model based on the foreign key.
    device = db.relationship('Device', primaryjoin='CallOutPhoneNumber.device_id == Device.id', 
                             backref='call_out_phone_numbers')


# -----------------------------------------------------------------------------
# Database Model: ConfigMisc
# This model represents miscellaneous configuration settings for a device.
# It includes security options, timing configurations, and more.
# -----------------------------------------------------------------------------
class ConfigMisc(db.Model):
    __tablename__ = 'config_misc'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'))
    
    # Indicates if the security code feature is enabled
    security_code_enabled = db.Column(db.Boolean)
    
    # The security code as a string
    security_code = db.Column(db.String)
    
    # Option to turn on a gate lock
    gate_lock_on = db.Column(db.Boolean)
    
    # Pulse time configuration as a string (could be formatted time or duration)
    pulse_time = db.Column(db.String)
    
    # Define the relationship with the Device model.
    device = db.relationship('Device', primaryjoin='ConfigMisc.device_id == Device.id', 
                             backref='config_miscs')


# -----------------------------------------------------------------------------
# Database Model: Device
# This model represents a device entity and is linked to other tables (Sites, Configurations, etc.).
# It includes attributes such as device type, contact details, timing parameters, security settings, 
# and an array of names for buttons or apartments.
# -----------------------------------------------------------------------------
class Device(db.Model):
    __tablename__ = 'device'
    
    # Primary key with auto-increment
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Device type as a string. Used to categorize or compare devices.
    device_type_name = db.Column(db.String)
    
    # SIM number associated with the device.
    device_sim_number = db.Column(db.String)
    
    # Access point name, possibly indicating network-related information.
    access_point_name = db.Column(db.String)
    
    # Foreign key linking to a Site (location or customer) where the device is installed.
    site_id = db.Column(db.ForeignKey('site.id'))
    
    # URL for the device's image; provides a default image if none is set.
    photo_url = db.Column(db.String(255), default='../static/profile_pics/switch4G_portfolio.png')
    
    # Timing attributes for device operation:
    pulse_time = db.Column(db.Integer, default=3)
    ring_time = db.Column(db.Integer, default=20)
    talk_time = db.Column(db.Integer, default=40)
    
    # Security settings for the device, including code activation and default code.
    security_code_enable = db.Column(db.Boolean, default=False)
    security_code = db.Column(db.String, default='8531')
    
    # Attributes to handle numbers related to buttons and apartments
    number_button = db.Column(db.Integer, default=0)
    number_apartment = db.Column(db.Integer, default=0)
    
    # A JSON column to hold an array of names, for example labels for buttons or apartments.
    names_array = db.Column(db.JSON)
    
    # Define relationship with Site (each device is linked to one site).
    site = db.relationship('Site', primaryjoin='Device.site_id == Site.id', backref='devices')
    
    def __init__(self, device_type_name, **kwargs):
        """
        Custom initializer for Device.
        
        Parameters:
            device_type_name (str): The type of device as a string.
            **kwargs: Additional keyword arguments for other fields.
            
        Depending on the device type, the names_array field is initialized with a list
        of default names. For example, certain intercoms have preset numbers of buttons.
        """
        # Initialize parent class with other provided keyword arguments
        super().__init__(**kwargs)
        self.device_type_name = device_type_name
        
        # Depending on the device type, set the names_array field:
        if self.device_type_name in ["Voyager Voice 2 button Intercom", "Voyager Voice 4 button Intercom"]:
            # If the device is one of these intercom types, initialize with 5 default names.
            self.names_array = [f"Name {i+1}" for i in range(5)]
        elif self.device_type_name == "Voyager Voice Appartment Intercom":
            # If the device is an apartment intercom, initialize with 50 default names.
            self.names_array = [f"Name {i+1}" for i in range(50)]
        else:
            # For other types, explicitly set names_array to None.
            self.names_array = None


# -----------------------------------------------------------------------------
# Database Model: KeypadCode
# This model represents access codes for keypads associated with a device.
# It includes fields for code type, applicable days/times, and temporary code durations.
# -----------------------------------------------------------------------------
class KeypadCode(db.Model):
    __tablename__ = 'keypad_code'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'))
    
    # The actual key code used for access.
    key_code = db.Column(db.String)
    
    # A string indicating the type of code (e.g., temporary, permanent)
    code_type = db.Column(db.String)
    
    # Comma-separated list of days when this code is valid (if applicable)
    days = db.Column(db.String)
    
    # Start time for the code's validity period
    start_time = db.Column(db.String)
    
    # End time for the code's validity period
    end_time = db.Column(db.String)
    
    # Output configuration associated with the key code
    output = db.Column(db.String)
    
    # Temporary days duration for temporary codes as an integer value
    temp_days = db.Column(db.Integer)
    
    # Define relationship with the Device model.
    device = db.relationship('Device', primaryjoin='KeypadCode.device_id == Device.id', 
                             backref='keypad_codes')


# -----------------------------------------------------------------------------
# Database Model: OutOfHour
# This model contains settings for out-of-hours operations, including
# alternative contact numbers and time ranges.
# -----------------------------------------------------------------------------
class OutOfHour(db.Model):
    __tablename__ = 'out_of_hours'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'))
    
    # Whether out-of-hours functionality is enabled
    out_of_hours_enabled = db.Column(db.Boolean)
    
    # The start and end times defining out-of-hours
    start_time = db.Column(db.String)
    end_time = db.Column(db.String)
    
    # Comma-separated days string during which out-of-hours are applicable
    days = db.Column(db.String)
    
    # An alternative phone number to contact during out-of-hours
    alternative_phone_no = db.Column(db.String)

    # Relationship with the Device model.
    device = db.relationship('Device', primaryjoin='OutOfHour.device_id == Device.id', 
                             backref='out_of_hours')


# -----------------------------------------------------------------------------
# Database Model: PhoneNumber
# This model stores phone number records linked to a device with associated output settings.
# -----------------------------------------------------------------------------
class PhoneNumber(db.Model):
    __tablename__ = 'phone_number'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'))
    
    # The phone number as a string.
    phone_number = db.Column(db.String)
    
    # The user name linked to the phone number.
    user_name = db.Column(db.String)
    
    # Output field with a server default value of '1'
    output = db.Column(db.Integer, server_default='1')

    # Relationship with the Device model.
    device = db.relationship('Device', primaryjoin='PhoneNumber.device_id == Device.id', 
                             backref='phone_numbers')


# -----------------------------------------------------------------------------
# Database Model: AutomaticSchedule
# This model defines an automatic schedule for a device, including timing and days configuration.
# -----------------------------------------------------------------------------
class AutomaticSchedule(db.Model):
    __tablename__ = 'automatic_schedule'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'))
    
    # Output configuration for the schedule, with default value '1'
    output = db.Column(db.Integer, server_default='1')
    
    # The start and end times for the schedule period.
    start_time = db.Column(db.String)
    end_time = db.Column(db.String)
    
    # Number of days (stored as an integer) for schedule recurrence.
    days = db.Column(db.Integer)
    
    # Additional schedule details as a string (possibly representing a range or list of days)
    n_days = db.Column(db.String)
    
    # Define relationship with the Device model.
    device = db.relationship('Device', primaryjoin='AutomaticSchedule.device_id == Device.id', 
                             backref='automatic_schedule')


# -----------------------------------------------------------------------------
# Database Model: Post
# This model defines a blog post or similar content piece with a title, content, and associated user.
# -----------------------------------------------------------------------------
class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # The title of the post, must be unique.
    title = db.Column(db.String, unique=True)
    
    # The date and time when the post was created.
    date_posted = db.Column(db.DateTime)
    
    # The main content of the post as a string.
    content = db.Column(db.String)
    
    # Foreign key linking the post to a user in the UserAccount table.
    user_id = db.Column(db.ForeignKey('user_accounts.id'))

    # Relationship with the UserAccount model.
    user = db.relationship('UserAccount', primaryjoin='Post.user_id == UserAccount.id', 
                           backref='posts')


# -----------------------------------------------------------------------------
# Database Model: Site
# This model represents a site or location which can have multiple devices and posts.
# -----------------------------------------------------------------------------
class Site(db.Model):
    __tablename__ = 'site'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key linking a site to a user account (typically the owner or administrator)
    user_id = db.Column(db.ForeignKey('user_accounts.id'))
    
    # The name of the site.
    site_name = db.Column(db.String)
    
    # Contact details for the site.
    site_contact_details = db.Column(db.String)

    # Relationship with the UserAccount model.
    user = db.relationship('UserAccount', primaryjoin='Site.user_id == UserAccount.id', 
                           backref='sites')


# -----------------------------------------------------------------------------
# Database Model: UserAccount
# This model defines a user account used for authentication and content management,
# integrating with Flask-Login through UserMixin.
# -----------------------------------------------------------------------------
class UserAccount(db.Model, UserMixin):
    __tablename__ = 'user_accounts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Email must be unique for each user
    email = db.Column(db.String, unique=True)
    
    # The user's username
    username = db.Column(db.String)
    
    # The user's hashed password
    password = db.Column(db.String)
    
    # Path to the user's profile image
    image_file = db.Column(db.String)
    
    # Indicates whether the user has administrator privileges
    administrator = db.Column(db.Boolean,  default=False)


# -----------------------------------------------------------------------------
# Database Model: CurrentDiagnostics
# This model stores diagnostic data that represents the current state of a device,
# including software version and various count metrics for issues.
# -----------------------------------------------------------------------------
class CurrentDiagnostics(db.Model):
    __tablename__ = 'current_diagnostics'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'), nullable=False)
    
    # Device type and software version fields
    device_type = db.Column(db.String(50), nullable=False)
    sw_version = db.Column(db.String(50), nullable=False)
    
    # Counters for various diagnostic issues
    count_signal_strength_too_low = db.Column(db.Integer, default=0)
    count_not_checking_signal_strength = db.Column(db.Integer, default=0)
    count_cannot_register = db.Column(db.Integer, default=0)
    count_os_problem = db.Column(db.Integer, default=0)
    count_state_stuck = db.Column(db.Integer, default=0)
    
    # The date of the diagnostic reading (stored as a string)
    date_diag = db.Column(db.String(50), nullable=True)

    # Relationship with the Device model with cascade deletion options.
    device = db.relationship(
        'Device',
        primaryjoin='CurrentDiagnostics.device_id == Device.id',
        backref=db.backref('current_diagnostics', cascade='all, delete-orphan')
    )


# -----------------------------------------------------------------------------
# Database Model: LiveDiagnostics
# This model captures real-time diagnostic data for devices, including signal strength,
# relay states, and the associated phone number for the device.
# -----------------------------------------------------------------------------
class LiveDiagnostics(db.Model):
    __tablename__ = 'live_diagnostics'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'), nullable=False)
    
    # Real-time device information: type, software version, instantaneous metrics, etc.
    device_type = db.Column(db.String(50), nullable=False)
    sw_version = db.Column(db.String(50), nullable=False)
    instantaneous_band = db.Column(db.String(50), nullable=True)
    instantaneous_signal_strength = db.Column(db.Float, nullable=True)
    
    # State data for device relays (could be 'on'/'off' or similar state values)
    state_of_relay_1 = db.Column(db.String(50), nullable=True)
    state_of_relay_2 = db.Column(db.String(50), nullable=True)
    
    # The date of the diagnostic reading
    date_diag = db.Column(db.String(50), nullable=True)
    
    # Phone number stored in the device for additional diagnostics or contacts
    stored_device_phone_number = db.Column(db.String(20), nullable=True)
    
    # Define relationship with the Device model with cascade deletion options.
    device = db.relationship(
        'Device',
        primaryjoin='LiveDiagnostics.device_id == Device.id',
        backref=db.backref('live_diagnostics', cascade='all, delete-orphan')
    )
