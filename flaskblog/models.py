# coding: utf-8
from flask_sqlalchemy import SQLAlchemy
from flaskblog import db, login_manager, ma
from flask_login import UserMixin



@login_manager.user_loader
def load_user(user_id):
    return UserAccount.query.get(int(user_id))
    #return User.objects(pk=user_id).first()


class CallOutPhoneNumber(db.Model):
    __tablename__ = 'call_out_phone_numbers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'))
    phone_number = db.Column(db.String)
    user_name = db.Column(db.String)

    device = db.relationship('Device', primaryjoin='CallOutPhoneNumber.device_id == Device.id', backref='call_out_phone_numbers')



class ConfigMisc(db.Model):
    __tablename__ = 'config_misc'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'))
    security_code_enabled = db.Column(db.Boolean)
    security_code = db.Column(db.String)
    gate_lock_on = db.Column(db.Boolean)
    pulse_time = db.Column(db.String)

    device = db.relationship('Device', primaryjoin='ConfigMisc.device_id == Device.id', backref='config_miscs')

############################################
# Device db table
#
# 1) added unique_device_identifier to allow the device to find 
#    
# its configuration inside the database

class Device(db.Model):
    __tablename__ = 'device'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_type_name = db.Column(db.Integer)
    device_sim_number = db.Column(db.String)
    access_point_name = db.Column(db.String)
    unique_device_identifier = db.Column(db.String)
    site_id = db.Column(db.ForeignKey('site.id'))

    site = db.relationship('Site', primaryjoin='Device.site_id == Site.id', backref='devices')

#device schema for Marshmallow
class DeviceSchema(ma.Schema):
    class Meta:
        fields = ('id','device_type_name','device_sim_number','access_point_name','unique_device_identifier','site_id')

#init schema, define variables,
# note there used to be a strict=True setting but it is now obsolete, all schemas are strict
device_schema = DeviceSchema()
devices_schema = DeviceSchema(many=True)



class KeypadCode(db.Model):
    __tablename__ = 'keypad_code'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'))
    key_code = db.Column(db.String)

    device = db.relationship('Device', primaryjoin='KeypadCode.device_id == Device.id', backref='keypad_codes')



class OutOfHour(db.Model):
    __tablename__ = 'out_of_hours'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'))
    out_of_hours_enabled = db.Column(db.Boolean)
    start_time = db.Column(db.String)
    end_time = db.Column(db.String)
    days = db.Column(db.String)
    alternative_phone_no = db.Column(db.String)

    device = db.relationship('Device', primaryjoin='OutOfHour.device_id == Device.id', backref='out_of_hours')

#
# CALL IN Phone Numbers
#
class PhoneNumber(db.Model):
    __tablename__ = 'phone_number'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.ForeignKey('device.id'))
    phone_number = db.Column(db.String)
    user_name = db.Column(db.String)

    device = db.relationship('Device', primaryjoin='PhoneNumber.device_id == Device.id', backref='phone_numbers')

#device schema for Marshmallow
class PhoneNumberSchema(ma.Schema):
    class Meta:
        fields = ('id','device_id','phone_number','user_name')

#init schema, define variables,
# note there used to be a strict=True setting but it is now obsolete, all schemas are strict
phone_number_schema = PhoneNumberSchema()
phone_numbers_schema = PhoneNumberSchema(many=True)




class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, unique=True)
    date_posted = db.Column(db.DateTime)
    content = db.Column(db.String)
    user_id = db.Column(db.ForeignKey('user_accounts.id'))

    user = db.relationship('UserAccount', primaryjoin='Post.user_id == UserAccount.id', backref='posts')



class Site(db.Model):
    __tablename__ = 'site'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.ForeignKey('user_accounts.id'))
    site_name = db.Column(db.String)
    site_contact_details = db.Column(db.String)

    user = db.relationship('UserAccount', primaryjoin='Site.user_id == UserAccount.id', backref='sites')



class UserAccount(db.Model, UserMixin):
    __tablename__ = 'user_accounts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, unique=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
    image_file = db.Column(db.String)
