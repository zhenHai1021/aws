from curses import flash
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask import Flask, render_template, request, redirect, flash, jsonify
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
#encrypt
csrf = CSRFProtect(app)

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
    return redirect('/viewadmin')

@app.route("/Dashboard", methods=['GET', 'POST'])
def AddingAdmin():
    return render_template('Dashboard.html')

@app.route("/Supervisor", methods=['GET', 'POST'])
def ManagingSupervisor():
    return redirect('/viewsupervisor')

@app.route("/Create", methods=['GET', 'POST'])
def AddingSupervisor():
    return render_template('AddSupervisor.html')

@app.route("/StudentApp", methods=['GET', 'POST'])
def ApprovingStudent():
    return redirect('/studentapproval')

@app.route("/CompanyApp", methods=['GET', 'POST'])
def ApprovingCompany():
    return redirect('/companyapproval')

@app.route('/addadmin', methods=['POST', 'GET'])
@csrf.exempt 
def add_admin():
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor = db_conn.cursor()
        cursor.execute("INSERT INTO Admin (id, name, email, password) VALUES (%s, %s, %s, %s)", (id, name, email, password))
        db_conn.commit()

        # Redirect to a success page or do something else as needed
        return redirect('/viewadmin')

    return render_template('AdminIndex.html')  

@app.route('/viewadmin', methods=['GET'])
def view_admin():
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM Admin")
        admins = cursor.fetchall()
        cursor.close()

        return render_template('AdminIndex.html', admins=admins)

    except Exception as e:
        return str(e)

@app.route('/deleteadmin', methods=['POST', 'GET'])
def delete_admin():
     if request.method == 'POST':
        id=request.form['id']

        delete_sql="DELETE FROM Admin WHERE id = %s"
        cursor = db_conn.cursor()
        cursor.execute(delete_sql, (id))
        db_conn.commit()
        cursor.close()

        return redirect('/viewadmin')
     return "Method Not Allowed", 405  # Handle GET requests with an error response


@app.route("/addsupervisor", methods=['POST'])
@csrf.exempt  
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

    return redirect('/Supervisor')
   # return render_template('AddSupOutput.html', name=sv_name, email=sv_email, programme=programme, faculty=faculty, age=age, object_url=object_url)


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
        
@app.route("/viewsupervisor", methods=['GET'])
def ViewSupervisor():
    try:
        statement = "SELECT sv_id, sv_name, sv_email, programme, faculty, age, profile_image FROM Supervisor"
        cursor = db_conn.cursor()
        cursor.execute(statement)

        # Fetch all the results
        results = cursor.fetchall()

        supervisors = []  # List to store supervisor data

        for result in results:
            sv_id, sv_name, sv_email, programme, faculty, age, profile_image = result
            supervisors.append({
                'sv_id': sv_id,
                'sv_name': sv_name,
                'sv_email': sv_email,
                'programme': programme,
                'faculty': faculty,
                'age': age,
                'profile_image': profile_image,
            })

        return render_template('ViewSupervisor.html', supervisors=supervisors)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/deletesupervisor", methods=['POST', 'GET'])
def DeleteSupervisor():
    if request.method == 'POST':
        sv_id = request.form['sv_id']

        # SQL statement to delete a supervisor by sv_id
        delete_sql = "DELETE FROM Supervisor WHERE sv_id = %s"
        cursor = db_conn.cursor()
        cursor.execute(delete_sql, (sv_id,))
        db_conn.commit()
        cursor.close()
        
        return redirect("/viewsupervisor")

    return "Method Not Allowed", 405  # Handle GET requests with an error response


@app.route("/studentapproval", methods=['GET'])
def StudAproval():
    try:
        statement = "SELECT id, stud_id, status FROM StudApproval WHERE status = %s"
        cursor = db_conn.cursor()
        cursor.execute(statement, ("pending"))

        # Fetch all the results
        results = cursor.fetchall()

        stud_approvals = []  # List to store StudApproval data

        for result in results:
            id, stud_id, status = result
            stud_approvals.append({
                'id': id,
                'stud_id': stud_id,
                'status': status,
            })

        return render_template('StudentApproval.html', stud_approvals=stud_approvals)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/updatestudentstatus", methods=['POST', 'GET'])
@csrf.exempt  
def UpdateStudStatus():
    try:
        id = request.form['id']
        new_status = request.form['status']

        # SQL statement to update the status of a StudApproval entry by id
        update_sql = "UPDATE StudApproval SET status = %s WHERE id = %s"
        cursor = db_conn.cursor()
        cursor.execute(update_sql, (new_status, id))
        db_conn.commit()
        cursor.close()
        
        return redirect("/studentapproval")

    except Exception as e:
        return str(e)

@app.route("/companyapproval", methods=['GET'])
def ComApproval():
    try:
        statement = "SELECT id, com_id, status FROM ComApproval WHERE status = %s"
        cursor = db_conn.cursor()
        cursor.execute(statement, ("pending"))

        # Fetch all the results
        results = cursor.fetchall()

        com_approvals = []  # List to store StudApproval data

        for result in results:
            id, com_id, status = result
            com_approvals.append({
                'id': id,
                'com_id': com_id,
                'status': status,
            })

        return render_template('CompanyApproval.html', com_approvals=com_approvals)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/updatecompanystatus", methods=['POST', 'GET'])
@csrf.exempt  
def UpdateComStatus():
    try:
        id = request.form['id']
        new_status = request.form['status']

        # SQL statement to update the status of a StudApproval entry by id
        update_sql = "UPDATE ComApproval SET status = %s WHERE id = %s"
        cursor = db_conn.cursor()
        cursor.execute(update_sql, (new_status, id))
        db_conn.commit()
        cursor.close()
        
        return redirect("/companyapproval")

    except Exception as e:
        return str(e)



    
if __name__ == '__main__':
    app.secret_key = 'zhenwei_key'
    app.run(host='0.0.0.0', port=80, debug=True)
