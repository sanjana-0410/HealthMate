from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from werkzeug.utils import secure_filename
from pytz import timezone
import os
from flask_mail import Mail, Message
from numpy.random import randint
from tensorflow.keras.models import load_model
import numpy as np
app = Flask(__name__)
app.secret_key = "HealthMate"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///userdb.db"
app.config["SQLALCHEMY_BINDS"] = {
    "RepoDB": "sqlite:///repodb.db",
    "FileDB": "sqlite:///filedb.db",
    "AppointmentDB": "sqlite:///appointmentdb.db",
    "prescriptionDB": "sqlite:///prescriptiondb.db"
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = r'C:\Users\nived\Documents\GitHub\miniproject\miniproject\static\files'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'healmate@outlook.com'
app.config['MAIL_PASSWORD'] = "miniproject123"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)


class UserDB(db.Model):
    userName = db.Column(db.String(20), primary_key=True)
    userPassword = db.Column(db.String(100), nullable=False)
    userFirstName = db.Column(db.String(50), nullable=False)
    userLastName = db.Column(db.String(50), nullable=False)
    userEmailID = db.Column(db.String(100), nullable=False)
    userDOB = db.Column(db.String(20), nullable=False)

    def __repr__(self) -> str:
        return f"{self.userName}"


class RepoDB(db.Model):
    __bind_key__ = 'RepoDB'
    id = db.Column(db.Integer, primary_key=True)
    userN = db.Column(db.String(20), nullable=False)
    nameOfRepo = db.Column(db.String(50), nullable=False)
    dateCreated = db.Column(db.String(30), default=datetime.now(
        timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S.%f'))

    def __repr__(self) -> str:
        return f"{self.id}"


class FileDB(db.Model):
    __bind_key__ = "FileDB"
    id = db.Column(db.Integer, primary_key=True)
    userAndRepoName = db.Column(db.String(100), nullable=False)
    fileName = db.Column(db.Text, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.String(200))
    mimetype = db.Column(db.Text, nullable=False)


class AppointmentDB(db.Model):
    __bind_key__ = "AppointmentDB"
    id = db.Column(db.Integer, primary_key=True)
    userN = db.Column(db.String(100), nullable=False)
    doctorN = db.Column(db.String(100), nullable=False)
    hospitalN = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(15), nullable=False)
    time = db.Column(db.String(10), nullable=False)


class prescriptionDB(db.Model):
    __bind_key__ = "prescriptionDB"
    id = db.Column(db.Integer, primary_key=True)
    userN = db.Column(db.String(100), nullable=False)
    medN = db.Column(db.String(100), nullable=False)
    freq = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(30), nullable=False)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if UserDB.query.filter_by(userName=request.form["un"]).first() is None:
            usern = request.form["un"]
            userpwd = request.form['up']
            usereid = request.form["ueid"]
            userdob = request.form["udob"]
            userfn = request.form["ufn"]
            userln = request.form["uln"]
            if userpwd != request.form["cp"]:
                return render_template("register.html", x=3)
            hashed_userpwd = bcrypt.generate_password_hash(userpwd, 14)
            user = UserDB(userName=usern, userPassword=hashed_userpwd, userFirstName=userfn,
                          userLastName=userln, userEmailID=usereid, userDOB=userdob)
            db.session.add(user)
            db.session.commit()
            return render_template("register.html", x=2)
        return render_template("register.html", x=1)
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    global session
    if request.method == "POST":
        usern = request.form["una"]
        if UserDB.query.filter_by(userName=usern).first() is not None:
            session["usern"] = usern
            userpwd = request.form['upa']
            if bcrypt.check_password_hash(UserDB.query.filter_by(userName=usern).first().userPassword, userpwd):
                return redirect(f"/profile/{usern}")
            else:
                return render_template("login.html", x=1)
        else:
            return render_template("login.html", x=1)

    return render_template("login.html")


@app.route("/forgotPassword", methods=["GET", "POST"])
def forgotPwd():
    if request.method == "POST":
        username = request.form["fpun"]
        user = UserDB.query.filter_by(userName=username).first()
        if not user:
            return render_template("forgotPwd.html", x=1)
        else:
            msg = Message(
                'HealMate Password Reset',
                sender='healmate@outlook.com',
                recipients=[user.userEmailID]
            )
            pwd = str(randint(1000, 10000, 1)[0])
            user.userPassword = bcrypt.generate_password_hash(pwd, 12)
            db.session.add(user)
            db.session.commit()
            msg.body = f"Hello,{user.userName}\nYour new password is {pwd}"
            mail.send(msg)
            return render_template("forgotPwd.html", x=2)
    return render_template("forgotPwd.html")


@app.route("/profile/<string:uName>")
def profile(uName):
    if "usern" in session:
        uName = session["usern"]
        user = UserDB.query.filter_by(userName=uName).first()
        repos = RepoDB.query.filter_by(userN=uName).all()
        return render_template("profile.html", user=user, repos=repos)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/editProfile", methods=["GET", "POST"])
def editProfile(uName):
    if "usern" in session:
        if request.method == "POST":
            prof = UserDB.query.filter_by(userName=uName).first()
            prof.userFirstName = request.form["upfn"]
            prof.userLastName = request.form["upln"]
            prof.userEmailID = request.form["upeid"]
            prof.userDOB = request.form["updob"]
            db.session.add(prof)
            db.session.commit()
            return redirect(f"/profile/{uName}")
        prof = UserDB.query.filter_by(userName=uName).first()
        return render_template("editProfile.html", username=uName, prof=prof)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/editProfile/changePWD", methods=["GET", "POST"])
def changePWD(uName):
    if "usern" in session:
        if request.method == "POST":
            prof = UserDB.query.filter_by(userName=uName).first()
            if not bcrypt.check_password_hash(prof.userPassword, request.form["pucp"]):
                return render_template("changePwd.html", username=uName, x=1)
            else:
                prof.userPassword = bcrypt.generate_password_hash(
                    request.form["punp"], 14)
                db.session.add(prof)
                db.session.commit()
                return render_template("changePwd.html", username=uName, x=2)
        return render_template("changePwd.html", username=uName)
    return redirect(url_for("login"))


@app.route("/profile/<string:uName>/createrepo", methods=["GET", "POST"])
def createRepo(uName):
    if "usern" in session:
        if request.method == "POST":
            repo = RepoDB(userN=uName, nameOfRepo=request.form["rn"])
            db.session.add(repo)
            db.session.commit()
            return redirect(f"/profile/{uName}")
        return render_template("createRepo.html", username=uName)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/<int:repoID>")
def repo(uName, repoID):
    if "usern" in session:
        files = FileDB.query.filter_by(userAndRepoName=uName+str(repoID)).all()
        return render_template("repo.html", username=uName, repoID=repoID, files=files)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/<int:repoID>/upload", methods=["GET", "POST"])
def fileUpload(uName, repoID):
    if "usern" in session:
        File = request.files["file"]
        fName = File.filename.split(".")
        File.filename = fName[0] + uName + str(datetime.now()) + "." + fName[1]
        fName = secure_filename(File.filename)
        File.save(os.path.join(app.config["UPLOAD_FOLDER"], fName))
        mimetype = File.mimetype
        file = FileDB(userAndRepoName=uName+str(repoID), fileName=fName,
                      name=request.form["fileName"], desc=request.form["fileDesc"], mimetype=mimetype)
        db.session.add(file)
        db.session.commit()
        return redirect(f"/profile/{uName}/{repoID}")
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/appointment")
def appointment(uName):
    if "usern" in session:
        appos = AppointmentDB.query.filter_by(userN=uName).all()
        return render_template("appointment.html", username=uName, appos=appos)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/appointment/createAppointment", methods=["GET", "POST"])
def createAppointment(uName):
    if "usern" in session:
        if request.method == "POST":
            dn = request.form["dname"]
            hn = request.form["hname"]
            t = request.form["atime"]
            d = request.form["adate"]
            appo = AppointmentDB(userN=uName, doctorN=dn,
                                 hospitalN=hn, date=str(d), time=str(t))
            db.session.add(appo)
            db.session.commit()
            return redirect(f"/profile/{uName}/appointment")
        return render_template("createAppointment.html", username=uName)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/<int:appoID>/appoupdate", methods=["GET", "POST"])
def appointmentUpdate(uName, appoID):
    if "usern" in session:
        if request.method == "POST":
            appo = AppointmentDB.query.filter_by(id=appoID).first()
            appo.doctorN = request.form["audn"]
            appo.hospitalN = request.form["auhn"]
            appo.time = str(request.form["autime"])
            appo.date = str(request.form["audate"])
            db.session.add(appo)
            db.session.commit()
            return redirect(f"/profile/{uName}/appointment")
        appo = AppointmentDB.query.filter_by(id=appoID).first()
        return render_template("appoUpdate.html", username=uName, aID=appoID, appo=appo)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/<int:appoID>/appodelete")
def appointmentDelete(uName, appoID):
    if "usern" in session:
        appo = AppointmentDB.query.filter_by(id=appoID).first()
        db.session.delete(appo)
        db.session.commit()
        return redirect(f"/profile/{uName}/appointment")
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/prescription")
def prescription(uName):
    if "usern" in session:
        pers = prescriptionDB.query.filter_by(userN=uName).all()
        return render_template("prescription.html", username=uName, pers=pers)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/prescription/createPrescription", methods=["GET", "POST"])
def createPrescription(uName):
    if "usern" in session:
        if request.method == "POST":
            medname = request.form["pmname"]
            pfreq = request.form.getlist("pfreq")
            pd = request.form["pdur"]
            st = ""
            for x in pfreq:
                st += x
                st += ","
            per = prescriptionDB(userN=uName, medN=medname,
                                 freq=st[:-1], duration=pd)
            db.session.add(per)
            db.session.commit()
            return redirect(f"/profile/{uName}/prescription")
        return render_template("createPrescription.html", username=uName)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/<int:perID>/perupdate", methods=["GET", "POST"])
def updatePrescription(uName, perID):
    if "usern" in session:
        if request.method == "POST":
            per = prescriptionDB.query.filter_by(id=perID).first()
            per.medN = request.form["pumname"]
            pfreq = request.form.getlist("pufreq")
            per.duration = request.form["pudur"]
            st = ""
            for x in pfreq:
                st += x
                st += ","
            per.freq = st[:-1]
            db.session.add(per)
            db.session.commit()
            return redirect(f"/profile/{uName}/prescription")
        per = prescriptionDB.query.filter_by(id=perID).first()
        return render_template("persUpdate.html", username=uName, perID=perID, per=per)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/<int:perID>/perdelete")
def persDelete(uName, perID):
    if "usern" in session:
        per = prescriptionDB.query.filter_by(id=perID).first()
        db.session.delete(per)
        db.session.commit()
        return redirect(f"/profile/{uName}/prescription")
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/<int:repoID>/repodelete")
def repoDelete(uName, repoID):
    if "usern" in session:
        file = FileDB.query.filter_by(userAndRepoName=uName+str(repoID)).all()
        for f in file:
            fl = FileDB.query.filter_by(id=f.id).first()
            db.session.delete(fl)
            db.session.commit()
        repo = RepoDB.query.filter_by(id=repoID).first()
        db.session.delete(repo)
        db.session.commit()
        return redirect(f"/profile/{uName}")
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/<int:repoID>/repoupdate", methods=["GET", "POST"])
def repoUpdate(uName, repoID):
    if "usern" in session:
        if request.method == "POST":
            newName = request.form["run"]
            rep = RepoDB.query.filter_by(id=repoID).first()
            rep.nameOfRepo = newName
            db.session.add(rep)
            db.session.commit()
            return redirect(f"/profile/{uName}")
        repo = RepoDB.query.filter_by(id=repoID).first()
        return render_template("repoUpdate.html", username=uName, repoID=repoID, repo=repo)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/<int:repoID>/<int:fileID>/filedelete")
def fileDelete(uName, repoID, fileID):
    if "usern" in session:
        file = FileDB.query.filter_by(id=fileID).first()
        db.session.delete(file)
        db.session.commit()
        return redirect(f"/profile/{uName}/{repoID}")
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/<int:repoID>/<int:fileID>/fileupdate", methods=["GET", "POST"])
def fileUpdate(uName, repoID, fileID):
    if "usern" in session:
        if request.method == "POST":
            file = FileDB.query.filter_by(id=fileID).first()
            file.name = request.form["fut"]
            file.desc = request.form["fud"]
            db.session.add(file)
            db.session.commit()
            return redirect(f"/profile/{uName}/{repoID}")
        file = FileDB.query.filter_by(id=fileID).first()
        return render_template("fileUpdate.html", username=uName, repoID=repoID, fileID=fileID, file=file)
    else:
        return redirect(url_for("login"))


@app.route("/profile/<string:uName>/diseasedetection", methods=["GET", "POST"])
def diseaseDetection(uName):
    if "usern" in session:
        if request.method == "POST":
            txt = request.form["ddnum"]
            symp = "itching,skin rash,nodal skin eruptions,continuous sneezing,shivering,chills,joint pain,stomach pain,acidity,ulcers on tongue,muscle wasting,vomiting,burning micturition,spotting  urination,fatigue,weight gain,anxiety,cold hands and feets,mood swings,weight loss,restlessness,lethargy,patches in throat,irregular sugar level,cough,high fever,sunken eyes,breathlessness,sweating,dehydration,indigestion,headache,yellowish skin,dark urine,nausea,loss of appetite,pain behind the eyes,back pain,constipation,abdominal pain,diarrhoea,mild fever,yellow urine,yellowing of eyes,acute liver failure,fluid overload,swelling of stomach,swelled lymph nodes,malaise,blurred and distorted vision,phlegm,throat irritation,redness of eyes,sinus pressure,runny nose,congestion,chest pain,weakness in limbs,fast heart rate,pain during bowel movements,pain in anal region,bloody stool,irritation in anus,neck pain,dizziness,cramps,bruising,obesity,swollen legs,swollen blood vessels,puffy face and eyes,enlarged thyroid,brittle nails,swollen extremeties,excessive hunger,extra marital contacts,drying and tingling lips,slurred speech,knee pain,hip joint pain,muscle weakness,stiff neck,swelling joints,movement stiffness,spinning movements,loss of balance,unsteadiness,weakness of one body side,loss of smell,bladder discomfort,foul smell of urine,continuous feel of urine,passage of gases,internal itching,toxic look (typhos),depression,irritability,muscle pain,altered sensorium,red spots over body,belly pain,abnormal menstruation,dischromic  patches,watering from eyes,increased appetite,polyuria,family history,mucoid sputum,rusty sputum,lack of concentration,visual disturbances,receiving blood transfusion,receiving unsterile injections,coma,stomach bleeding,distention of abdomen,history of alcohol consumption,fluid overload.1,blood in sputum,prominent veins on calf,palpitations,painful walking,pus filled pimples,blackheads,scurring,skin peeling,silver like dusting,small dents in nails,inflammatory nails,blister,red sore around nose,yellow crust ooze"
            symp = symp.split(",")
            symp_sorted = sorted(symp)
            l = txt.split(",")
            for x in l:
                try:
                    int(x)
                    if (int(x) > 132):
                        er2 = "Entered incorrect serial number."
                        return render_template("diseaseDetection.html", username=uName, er=er2)
                except:
                    er = "Entered incorrect serial number.Should be serial number separated by commas."
                    return render_template("diseaseDetection.html", username=uName, er=er)
            l = map(int, l)
            ind = []
            for i in range(132):
                ind.append(0)
            for x in l:
                ind[symp.index(symp_sorted[x-1])] = 1
            model = load_model(r'trainedModel.h5')
            dclass = ['(vertigo) Paroymsal  Positional Vertigo', 'AIDS', 'Acne',
                      'Alcoholic hepatitis', 'Allergy', 'Arthritis', 'Bronchial Asthma',
                      'Cervical spondylosis', 'Chicken pox', 'Chronic cholestasis',
                      'Common Cold', 'Dengue', 'Diabetes ',
                      'Dimorphic hemmorhoids(piles)', 'Drug Reaction',
                      'Fungal infection', 'GERD', 'Gastroenteritis', 'Heart attack',
                      'Hepatitis B', 'Hepatitis C', 'Hepatitis D', 'Hepatitis E',
                      'Hypertension ', 'Hyperthyroidism', 'Hypoglycemia',
                      'Hypothyroidism', 'Impetigo', 'Jaundice', 'Malaria', 'Migraine',
                      'Osteoarthristis', 'Paralysis (brain hemorrhage)',
                      'Peptic ulcer diseae', 'Pneumonia', 'Psoriasis', 'Tuberculosis',
                      'Typhoid', 'Urinary tract infection', 'Varicose veins',
                      'hepatitis A']
            p = list(model.predict(np.array(ind).reshape(1, -1))[0])
            pred = []
            for x in sorted(p, reverse=True)[:3]:
                pred.append(dclass[p.index(x)])
            return render_template("diseaseDetection.html", username=uName, pred=pred)
        return render_template("diseaseDetection.html", username=uName)
    else:
        return redirect(url_for("login"))


@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")


@app.route("/logout")
def logout():
    session.pop("usern", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
