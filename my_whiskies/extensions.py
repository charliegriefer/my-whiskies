from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
login = LoginManager()
login.login_view = "auth.login"
login.login_message = "Please log in to access this page."
mail = Mail()
migrate = Migrate()
