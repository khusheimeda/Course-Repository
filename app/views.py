from app import app, lm
from flask import request, redirect, render_template, url_for, send_file, current_app
from flask_login import login_user, logout_user, current_user
from functools import wraps
from .forms import LoginForm
from .user import User
import pymongo
from werkzeug.utils import secure_filename
import pandas as pd
import database_converter as dc
import os
from time import sleep
import datetime
import platform


username = ''
password = ''
sem = ''
role = ''
cache = ""
oldpwd = ""
newpwd = ""
confirm = ""
branch = ''
urole = '' #role of user
upload_role = '' #role of USN the admin uploads
static_path = os.path.join(os.path.abspath("app"), "static")


def login_required(role = "ANY"):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args,**kwargs):

            if not current_user.is_authenticated:
               return current_app.login_manager.unauthorized()
            if ( (urole != role) and (role != "ANY")):
                return current_app.login_manager.unauthorized()      
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


@app.route('/')
def home():
    sleep(1)
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None
    if request.method == 'POST' and form.validate_on_submit():
        global role
        role = request.form.get('role')
        if role == "Student":  #_id:5d1b877cba85c7eb1537d130 Username:"PES1201700003" Password:"abcd"
            user = app.config['STUDENT_COLLECTION'].find_one({"Username": form.username.data})
            if user and User.validate_login(user['Password'], form.password.data):
                user_obj = User(user['Username'],user['Password'],role)
                global username, password, urole
                username = user_obj.username
                password = user_obj.password
                urole = user_obj.urole
                login_user(user_obj)
                print(urole)
                print("login success")
                return redirect(url_for("home_student"))
            else:
                error = "Wrong username or password!"
        elif role == "Admin":#as of now username is admin and password is admin123
            user = app.config['ADMIN_COLLECTION'].find_one({"Username": form.username.data})
            if user and User.validate_login(user['Password'], form.password.data):
                user_obj = User(user['Username'],user['Password'],role)
                username = user_obj.username
                password = user_obj.password
                urole = user_obj.urole
                login_user(user_obj)
                print(urole)
                print("login success")
                return redirect(url_for("home_admin"))
            else:
                error = "Wrong username or password!"
        elif role == "Teacher":
            user = app.config['TEACHER_COLLECTION'].find_one({"Username": form.username.data})
            if user and User.validate_login(user['Password'], form.password.data):
                user_obj = User(user['Username'], user['Password'], role)
                username = user_obj.username
                password = user_obj.password
                urole = user_obj.urole
                login_user(user_obj)
                print("login success")
                return redirect(url_for("home_teacher"))
            else:
                error = "Wrong username or password!"
        elif role == "Anchor":  #_id:5d1ebafdc77f1226b4f83278 Username:"anchor@pes.edu" Password:"anchor@pes.edu"
            user = app.config['ANCHOR_COLLECTION'].find_one({"Username": form.username.data})
            if user and User.validate_login(user['Password'], form.password.data):
                user_obj = User(user['Username'],user['Password'],role)
                username = user_obj.username
                password = user_obj.password
                urole = user_obj.urole
                login_user(user_obj)
                print("login success")
                return redirect(url_for("home_anchor"))
            else:
                error = "Wrong username or password!"
            
        error = "Wrong username or password!"
    return render_template('login_common.html', title='login', form=form, error=error)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/home/student', methods=['GET', 'POST'])
@login_required(role = "Student")
def home_student(path = ''):
    global sem
    sem = find_sem(username)
    global branch
    branch = "CSE"
    chk = 0
    sub = ''
    user = app.config['STUDENT_COLLECTION'].find_one({"Username": username})
    if user["Cache"] == 0:
        return redirect(url_for('reset_password', role = 'Student'))
    else:
        if user["Password"] == password:
            print("Password set")
    return redirect(url_for('directories', role = 'Student'))


@app.route('/home/admin', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required("Admin")
def home_admin():
    print(urole)
    user = app.config['ADMIN_COLLECTION'].find_one({"Username": username})
    if user["Cache"] == 0:
        return redirect(url_for('reset_password', role = 'Admin'))
    else:
        if user["Password"] == password:
            print("Password set")
            if request.method == 'POST':
                number = request.form.get('howmany')
                print(number)
                global upload_role
                upload_role = request.form.get('uploadrole')
                print(upload_role)
                if number == 'Many':
                    return redirect(url_for('upload_file', upload_role = upload_role))
                elif number == 'One':
                    return redirect(url_for('upload_one', upload_role = upload_role))
    return render_template('home_admin.html')

def find_sem(username):
    if len(username) == 13:
        year = int(username[4:8])
        
    elif len(username) == 12:
        year = int("20"+username[4:6])
        
    x = datetime.datetime.now()
    year_now = x.year
    month = x.month
    if year_now-year==0 and month in range(6,13):
        print("sem 1")
        return 1        
    elif year_now-year==1 and month in range(1,6):
        print("sem 2")
        return 2
    elif year_now-year==1 and month in range(6,13):
        print("sem 3")
        return 3
    elif year_now-year==2 and month in range(1,6):
        print("sem 4")
        return 4
    elif year_now-year==2 and month in range(6,13):
        print("sem 5")
        return 5
    elif year_now-year==3 and month in range(1,6):
        print("sem 6")
        return 6
    elif year_now-year==3 and month in range(6,13):
        print("sem 7")
        return 7
    elif year_now-year==4 and month in range(1,6):
        print("sem 8")
        return 8

def make_tree(path, role):
    # Returns a tree representing the file structure
    # Each node contains a list of its children, "&" separated relative path value, and its name
    # If node represents a file, it does not contain children
    separator = '/'
    if platform.system() == 'Windows':
        separator = '\\'
    tree = dict(name=" ".join(os.path.basename(path).split("_")), children=[], path="&".join(path.split(separator)), isDir=True)
    try: lst = os.listdir(os.path.join(static_path, path))
    except OSError:
        pass    #ignore errors
    else:
        for file in lst:
            file_path = os.path.join(static_path, path, file)
            if os.path.isdir(file_path):
                if role == "Student" and (file == 'Course_Assessments' or file == 'Question_papers_&_Solns' or file == 'Projects'):
                    continue
                tree['children'].append(make_tree(os.path.join(path, file), role))
            else:
                tree['children'].append(dict(name = file, path = "&".join(os.path.join(path, file).split(separator)), isDir=False))
    return tree


@app.route('/home/directories/<role>', methods = ['GET', 'POST', 'PUT', 'DELETE'])
@login_required("ANY")
def directories(role):
    sem = 0
    if role == 'Teacher' or role == 'Anchor':
        path = "Course_Material"
    elif role == 'Student':
        sem = find_sem(username)
        path = os.path.join("Course_Material", f"Semester_{sem}")
    return render_template('directories.html', role = role, tree = make_tree(path, role), sem = sem, username = username)


def show_file(path, name):
    if request.method == 'GET':
        return send_file(os.path.join(path, name))


@app.route('/get-file/<path>', methods = ['GET', 'POST', 'PUT', 'DELETE'])
def get_file(path):
    if request.method == 'GET':
        relative_file_path = path.split("&")
        file_path = os.path.join(static_path, *relative_file_path)
        return send_file(file_path)
        

@app.route('/home/show/<role>/<path>', methods = ['GET', 'POST', 'PUT', 'DELETE'])
@login_required("ANY")
def show_content(role, path):    
    sem = 0        
    if role == 'Student':
        sem = find_sem(username)    
    return render_template('open_file.html', filepath = path, role = role, username = username, sem = sem)


@app.route('/home/teacher')
@login_required("Teacher")
def home_teacher():
    user = app.config['TEACHER_COLLECTION'].find_one({"Username": username})
    if user["Cache"] == 0:
        return redirect(url_for('reset_password', role = 'Teacher'))
    else:
        if user["Password"] == password:
            print("Password set")
    return redirect(url_for('directories', role = 'Teacher'))


@app.route('/home/anchor')
@login_required("Anchor")
def home_anchor():
    user = app.config['ANCHOR_COLLECTION'].find_one({"Username": username})
    if user["Cache"] == 0:
        return redirect(url_for('reset_password', role = 'Anchor'))
    else:
        if user["Password"] == password:
            print("Password set")
    return redirect(url_for('directories', role = 'Anchor'))


@app.route('/home/anchor/upload', methods = ["POST", "GET", "PUT", "DELETE"])
@login_required("Anchor")
def anchor_upload():
    path = ''
    global static_path
    print(static_path)
    if request.method == 'POST' and 'file' in request.files:
        f = request.files['file']
        upsem = request.form.get('upsem')
        upsub = request.form['upsub']
        material = request.form.get('material')
        UPLOAD_FOLDER = (os.path.join(os.path.abspath("app"), "static", 'Course_Material', upsem, upsub, material)).replace("\\",'/')
        filename = secure_filename(f.filename)
        f.save(os.path.join(UPLOAD_FOLDER,filename))
        return redirect(url_for('anchor_download'))
    return render_template('uploadmany.html', role = 'Anchor', username = username)


@app.route("/home/anchor/download/success", methods = ["POST","GET","PUT","DELETE"])
@login_required("Anchor")
def anchor_download():
    return render_template("file_upload_result.html",upload_role = "Anchor", username = username)


@app.route('/reset/password/<role>', methods=["POST", "GET", "PUT", "DELETE"])
@login_required("ANY")
def reset_password(role):
    error = None
    col = "student"
    home = "home_student"
    if request.method == 'POST':
        global username, oldpwd, newpwd, confirm
        oldpwd = request.form['oldpwd']
        newpwd = request.form['newpwd']
        confirm = request.form['confirm']
        if role == 'Student':
            col = "student"
            home = 'home_student'

        elif role == 'Teacher':
            col = "teacher"
            home = 'home_teacher'

        elif role == 'Admin':
            col = "admin"
            home = 'home_admin'

        else:
            col = 'anchor'
            home = 'home_anchor'
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["mydatabase"]
        mycol = mydb[col]
        if mycol.find_one({'Username': username}):
            deets = mycol.find_one({'Username': username})
            if deets.get("Password") != oldpwd:
                error = 'Incorrect Password. Try again.'
            else:
                if newpwd != confirm:
                    error = 'Passwords (new and confirm) don\'t match'
                else:
                    deets.update(Password=newpwd)
                    error = 'Password Changed.'
                    cache = deets.get("Cache")
                    myquery = {"Password": oldpwd, 'Cache': cache}
                    newvalues = {"$set": {"Password": newpwd, 'Cache': str(int(cache) + 1)}}
                    mycol.update_one(myquery, newvalues)
                    return redirect(url_for(home))

    return render_template('reset_password.html', role=role, oldpwd=oldpwd, newpwd=newpwd, confirm=confirm, error=error)


@app.route('/upload/one', methods= ['GET', 'POST', "PUT", "DELETE"])
@login_required("Admin")
def upload_one():
    error = None
    print(role)
    print(upload_role)
    if request.method == 'POST':
        if request.form.get('username') == request.form.get('confirm'):
            myclient = pymongo.MongoClient("mongodb://localhost:27017/")
            db = myclient["mydatabase"]
            if upload_role == 'Student':
                data = db.student
                cursor = data.find({})
                temp = []
                for i in cursor:
                    temp.append(i)
                flag = 0
                for y in temp:
                    if request.form.get('username') == y['Username']:
                        flag = 1
                        break
                if flag == 0:
                    x = {"Username": request.form.get('username'), "Password": request.form.get('username'), "Cache": 0}
                    result = db.student.insert_one(x)
                else:
                    error = 'User already in database'
                    return render_template('home_admin_uploadone.html', upload_role = upload_role, error=error)
                for x in db.student.find():
                    print(x)
            elif upload_role == 'Teacher':
                data = db.teacher
                cursor = data.find({})
                temp = []
                for i in cursor:
                    temp.append(i)
                flag = 0
                for y in temp:
                    if request.form.get('username') == y['Username']:
                        flag = 1
                        break
                if flag == 0:
                    x = {"Username": request.form.get('username'), "Password": request.form.get('username'), "Cache": 0}
                    result = db.teacher.insert_one(x)
                else:
                    error = 'User already in database'
                    return render_template('home_admin_uploadone.html', upload_role = upload_role, error=error)
                for x in db.teacher.find():
                    print(x)
        else:
            error = 'Username and Confirm Username do not match. Try again.'
        return redirect(url_for('file_upload_result', upload_role = upload_role))
    return render_template('home_admin_uploadone.html', upload_role = upload_role, error = error, username = username)
                

@app.route('/upload/file', methods=['GET', 'POST', "PUT", "DELETE"])
@login_required("Admin")
def upload_file():
    print(upload_role)
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename('temp.xlsx'))
        writer = pd.ExcelWriter('temp.xlsx', engine='openpyxl')
        wb = writer.book
        df = pd.read_excel("temp.xlsx")
        df['Password'] = df['Username']
        df['Cache'] = '0'

        df.to_excel(writer, index=False)
        wb.save('temp.xlsx')
        dc.csv_from_excel('temp')

        if upload_role == 'Student':
            dataframe0 = pd.read_csv('student_database.csv')
            dataframe1 = pd.read_csv('temp.csv')
            combined_csv = pd.concat([dataframe0, dataframe1])
            combined_csv.to_csv("student_database.csv", index=False, encoding='utf-8-sig')
            dc.convert("student_database.csv")
            """data_csv = pd.read_csv('student_database.csv', 'Sheet1')
            data_csv.to_csv('student_database.csv', encoding='utf-8') """

        else:
            dataframe0 = pd.read_csv('teacher_database.csv')
            dataframe1 = pd.read_csv('temp.csv')
            combined_csv = pd.concat([dataframe0, dataframe1])
            combined_csv.to_csv("teacher_database.csv", index=False, encoding='utf-8-sig')
            dc.convert("teacher_database.csv")
            """data_csv = pd.read_csv('teacher_database.csv', 'Sheet1')
            data_csv.to_csv('teacher_database.csv', encoding='utf-8') """

        os.remove('temp.csv')
        os.remove('temp.xlsx')

        return redirect(url_for('file_upload_result', upload_role = upload_role))
    return render_template('uploadmany.html', upload_role = upload_role, username = username, role = 'Admin')


@app.route('/upload/result/<upload_role>')
@login_required("Admin")
def file_upload_result(upload_role):
    return render_template('file_upload_result.html', upload_role = upload_role)


@lm.user_loader
def load_user(username):
    u = app.config['STUDENT_COLLECTION'].find_one({"Username": username})
    t = app.config['TEACHER_COLLECTION'].find_one({"Username": username})
    a = app.config['ADMIN_COLLECTION'].find_one({"Username": username})
    at = app.config['ANCHOR_COLLECTION'].find_one({"Username": username})
    if not (u or t or a or at):
        return None
    elif not (u or a or at):
        return User(t['Username'],t['Password'],urole)
    elif not (u or t or at):
        return User(a['Username'],a['Password'],urole)
    elif not (u or t or a):
        return User(at['Username'],at['Password'],urole)
    else:
        return User(u['Username'],u['Password'],urole)
