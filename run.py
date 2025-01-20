from flask import Flask, flash, jsonify, make_response, redirect, request, session, url_for, render_template
from models import db, Student, StudentScheme, User
from fileupload import csvUpload, excelUpload
from functools import wraps
import jwt
import datetime

app = Flask(__name__, template_folder='template', static_folder='static')

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "ThisisSecretKey"
db.init_app(app)

studentsScheme = StudentScheme(many=True)
studentScheme = StudentScheme()

ALLOWED_EXTENSIONS = {'xlsx', 'csv'}


def allowedfile(filename):
    return "." in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

with app.app_context():
    db.create_all()
    # db.drop_all()


def token_required(f):
    @wraps(f)
    def docorated(*args, **kwargs):
        token = request.cookies.get('currentUser')
        print(token)
        
        if not token:
            flash('Please login to Access this page', 'danger')
            return redirect(url_for('login'))
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            currentUser = User.query.get(data['user.id'])
            if not currentUser or currentUser.id != session['user.id']:
                res = make_response('cookie deleted')
                res.set_cookie('currentUser', '', expires=0)
                session.pop('user.id', None)
                session.clear()
                flash('token is invalid', 'danger')
                return redirect(url_for('login'))
        except jwt.ExpiredSignatureError:
            flash('Token has expired. Please log in again.', 'danger')
            return redirect(url_for('login'))
        except jwt.InvalidTokenError:
            flash('Invalid token. Please log in again.', 'danger')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'token is {str(e)}', 'danger')
            return redirect(url_for('login'))
        
        return f(currentUser)
    return docorated

@app.route('/', methods= ["GET", "POST"])
# @token_required
def home():
    allStudent = Student.query.all()
    # return studentsScheme.jsonify(allStudent)
    return render_template('home.html', student = allStudent)

# app.add_url_rule('/','home', home,methods=['GET'])

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == 'POST':

        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        cpassword = request.form.get('cPassword')
        print(cpassword, password)
        if password != cpassword:
            flash("Password and Confirm Password is matching!", "info")
            return redirect(url_for('register'))
        existingUser = User.query.filter_by(username = username).count()
        existingemail = User.query.filter_by(email = email).count()
        if existingUser:
            flash("Username is not Available!", "info")
            return redirect(url_for('register'))
        elif existingemail:
            flash("email is not Available!", "info")
            return redirect(url_for('register'))
        
        user = User(username,email, password)
        db.session.add(user)
        db.session.commit()
        flash(f"{user.username} account is Created successfully", 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title = 'register')


@app.route("/login", methods= ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        # user = User.query.filter_by(email=data['email']).first()

        if not user:
            return jsonify({'failed': "User not found"}), 404
        
        session['user.id'] = user.id # type: ignore
        if user and user.checkPassword(password):
            token = jwt.encode(
        {'user.id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        app.config['SECRET_KEY'],
        algorithm="HS256"
    )
            response = make_response(redirect(url_for("home")))
            response.set_cookie('currentUser', token, httponly=True, secure=False)  # Secure=False for local testing
            session['user.id'] = user.id
            flash(f"Welcome {user.username}", 'success')
            return response
        else:
            flash('invalid email and Password', 'warning')
            return redirect(url_for('login'))
    
    return render_template('login.html', title = 'login')
    
@app.route('/logout')
@token_required
def logout(currentUser):
    res = make_response(redirect(url_for('home')))
    res.set_cookie('currentUser', '', expires=0)
    session.clear()
    flash("User is Logout", 'success')
    return res

    
    
    
@app.route('/addstudent', methods=['POST','GET'])
@token_required
def addstudent(currentuser):
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            rollNo = request.form.get('rollNo')
            std = request.form.get('std')
            course = request.form.get('course')

            # Validate data (optional, add checks as needed)
            if not name or not rollNo or not std or not course:
                flash("All fields are required!", "danger")
                return redirect(url_for('addstudent'))

            newstudent = Student(name, rollNo, std, course)
            db.session.add(newstudent)
            db.session.commit()
        
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'invalid : {str(e)}', 'warning')
            return redirect(url_for('addstudent'))
    else:
        return render_template('addstudent.html', title='addstudent',info='Add', endpoint="addstudent", student=None)

@app.route('/updatestudent/<int:id>', methods=['POST', 'GET'])
def updateStudent(id):
    student = Student.query.get_or_404(id)
    if request.method == "POST":
        data = request.form
        # name, rollNo, std, course=  data.value()
        student.name = data.get('name', student.name)
        student.rollNo = data.get('rollNo', student.rollNo)
        student.course = data.get('course', student.course)
        student.std = data.get('std', student.std)

        db.session.commit()
        flash('Student is update successfully', 'success')
        return redirect(url_for('home'))
        # return jsonify({'msg': f"update {studentScheme.jsonify(student)} student is added"})
    return render_template('addstudent.html', title='Update', info='Update', student=student, endpoint="updatestudent")

@app.route('/deletestudent/<int:userid>')
def deletestudent(userid):
    student = Student.query.get_or_404(userid)
    if not student:
        flash("user is not found or already delete", 'info')
        return redirect(url_for('home'))
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {student.name} is delete successfully', 'success')
    return redirect(url_for('home'))
    # return f"{studentScheme.dump(student)} is delete"
    
    
    

@app.route('/fileupload',methods = ["GET", "POST"])
# @token_required
def upload():
    if request.method == "POST":
        file = request.files['file']
        if file and allowedfile(file.filename):
            try:
                if file.filename:
                    filenames = file.filename.rsplit('.', 1)[1]
                    if filenames == "csv":
                        return csvUpload(file)
                    else:
                        return excelUpload(file)
            except Exception as e:
                return jsonify({"error": f"Failed to Upload process the file: {str(e)}"}), 500
        else:
                return "failed", 400

       
        
    return "failed", 400

if __name__ == "__main__":
    app.run(debug=True)
    
