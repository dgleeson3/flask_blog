import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy import create_engine
import sqlalchemy as sa
from os import environ


# now interfacing to postgresql db vgr_13db ( 181124 )
# https://stackoverflow.com/questions/62113733/how-connect-postgresql-database-with-sqlalchemy-python
# https://stackoverflow.com/questions/62688256/sqlalchemy-exc-nosuchmoduleerror-cant-load-plugin-sqlalchemy-dialectspostgre
app = Flask(__name__)
#                                           driver://user:pass@localhost/dbname

# Now defined as an environment variable.
# this is what we use on the development machine.
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dgleeson3:access45@localhost/vgr_12db'

# this is what we are using on Render to point at the database
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('SQLALCHEMY_DATABASE_URI')

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

# For hosting in Render I need to initalise the database
# check if it needs to be initalised first.
# https://testdriven.io/blog/flask-render-deployment/
# https://gitlab.com/patkennedy79/flask_user_management_example/-/blob/2be600d0bfd5a28957b4961bcb2a6607a9c07b08/project/__init__.py#L42
# Check if the database needs to be initialized
engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
inspector = sa.inspect(engine)
if not inspector.has_table("user_accounts"):
    print("Init the db ")
    with app.app_context():
        db.drop_all()
        db.create_all()
        app.logger.info('Initialized the database!')
else:
    print("  db  already initalised ")
    app.logger.info('Database already contains the user_accounts table.')
