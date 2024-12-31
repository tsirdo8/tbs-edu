from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

# Configure login manager
login_manager.login_view = 'login'
login_manager.login_message = 'გთხოვთ გაიაროთ ავტორიზაცია ამ გვერდის სანახავად.'
login_manager.login_message_category = 'info'
