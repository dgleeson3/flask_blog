from flaskblog import app
from flaskblog import db


if __name__ == '__main__':
  with app.app_context():
    db.create_all()    
    app.run(debug=True)
#    app.run(host='0.0.0.0', port=80, debug=True)


