from flask import Flask, render_template, request, redirect, url_for, flash, session, logging, request, jsonify
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, DecimalField
from wtforms.validators import InputRequired
from passlib.hash import sha256_crypt
from functools import wraps
from decimal import Decimal
import json
import os


app = Flask(__name__)
app.secret_key='secret123'

#Config flask_mysqldb
app.config['MYSQL_HOST'] = 'us-cdbr-iron-east-01.cleardb.net'
app.config['MYSQL_USER'] = 'b42c12cefdb6bd'
app.config['MYSQL_PASSWORD'] = '7d5f7fcc'
app.config['MYSQL_DB'] = 'heroku_c4fb624a7366a09'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL
mysql = MySQL(app)

#route for home page
@app.route("/")
def home():

    return render_template("home.html")

#route for about page
@app.route("/about")
def about():
    return render_template("about.html")

#Register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
     ])
    confirm = PasswordField('Confirm Password')

#User register
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create cursor
        cur = mysql.connection.cursor()

        #Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #commit to db
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

#User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get FORM Fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Create cursor
        cur = mysql.connection.cursor()

        #Get user by Username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get storted hash
            data = cur.fetchone()
            password = data['password']

            #Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                #Passwords match
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('profile'))

            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

#Check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, Please log in', 'danger')
            return redirect(url_for('login'))
    return wrap

#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


#route for profile page
@app.route('/profile')
@is_logged_in
def profile():
    #Create Cursor
    cur = mysql.connection.cursor()
    username = session['username']

    #Get list of spendings from current logged in user
    result = cur.execute("SELECT * FROM spendings WHERE user = %s ORDER BY register_date DESC", [username])

    spendings = cur.fetchall()

    if result > 0:
        return render_template('profile.html', spendings=spendings)
    else:
        msg = 'No amounts found'
        return render_template('profile.html', msg=msg)

    #CLose connection
    cur.close()

#Add spending amount
class AddSpending(Form):
    spending = DecimalField('Amount', places=2, validators=[InputRequired()])
    description = StringField('Description', [validators.Length(min=1, max=200)])

#route to add spending for user
@app.route('/add_spending', methods=['GET', 'POST'])
@is_logged_in
def add_spending():
    form = AddSpending(request.form)
    if request.method == 'POST' and form.validate():
        spending = form.spending.data
        description = form.description.data

        #create cursor
        cur = mysql.connection.cursor()

        #Execute
        cur.execute("INSERT INTO spendings(spending, description, user) VALUES (%s, %s, %s)", (spending, description, session['username']))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('Spending has been saved', 'success')

        return(redirect(url_for('profile')))

    return render_template('add_spending.html', form=form)

#Route to display the spendings in the last three days
@app.route('/profile/three_days')
@is_logged_in
def three_days():
    #Create Cursor
    cur = mysql.connection.cursor()
    username = session['username']

    #Get list of spendings from from the last three days from the current user
    result = cur.execute("SELECT * FROM spendings WHERE register_date >= (DATE(NOW()) - INTERVAL 3 DAY) AND user = %s ORDER BY register_date DESC", [username])

    spendings = cur.fetchall()

    if result > 0:
        return render_template('profile.html', spendings=spendings)
    else:
        msg = 'No amounts found'
        return render_template('profile.html', msg=msg)

    #CLose connection
    cur.close()

#Route to display the spendings for the last week
@app.route('/profile/last_week')
@is_logged_in
def last_week():
    #Create Cursor
    cur = mysql.connection.cursor()
    username = session['username']

    #Get list of spendings from from the last seven days from the current user
    result = cur.execute("SELECT * FROM spendings WHERE register_date >= (DATE(NOW()) - INTERVAL 7 DAY) AND user = %s ORDER BY register_date DESC", [username])

    spendings = cur.fetchall()

    if result > 0:
        return render_template('profile.html', spendings=spendings)
    else:
        msg = 'No amounts found'
        return render_template('profile.html', msg=msg)

    #CLose connection
    cur.close()

#Route to display the spendings for the last month
@app.route('/profile/last_month')
@is_logged_in
def last_month():
    #Create Cursor
    cur = mysql.connection.cursor()
    username = session['username']

    #Get list of spendings from from the last thirty days from the current user
    result = cur.execute("SELECT * FROM spendings WHERE register_date >= (DATE(NOW()) - INTERVAL 30 DAY) AND user = %s ORDER BY register_date DESC", [username])

    spendings = cur.fetchall()

    if result > 0:
        return render_template('profile.html', spendings=spendings ,pred=result)
    else:
        msg = 'No amounts found'
        return render_template('profile.html', msg=msg)

    #CLose connection
    cur.close()


@app.route('/delete_spending/<string:id>', methods=['POST'])
@is_logged_in
def delete_spending(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM spendings WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Spending Deleted', 'success')

    return redirect(url_for('profile'))

#route to edit spending for user
@app.route('/edit_spending/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_spending(id):
    cur = mysql.connection.cursor()

    #Get spending by id
    result = cur.execute("SELECT * FROM spendings WHERE id=%s", [id])

    spendings = cur.fetchone()

    form = AddSpending(request.form)

    #populate Fields
    form.spending.data = spendings['spending']
    form.description.data = spendings['description']

    if request.method == 'POST' and form.validate():
        spending = request.form['spending']
        description = request.form['description']

        #create cursor
        cur = mysql.connection.cursor()

        #Execute
        cur.execute("UPDATE spendings SET spending=%s, description=%s WHERE id = %s", (spending, description, id))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('Spending has been updated', 'success')

        return(redirect(url_for('profile')))

    return render_template('edit_spending.html', form=form)

if __name__ == "__main__":
    app.run(debug=True)
