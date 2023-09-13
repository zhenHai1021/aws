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
    return render_template('AddSupervisor.html')

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

    insert_sql = "INSERT INTO Supervisor VALUES (%s, %s, %s, %s, %s, %s. %s)"
    cursor = db_conn.cursor()

    if profile_image.filename == "":
        return "Please add a profile picture"
    
    if not allowed_file(profile_image.filename):
        return "File type not allowed. Only images (png, jpg, jpeg, gif) and PDFs are allowed."
    
    try:
        cursor.execute(insert_sql, (sv_id, sv_name, sv_email, programme, faculty, age, password))
        db_conn.commit()

        
        # Upload image file in S3
        profile_image_in_s3 = "sv_id-" + str(sv_id) + "_image_file"
        s3 = boto3.resource('s3')
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=profile_image_in_s3, Body=profile_image)\
            
            # Generate the object URL
            object_url = f"https://{custombucket}.s3.amazonaws.com/{profile_image_in_s3}"

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddStudOutput.html', name=sv_name, email=sv_email, programme=programme, 
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

@app.route("/viewsupervisor", methods=['POST'])
def ViewSupervisor():
    try:
        statement = "SELECT sv_id, sv_name, sv_email, programme, faculty, age, profile_image From Supervisor"
        cursor = db_conn.cursor()
        cursor.execute(statement,)

        # Fetch the result
        result = cursor.fetchone()

        if result:
            sv_id, sv_name, programme, faculty, age, profile_image = result
        return render_template('ViewSupervisor.html', name=sv_name, id=sv_id, programme=programme, faculty=faculty, age=age, profile_image=profile_image)
    
    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/view_com_approvals", methods=['GET'])
def view_com_approvals():
    try:
        statement = "SELECT id, com_id, status FROM ComApproval"
        cursor = db_conn.cursor()
        cursor.execute(statement)

        # Fetch all the results
        results = cursor.fetchall()

        com_approvals = []  # List to store company approval data

        for result in results:
            id, com_id, status = result
            com_approvals.append({
                'id': id,
                'com_id': com_id,
                'status': status
            })

        return render_template('CompanyApproval.html', com_approvals=com_approvals)
    
    except Exception as e:
        return str(e)

    finally:
        cursor.close()


@app.route("/manage_com_approval/<int:approval_id>", methods=['POST'])
def manage_com_approval(approval_id):
    try:
        new_status = request.form['status']
        statement = "UPDATE ComApproval SET status = %s WHERE id = %s"
        cursor = db_conn.cursor()
        cursor.execute(statement, (new_status, approval_id))
        db_conn.commit()
        flash("Approval status updated successfully", "success")
        return redirect("/view_com_approvals")
    
    except Exception as e:
        flash("Failed to update approval status", "error")
        return redirect("/view_com_approvals")

    finally:
        cursor.close()

@app.route("/view_stud_approvals", methods=['GET'])
def view_stud_approvals():
    try:
        statement = "SELECT id, stud_id, status FROM StudApproval"
        cursor = db_conn.cursor()
        cursor.execute(statement)

        # Fetch all the results
        results = cursor.fetchall()

        stud_approvals = []  # List to store company approval data

        for result in results:
            id, stud_id, status = result
            stud_approvals.append({
                'id': id,
                'stud_id': stud_id,
                'status': status
            })

        return render_template('CompanyApproval.html', stud_approvals=stud_approvals)
    
    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/manage_stud_approval/<int:approval_id>", methods=['POST'])
def manage_stud_approval(approval_id):
    try:
        new_status = request.form['status']
        statement = "UPDATE StudApproval SET status = %s WHERE id = %s"
        cursor = db_conn.cursor()
        cursor.execute(statement, (new_status, approval_id))
        db_conn.commit()
        flash("Approval status updated successfully", "success")
        return redirect("/view_stud_approvals")
    
    except Exception as e:
        flash("Failed to update approval status", "error")
        return redirect("/view_stud_approvals")

    finally:
        cursor.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
