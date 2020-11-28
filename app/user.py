from werkzeug.security import check_password_hash
from functools import wraps


class User():

    def __init__(self, username,password,urole):
        self.username = username
        self.password = password
        self.urole = urole
        #self.email = email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    def get_role(self):
        return self.urole

    @staticmethod
    def validate_login(password_db, password_ip):
        if password_db==password_ip:
            return True
        return False

        
