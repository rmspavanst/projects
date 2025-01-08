# py_flask_pg


## Python Flask Student Create, read, update and delete (CRUD) using PostgreSQL psycopg2 and dataTables bootstrap

install psycopg2 https://pypi.org/project/psycopg2/
Psycopg is the most popular PostgreSQL database adapter for the Python programming language.
(venv) PS C:\flaskmyproject> pip install psycopg2

Crate database table
CREATE TABLE students (
	id serial PRIMARY KEY,
	fname VARCHAR ( 40 ) NOT NULL,
	lname VARCHAR ( 40 ) NOT NULL,
	email VARCHAR ( 40 ) NOT NULL
);

SELECT * FROM students

INSERT INTO students (id, fname, lname, email)
VALUES('1','Mark','Oto', 'Oto@gmail.com'),

Insert multiple records
INSERT INTO
    students(id,fname,lname,email)
VALUES
    ('2','Quinn','Flynn'', 'Flynn'@gmail.com'),
    ('3','Tiger','nizon', 'nizon@gmail.com'),
    ('4','Airi','sato', 'sato@gmail.com');

How to Alter Sequence in PostgreSQL

To alter the sequence so that IDs start a different number, you can't just do an update, you have to use the alter sequence command.

alter sequence students_id_seq restart with 9;
ALTER SEQUENCE students_id_seq RESTART WITH 1;
ALTER TABLE students ADD CONSTRAINT unique_email UNIQUE (email);

# troubleshoot
\d students
                                   Table "public.students"
 Column |         Type          | Collation | Nullable |               Default
--------+-----------------------+-----------+----------+--------------------------------------
 id     | integer               |           | not null | nextval('students_id_seq'::regclass)
 fname  | character varying(40) |           | not null |
 lname  | character varying(40) |           | not null |
 email  | character varying(40) |           | not null |
Indexes:
    "students_pkey" PRIMARY KEY, btree (id)
    "unique_email" UNIQUE CONSTRAINT, btree (email)

demo=> SELECT setval('students_id_seq', (SELECT MAX(id) FROM students));



## app.py
=============

#app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2 #pip install psycopg2 
import psycopg2.extras
 
app = Flask(__name__)
app.secret_key = "cairocoders-ednalan"
 
DB_HOST = "localhost"
DB_NAME = "sampledb"
DB_USER = "postgres"
DB_PASS = "P@ssw0rd"
 
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
 
@app.route('/')
def Index():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    s = "SELECT * FROM students"
    cur.execute(s) # Execute the SQL
    list_users = cur.fetchall()
    return render_template('index.html', list_users = list_users)
 
@app.route('/add_student', methods=['POST'])
def add_student():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        cur.execute("INSERT INTO students (fname, lname, email) VALUES (%s,%s,%s)", (fname, lname, email))
        conn.commit()
        flash('Student Added successfully')
        return redirect(url_for('Index'))
 
@app.route('/edit/<id>', methods = ['POST', 'GET'])
def get_employee(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    cur.execute('SELECT * FROM students WHERE id = %s', (id))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit.html', student = data[0])
 
@app.route('/update/<id>', methods=['POST'])
def update_student(id):
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
         
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE students
            SET fname = %s,
                lname = %s,
                email = %s
            WHERE id = %s
        """, (fname, lname, email, id))
        flash('Student Updated Successfully')
        conn.commit()
        return redirect(url_for('Index'))
		
@app.route('/delete/<string:id>', methods = ['POST','GET'])
def delete_student(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    cur.execute('DELETE FROM students WHERE id = {0}'.format(id))
    conn.commit()
    flash('Student Removed Successfully')
    return redirect(url_for('Index'))
 
if __name__ == "__main__":
    app.run(debug=True)
</string:id></id></id>




## templates/index.html
=========================

//templates/index.html
{% extends "layout.html" %}
{% block body %}
 <div class="row"><h3>Students</h3></div>
  <div class="row">
    <div class="col-md-4">
      {% with messages = get_flashed_messages()  %}
      {% if messages %}
      {% for message in messages %}
      <div class="alert alert-success alert-dismissible fade show" role="alert">
        {{ message }}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">×</span>
        </button>
      </div>
      {% endfor %}
      {% endif %}
      {% endwith %}
      <div class="card card-body">
        <form action="{{url_for('add_student')}}" method="POST">
          <div class="form-group">
            <input type="text" class="form-control" name="fname" placeholder="First Name">
          </div>
          <div class="form-group">
            <input type="text" class="form-control" name="lname" placeholder="Last Name">
          </div>
          <div class="form-group">
            <input type="email" class="form-control" name="email" placeholder="Email">
          </div>
          <button class="btn btn-primary btn-block">
            Save 
          </button>
        </form>
      </div>
    </div>
    <div class="col-md-8">
      <table id="example" class="table table-striped table-bordered" style="width:100%">
        <thead>
          <tr>
            <td>ID</td>
            <td>First Name</td>
            <td>Last Name</td>
            <td>Email</td>
            <td>Action</td>
          </tr>
        </thead>
        <tbody>
          {% for row in list_users %}
          <tr>
            <td>{{row[0]}}</td>
            <td>{{row[1]}}</td>
            <td>{{row[2]}}</td>
            <td>{{row[3]}}</td>
            <td width="130">
              <a href="/edit/{{row[0]}}" class="btn btn-secondary btn-sm">edit</a>
              <a href="/delete/{{row[0]}}" class="btn btn-danger btn-delete btn-sm">delete</a>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
  
{% endblock %}



## templates/layout.html

//templates/layout.html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>Python Flask Student Create, read, update and delete (CRUD) using PostgreSQL psycopg2 and dataTables bootstrap</title>
<link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" rel="stylesheet" id="bootstrap-css">
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>  
  
<script src="https://cdn.datatables.net/1.10.16/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.10.16/js/dataTables.bootstrap4.min.js"></script>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
      <a class="navbar-brand" href="/">Python Flask Student Create, read, update and delete (CRUD) using PostgreSQL psycopg2 and dataTables bootstrap</a>
    </nav>
  
    <div class="container pt-4">
      {% block body %}
      {% endblock %}
    </div>
   
<script>
const btnDelete= document.querySelectorAll('.btn-delete');
if(btnDelete) {
  const btnArray = Array.from(btnDelete);
  btnArray.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if(!confirm('Are you sure you want to delete it?')){
        e.preventDefault();
      }
    });
  })
}
  
$(document).ready(function() {
    $('#example').DataTable({     
      "aLengthMenu": [[3, 5, 10, 25, -1], [3, 5, 10, 25, "All"]],
        "iDisplayLength": 3
       } 
    );
} );
  
</script>
  </body>
</html>


###templates/edit.html


//templates/edit.html
{% extends "layout.html" %}
{% block body %}
  <div class="row">
    <div class="col-md-4 offset-md-4">
      <div class="card card-body">
        <form action="/update/{{student.id}}" method="POST">
          <div class="form-group">
            <input type="text" name="fname" value="{{student.fname}}" class="form-control">
          </div>
          <div class="form-group">
            <input type="text" name="lname" value="{{student.lname}}" class="form-control">
          </div>
          <div class="form-group">
            <input type="text" name="email" value="{{student.email}}" class="form-control">
          </div>
          <div class="form-group">
            <button type="submit" class="btn btn-primary btn-block">
              Update
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
{% endblock %}


==========================================================

dockerize:

# https://tecadmin.net/how-to-create-and-run-a-flask-application-using-docker/



1.Let’s begin with creating a new directory:
mkdir flask-app && flask-app 

2.Next, create the Python virtual environment and then activate the environment.
python3 -m venv venv 
source venv/bin/activate 

3.Now install the Flask python module under the virtual environment.
pip install Flask 

4.The below command will create the requirements.txt file with the installed packages under the current environment. This file is useful for installing module at deployments.
pip freeze > requirements.txt 

5.Now, create a sample Flask application.. You can write your code in a .py file and run it with the python command.
vi app.py 


Ex:

# Import flask module
from flask import Flask
 
app = Flask(__name__)
 
@app.route('/')
def index():
    return 'Hello to Flask!'
 
# main driver function
if __name__ == "__main__":
    app.run()


flask run --host 0.0.0.0 --port 5000 

nohup python3 -m flask run --host=0.0.0.0 --port=5000 > logs_$(date +"%Y-%m-%d").log 2>&1 &
nohup python3 -m flask run --host=0.0.0.0 --port=5000 > logs_$(date +"%Y-%m-%d_%H-%M-%S").log 2>&1 &

ps aux | grep flask
kill -9 <PID>

# Create a Dockerfile for Your Flask Application


vi Dockerfile 

FROM python:3-alpine

# Create app directory
WORKDIR /app

# Install app dependencies
COPY requirements.txt ./

RUN pip install -r requirements.txt

# Bundle app source
COPY . .

EXPOSE 5000
CMD [ "flask", "run","--host","0.0.0.0","--port","5000"]


2.Next, create the Docker image by running the below-mentioned command. Here “flask-app” is the image name.
docker build -t flask-app . 

3.This image will be created in local image registry. Then you can create a Docker container with the following command.
sudo docker run -it -p 5000:5000 -d flask-app  

4.Now, verify that container is running on your system.
docker containers ls 
		
		
		
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		
		
