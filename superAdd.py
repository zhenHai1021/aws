from curses import flash
from flask import Flask, redirect, render_template, request
from pymysql import connections
import os
import boto3
import botocore

customhost = "internshipdb.c97pmphwoykd.us-east-1.rds.amazonaws.com"
customuser = "admin"
custompass = "admin123"
customdb = "internshipDB"
custombucket = "huezhenwei-bucket"
customregion = "us-east-1"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

app = Flask(__name__, static_folder='assets')

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
)
output = {}
table= 'Supervisor'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('searchSupervisor.html')

@app.route("/addsupervisor", methods=['POST'])
def AddSupervisor():
    sv_id = request.form['sv_id']
    sv_name = request.form['sv_name']
    sv_email = request.form['sv_email']
    programme = request.form['programme']
    faculty = request.form['faculty']
    age = request.form['age']
    password = request.form['password']
    profile_image = request.files['profile_image']

    insert_sql = "INSERT INTO Supervisor VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if profile_image.filename == "":
        return "Please add a profile picture"
    
    if not allowed_file(profile_image.filename):
        return "File type not allowed. Only images (png, jpg, jpeg, gif) and PDFs are allowed."
    
    try:
        cursor.execute(insert_sql, (sv_id, sv_name, sv_email, programme, faculty, age, profile_image, password))
        db_conn.commit()

        
        # Upload image file in S3
        profile_image_in_s3 = "sv_id-" + str(sv_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=profile_image_in_s3, Body=profile_image, ContentType=profile_image.content_type)
            
            # Generate the object URL
            object_url = f"https://{custombucket}.s3.amazonaws.com/{profile_image_in_s3}"

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddSupOutput.html', name=sv_name, email=sv_email, programme=programme, 
                           faculty= faculty, age=age, object_url=object_url)

@app.route("/searchsupervisor", methods=['POST'])
def GetSupervisor():
    try:
        supe = request.form['search']
        # Corrected SQL statement with placeholder
        statement = "SELECT sv_id, sv_name FROM Supervisor WHERE sv_name = %s"
        cursor = db_conn.cursor()
        cursor.execute(statement, (supe,))

        # Fetch the result
        result = cursor.fetchone()

        if result:
            sv_id, sv_name = result
            return render_template('searchSupervisor.html', name=sv_name, id=sv_id)
        else:
            return render_template('searchSupervisorError.html', id=supe)
        
    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        
@app.route("/managesupervisor", methods=['GET'])
def ManageSupervisor():
    sv_id = 1
    statement = "SELECT sv_id, sv_name, email, programme, faculty From Supervisor WHERE sv_id = %s"
    cursor = db_conn.cursor()
    cursor.execute(statement, (sv_id))
    result = cursor.fetchall()
    cursor.close()
    
    return render_template('ManageSupervisor.html', data=result)

@app.route('/viewsupervisor/<int:sv_id>')
def view_supervisor(sv_id):
    statement = "SELECT * FROM Supervisor WHERE sv_id = %s"
    cursor = db_conn.cursor()
    cursor.execute(statement, (sv_id))
    result = cursor.fetchone()

    return render_template('ViewSupervisor.html', supervisor=result)

@app.route('/editsupervisor/<int:sv_id>')
def edit_supervisor(sv_id):
    statement = "SELECT * FROM Supervisor WHERE sv_id = %s"
    cursor = db_conn.cursor()
    cursor.execute(statement, (sv_id))
    result = cursor.fetchone()

    return render_template('ViewSupervisor.html', supervisor=result)

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
