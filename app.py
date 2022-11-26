from flask import Flask, render_template ,request, session, redirect, url_for, jsonify
from flask_mysqldb import MySQL
import os
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath


app = Flask(__name__)

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/assets/images/performer')


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'events'
app.config['MYSQL_PORT'] = 3307
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# configure secret key for session protection)
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'

mysql = MySQL(app)
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 

@app.route("/")
def index():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * from events;')
    events = cursor.fetchall()
    return render_template("index.html",events=events)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/events")
def events():   
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * from events;')
    events = cursor.fetchall()
    return render_template("events.html",events=events)

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")

@app.route("/contact", methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        phone = request.form.get("cell")
        city = request.form.get("city")
        msg = request.form.get("msg")
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO messages (fname, lname, email,phone, city, message) VALUES (%s,%s,%s,%s,%s,%s);',(fname,lname,email,phone,city,msg))
        mysql.connection.commit()        
        return render_template("contact.html",sent="true")
    return render_template("contact.html")

@app.route("/registration" , methods=['POST'])
def registration():
    if request.method == 'POST':
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        cell = request.form.get("cell")
        address = request.form.get("address")
        zip = request.form.get("zip")
        date = request.form.get("date")
        time = request.form.get("time")
        city = request.form.get("city")
        programid = request.form.get("program")
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT name from events where id =%s',(programid))
        event_name = cursor.fetchone()['name']
        cursor.execute('INSERT INTO registrations (fname, lname, email,phone, address, zip, date, time, city, eventid, event_name) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);',(fname,lname,email,cell,address,zip,date,time,city,programid,event_name))
        mysql.connection.commit()
        # redirect index 
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * from events;')
        events = cursor.fetchall()
        return render_template("index.html",events=events,register="done")
        
# -------------------------------------  ADMIN DASH  ----------------------------------------------------
@app.route("/admin")
def admin():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM registrations where city="karachi";')
        karachi_registrations = cursor.fetchone()['COUNT(*)']
        cursor.execute('SELECT COUNT(*) FROM registrations where city="lahore";')
        lahore_registrations = cursor.fetchone()['COUNT(*)']
        cursor.execute('SELECT COUNT(*) FROM registrations where city="islamabad";')
        islamabad_registrations = cursor.fetchone()['COUNT(*)']
        cursor.execute('SELECT COUNT(*) FROM messages;')
        messages = cursor.fetchone()['COUNT(*)']
        return render_template("admin-index.html",K_registrations=karachi_registrations,L_registrations=lahore_registrations,I_registrations=islamabad_registrations,messages=messages)
    else:
        return redirect(url_for("admin_login"))

@app.route("/admin-login",methods=['GET','POST'])
def admin_login():
    if 'loggedin' in session :
        return redirect(url_for("admin"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            return render_template("admin-login.html",error="Missing username or password!")
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * from admin where username = %s;',[username])
        data = cursor.fetchone()
        if data:
            if data['password'] == password:                
                session['loggedin'] = True
                session['userid'] = data['id']
                session['type'] = 'admin'
                session['username'] = data['username']
                return redirect(url_for("admin"))
            else:
                return render_template("admin-login.html",error="Invalid Password!")
        else:
                return render_template("admin-login.html",error="Invalid Username!")
    return render_template("admin-login.html")
    
@app.route("/logout")
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('username', None)
    session.pop('type', None)
    # Redirect to index page
    return redirect(url_for('admin'))

@app.route("/admin-events")
def admin_events():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * from events;')
    events = cursor.fetchall()
    return render_template("admin-events.html",events=events)
@app.route("/admin-add-events",methods=['GET','POST'])
def admin_add_events():
    if request.method == 'POST':
        name = request.form.get("name")
        desc = request.form.get("desc")
        price = request.form.get("price")
        picture = request.files["picture"]
        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            picture.save(
                    os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO events (name, description, picture, price) VALUES (%s,%s,%s,%s);',(name,desc,filename,price))
            mysql.connection.commit()
            return redirect(url_for("admin_events"))

        else:
            return render_template("admin-add-events.html",error="Image Not Supported")
    else:
        return render_template("admin-add-events.html")

@app.route("/delete/<string:type>/<string:id>")
def deleting_route(type,id):
    if type == "admin-event":
            cursor = mysql.connection.cursor()
            cursor.execute('Select picture FROM events WHERE id=%s;',[id])
            filename = cursor.fetchone()['picture']
            cursor.execute('DELETE FROM events WHERE id=%s;',[id])
            mysql.connection.commit()
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                print(e)
            return redirect(url_for("admin_events"))
    elif type == "registrations":
            cursor = mysql.connection.cursor()
            cursor.execute('DELETE FROM registrations WHERE id=%s;',[id])
            mysql.connection.commit()
            return redirect(url_for("admin_registrations"))
    elif type == "message":
            cursor = mysql.connection.cursor()
            cursor.execute('DELETE FROM messages WHERE id=%s;',[id])
            mysql.connection.commit()
            return redirect(url_for("admin_messages"))

            
@app.route("/admin-registrations")
def admin_registrations():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * from registrations;')
    registrations = cursor.fetchall()
    return render_template("admin-registrations.html",registrations=registrations)
            
@app.route("/admin-messages")
def admin_messages():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * from messages;')
    messages = cursor.fetchall()
    return render_template("admin-messages.html",messages=messages)



if __name__=='__main__':
    app.run(debug=True)