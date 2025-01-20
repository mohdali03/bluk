from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

ma = Marshmallow()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    rollNo = db.Column(db.Integer, unique = True)
    std = db.Column(db.String(100))
    course = db.Column(db.String(100))
    
    def __init__(self, name, rollNo, std, course):
         self.name = name 
         self.rollNo = rollNo 
         self.std = std 
         self.course = course 


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), nullable= False)
    email = db.Column(db.String(100), nullable=False)
    _password = db.Column(db.String(150))
    
    @property
    def password(self):
        raise AttributeError("can't read the password")
    
    @password.setter
    def password(self, password):
        self._password = generate_password_hash(password)
            
        
    def __init__(self,username, email, password):
        self.username = username
        self.email = email
        self.password = password
    # @staticmethod
    def checkPassword(self, password):
        
        return check_password_hash(self._password, password )

class StudentScheme(ma.Schema):
    class Meta: # type:ignore
        fields = ("name", 'rollNo', 'std', 'course')