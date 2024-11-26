# coding: utf-8
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flaskblog import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User_Accounts.query.get(int(user_id))
    #return User.objects(pk=user_id).first()


class Device(db.Model):
    __tablename__ = 'device'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    site_id = db.Column(db.ForeignKey('site.id'))
    device_type_name = db.Column(db.Integer)
    device_sim_number = db.Column(db.String)
    access_point_name = db.Column(db.String)

    site = db.relationship('Site', primaryjoin='Device.site_id == Site.id', backref='devices')

##################################################
# class for DeviceType()   removed 2/10/24
#  It was just overcomplicated. Just need 'Device' table
#
#class DeviceType(db.Model):
#    __tablename__ = 'device_type'

#    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
#    device_id = db.Column(db.ForeignKey('device.id'))
#    device_type_name = db.Column(db.Integer)
#    device_sim_number = db.Column(db.String)
#    access_point_name = db.Column(db.String)

#    device = db.relationship('Device', primaryjoin='DeviceType.device_id == Device.id', backref='device_types')



class KeypadCode(db.Model):
    __tablename__ = 'keypad_code'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    device_id = db.Column(db.ForeignKey('device.id'))
    key_code = db.Column(db.String)

    device = db.relationship('Device', primaryjoin='KeypadCode.device_id == Device.id', backref='keypad_codes')



class OpenNumberWhiteList(db.Model):
    __tablename__ = 'open_number_white_list'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    device_id = db.Column(db.ForeignKey('device.id'))
    country_code = db.Column(db.String)
    name = db.Column(db.String)

    device = db.relationship('Device', primaryjoin='OpenNumberWhiteList.device_id == Device.id', backref='open_number_white_lists')



class OutOfHour(db.Model):
    __tablename__ = 'out_of_hours'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    device_id = db.Column(db.ForeignKey('device.id'))
    country_code = db.Column(db.String)
    name = db.Column(db.String)

    device = db.relationship('Device', primaryjoin='OutOfHour.device_id == Device.id', backref='out_of_hours')



class PhoneNumber(db.Model):
    __tablename__ = 'phone_number'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    device_id = db.Column(db.ForeignKey('device.id'))
    phone_number = db.Column(db.String)
    user_name = db.Column(db.String)

    device = db.relationship('Device', primaryjoin='PhoneNumber.device_id == Device.id', backref='phone_numbers')

class ConfigMisc(db.Model):    
    __tablename__ = 'config_misc'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    device_id = db.Column(db.ForeignKey('device.id'))

    security_code_enabled = db.Column(db.Boolean, unique=True)
    security_code = db.Column(db.String)
    gate_lock_on = db.Column(db.Boolean)
    pulse_time = db.Column(db.String)

    user = db.relationship('Device', primaryjoin='ConfigMisc.device_id == Device.id', backref='config_misc')


class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    title = db.Column(db.String, unique=True)
    date_posted = db.Column(db.DateTime)
    content = db.Column(db.String)
    user_id = db.Column(db.ForeignKey('user_accounts.id'))

    user_accounts = db.relationship('User_Accounts', primaryjoin='Post.user_id == User_Accounts.id', backref='posts')



class Site(db.Model):
    __tablename__ = 'site'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    user_id = db.Column(db.ForeignKey('user_accounts.id'))
    site_name = db.Column(db.String)
    site_contact_details = db.Column(db.String)

    user_accounts = db.relationship('User_Accounts', primaryjoin='Site.user_id == User_Accounts.id', backref='sites')


class User_Accounts(db.Model, UserMixin):    
    __tablename__ = 'user_accounts'

#    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, unique=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
    image_file = db.Column(db.String)
