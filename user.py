from werkzeug.security import check_password_hash
from flask_login import UserMixin

class User(UserMixin):  # 👈 Inherit from UserMixin
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.is_admin = False

    def get_id(self):
        return self.username

    def check_password(self, password_input):
        return check_password_hash(self.password, password_input)
