from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2 #pip install psycopg2 
import psycopg2.extras
 
app = Flask(__name__)
app.secret_key = "cairocoders-ednalan"
 
DB_HOST = "10.0.16.210"
DB_NAME = "demo"
DB_USER = "demo"
DB_PASS = "demo"
 
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
 
@app.route('/')
def Index():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        s = "SELECT * FROM students"
        cur.execute(s)  # Execute the SQL
        list_users = cur.fetchall()
        return render_template('index.html', list_users=list_users)
    except Exception as e:
        # Rollback the transaction if an error occurs
        conn.rollback()
        flash(f'Error fetching students: {e}', 'error')
        return render_template('index.html', list_users=[])
    finally:
        cur.close()  # Always close the cursor 

 
@app.route('/add_student', methods=['POST'])
def add_student():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']

        # Check if the email already exists in the database
        cur.execute("SELECT * FROM students WHERE email = %s", (email,))
        existing_student = cur.fetchone()
        
        if existing_student:
            flash('Email already exists. Please use a different email.', 'error')
        else:
            try:
                cur.execute("INSERT INTO students (fname, lname, email) VALUES (%s,%s,%s)", (fname, lname, email))
                conn.commit()
                flash('Student Added successfully')
            except Exception as e:
                conn.rollback()  # Rollback in case of any error
                flash(f'Error: {e}', 'error')           
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
        
        # Check if the new email already exists for another student
        cur.execute("SELECT * FROM students WHERE email = %s AND id != %s", (email, id))
        existing_student = cur.fetchone()
        
        if existing_student:
            flash('Email already exists. Please use a different email.', 'error')
            return redirect(url_for('get_employee', id=id))
        
        try:
            # Proceed with the update if email is unique
            cur.execute("""
                UPDATE students
                SET fname = %s,
                    lname = %s,
                    email = %s
                WHERE id = %s
            """, (fname, lname, email, id))
            conn.commit()
            flash('Student Updated Successfully')
        except Exception as e:
            conn.rollback()  # Rollback if there's an error
            flash(f'Error: {e}', 'error')
        finally:
            cur.close()

        return redirect(url_for('Index'))

		
@app.route('/delete/<string:id>', methods=['POST', 'GET'])
def delete_student(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Perform the deletion
        cur.execute('DELETE FROM students WHERE id = %s', (id,))
        conn.commit()
        
        # Reset the sequence to the maximum id in the students table
        cur.execute('SELECT setval(\'students_id_seq\', (SELECT MAX(id) FROM students));')
        conn.commit()
        
        flash('Student Removed Successfully')
    except Exception as e:
        conn.rollback()  # Rollback in case of error
        flash(f'Error: {e}', 'error')
    finally:
        cur.close()

    return redirect(url_for('Index'))


 
if __name__ == "__main__":
    app.run(debug=True)
#</string:id></id></id>
