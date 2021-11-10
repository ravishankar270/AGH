from operator import sub
import os
from flask import Flask,render_template,request,flash,redirect,session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from werkzeug.wrappers import response
import json

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER
    
    # Other FLASK config varaibles ...
app.config['SQLALCHEMY_DATABASE_URI']="mysql://root:@localhost/agh"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY']="this"

db=SQLAlchemy(app)
class Subject(db.Model):
    subId=db.Column(db.Integer,primary_key=True)
    subject=db.Column(db.String(200),nullable=False)
    marks=db.Column(db.Integer)
    students=db.relationship('Student',backref="students")
    teachers=db.relationship('Teacher',backref="teacher")

class Student(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    seatNo=db.Column(db.Integer)
    email=db.Column(db.String(200),nullable=False)
    answer=db.Column(db.String(200))
    marks=db.Column(db.Integer)
    subject_id=db.Column(db.Integer,db.ForeignKey('subject.subId'))
    





class Teacher(db.Model):
    teacherId=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(200),nullable=False)
    subject_id=db.Column(db.Integer,db.ForeignKey('subject.subId'))
    
    
class Answer(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    question=db.Column(db.String(200),nullable=False)
    answer=db.Column(db.String(700),nullable=False)
    tid=db.Column(db.Integer,db.ForeignKey('teacher.teacherId'))
    subject_id=db.Column(db.Integer,db.ForeignKey('subject.subId'))



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/",methods=['GET','POST'])
def index():
    
    if session.get('messages'):
        s=json.loads(session.get("messages"))
        response=dict(json.loads(session['messages']))
        if s.get('answer'):

            return render_template('index.html',response={"m":response,"message":"success"})

        
        
    else:
        return redirect('/login')
    if request.method=='POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        
        if file.filename == '':
            flash('No selected file')
            
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            path=app.config['UPLOAD_FOLDER']
            
            try:
                if not os.path.exists(path+str(response['seatno'])):
                    os.makedirs(path+str(response['seatno']))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            
            pdfname = secure_filename(file.filename)
            
            file.save(os.path.join(path+str(response['seatno']),pdfname))
            pdfs = f"uploads/{response['seatno']}/{pdfname}"
            pages = convert_from_path(pdfs, 350, poppler_path = r"C:\Users\Ravi\Downloads\proppler\poppler-21.11.0\Library\bin")
            print(pages)
            i = 1
            for page in pages:
                image_name = "Page_" + str(i) + ".jpg"  
                filename = secure_filename(image_name)
                page.save(os.path.join(app.config['UPLOAD_FOLDER']+str(response['seatno']), filename))
                # page.save(image_name, "JPEG")
                i = i+1
            student=Student.query.filter_by(email=response['email']).first()
            print(student.answer)
            student.answer=path+str(response['seatno'])
            db.session.add(student)
            db.session.commit()
            print(student.answer)
            a=json.loads(session['messages']).update({"answer":student.answer})
            session['messages']=a
            return render_template('index.html',response={"m":response,"message":"success"})
    return render_template("index.html",response={"m":response,"message":"upload"})


# @app.route("/login")
# def Login():
#     return render_template("login.html")


@app.route("/login",methods=['GET','POST'])
def login():
    print('ok')
    if session.get('messages'):
        print("ok")
        return redirect("/")
    if request.method=='POST':
        if request.form['val']=="2":
            student=Student.query.filter_by(email=request.form['email']).first()
            if not student:
                return redirect(request.url)
            subject=student.subject_id
            answer=student.answer
            session['messages']=json.dumps({"email":student.email,"seatno":student.seatNo,"answer":answer,"subject":subject})
            
            return redirect('/')
        else:
            teacher=Teacher.query.filter_by(email=request.form['email']).first()
            print(teacher)
            if not teacher:
                return redirect(request.url)
            session['messages']=json.dumps({"email":teacher.email,"subject":request.form['subject']})
            print('a')
            return redirect('/teacher')

    return render_template("login.html")




@app.route("/teacher",methods=['GET','POST'])
def teacher():
    if not session.get('messages'):
        return redirect('/login')
        
    else:
        response=json.loads(session['messages'])
        subject=Subject.query.filter_by(subject=response['subject']).first()
        answ=Answer.query.filter_by(subject_id=subject.subId).first()
        if answ:
            return render_template("teacher.html",message="yes")
    if request.method=='POST':
        print(request.form)
        subject=Subject.query.filter_by(subject=request.form['subject']).first()
        t=Teacher.query.filter_by(email=response['email']).first()
        i=0
        for key in request.form.keys():
            if i<1:
                i+=1
                continue
            answer=Answer(question=key,answer=request.form[key],subject_id=subject.subId,tid=t.teacherId)
            db.session.add(answer)
            db.session.commit()
            return render_template("teacher.html",message="yes")

    return render_template("teacher.html",message="no")

@app.route("/logout",methods=['GET','POST'])
def logout():
    session.clear()
    return redirect('/login')




if __name__=="__main__":
    app.run(debug=True)