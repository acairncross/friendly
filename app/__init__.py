from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# app.jinja_options = {
#     'extensions': ['jinja2.ext.autoescape', 'jinja2.ext.with_'],
#     'trim_blocks': True,
#     'lstrip_blocks': True
# }

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import views
