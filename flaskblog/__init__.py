import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate


# now interfacing to postgresql db vgr_6db ( 180824 )
# https://stackoverflow.com/questions/62113733/how-connect-postgresql-database-with-sqlalchemy-python
# https://stackoverflow.com/questions/62688256/sqlalchemy-exc-nosuchmoduleerror-cant-load-plugin-sqlalchemy-dialectspostgre
app = Flask(__name__)
#                                           driver://user:pass@localhost/dbname
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dgleeson3:access45@localhost/vgr_12db'

app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
db = SQLAlchemy(app)
# After the db declaration, you use the Migrate class to initiate a migration instance called migrate,
#  passing it to the Flask app instance and the db database instance.
migrate = Migrate(app,db)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
# needed this placed here to allow site to run
from flaskblog import routes
