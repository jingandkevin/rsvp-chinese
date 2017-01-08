from flask import Flask, render_template, flash, redirect, session, url_for, request, g, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, BooleanField, TextAreaField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired
import os
import sys
import pandas as pd

# initializing the Flask app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

############################################
#
# Configuration
#
############################################

# configuration settings
app.config.update(dict(
	WTF_CSRF_ENABLED = True,
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir, 'app.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
	BOOTSTRAP_SERVE_LOCAL = True,
    SECRET_KEY='HuiphI5wmXy1pyN5',
))

# set up our user database connection
db = SQLAlchemy(app)

# give the app access to the bootstrap css/js for pretty websites
bootstrap = Bootstrap(app)

# set up the login manager
loginmanager = LoginManager()
loginmanager.init_app(app)

# point the app to the login page if an unauthenticated
# user tries to access a login_required page
loginmanager.login_view = "login"

############################################
#
# Forms
#
############################################

class RSVPForm(Form):
    name = StringField('', validators=[DataRequired()])
    email = StringField('', validators=[DataRequired()])
    attending = SelectField(choices=[('',''),('1', "Yes"), ('0', 'No')], validators=[DataRequired()])
    plusone = SelectField(choices=[('',''),('1', 'Yes'), ('0', 'No')], validators=[DataRequired()])
    plusonename = StringField('')
    message = TextAreaField('')
    street = StringField('')
    city = StringField('')
    state = StringField('')
    zipcd = StringField('')
    submit = SubmitField('Submit')

class LoginForm(Form):
	user = StringField('', validators=[DataRequired()])
	password = PasswordField('', validators=[DataRequired()])
	submit = SubmitField('Submit')

############################################
#
# Database models (i.e. tables)
#
############################################

# our user table to keep track of who is allowed
# to see our webpage, how many times they've logged in,
# and when they last logged in.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    attending = db.Column(db.Integer, unique=True)
    plusone = db.Column(db.Integer, unique=True)
    plusonename = db.Column(db.String(64), unique=True)
    message = db.Column(db.String(500), unique=True)
    street = db.Column(db.String(120), unique=True)
    city = db.Column(db.String(120), unique=True)
    state = db.Column(db.String(64), unique=True)
    zipcd = db.Column(db.Integer, unique=True)

    def __repr__(self):
        return self.name

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

class Admin(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user = db.Column(db.String(64), index=True, unique=True)

	def __repr__(self):
		return self.user

	@property
	def is_authenticated(self):
		return True

	@property
	def is_active(self):
		return True

	@property
	def is_anonymous(self):
		return False

	def get_id(self):
		try:
			return unicode(self.id)
		except NameError:
			return str(self.id)

############################################
#
# Views
#
############################################

@app.before_request
def before_request():
    g.user = current_user

@loginmanager.user_loader
def load_user(id):
    return Admin.query.get(int(id))

@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    # create an instance of the rsvp form
    form = RSVPForm()
    if request.method == 'GET':
        return render_template('rsvp.html', form=form)
    # check if form is valid
    if form.validate_on_submit():
        u = User()
        u.name = request.form['name']
        u.email = request.form['email'].lower()
        u.attending = request.form['attending']
        u.plusone = request.form['plusone']
        u.plusonename = request.form['plusonename']
        u.message = request.form['message']
        u.street = request.form['street']
        u.city = request.form['city']
        u.state = request.form['state']
        u.zipcd = request.form['zipcd']
        db.session.add(u)
        db.session.commit()
        login_user(u)
        return redirect('https://jingandkevin.github.io/travel/')

    else:
        for fieldName, errorMessages in form.errors.iteritems():
            for err in errorMessages:
                flash(fieldName.capitalize() + ' ' + err[-12:], 'warning')
        return render_template('rsvp.html', title='RSVP', form=form)
	return render_template('rsvp.html', title='RSVP', form=form)

@app.route('/decline')
def decline():
	u = User()
	u.name = request.args.get('name')
	u.email = request.args.get('email')
	u.attending = u.plusone = 0
	u.message = request.remote_addr + ',' + request.user_agent.platform + ',' + request.user_agent.browser
	db.session.add(u)
	db.session.commit()
	return redirect('https://jingandkevin.github.io/sorry/')
# jingandkevin.pythonanywhere.com/decline?name=FIRST%20LAST&email=EMAIL%40GMAIL%2Ecom

@app.route('/guestlist')
@login_required
def guestlist():
	guests = User.query.all()
	guestcount = 0
	for guest in guests:
		if guest.attending:
			guestcount += 1
		if guest.plusone:
			guestcount += 1
	return render_template('guestlist.html', guests=guests, guestcount=guestcount)

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = Admin.query.filter_by(user=request.form['user']).first()
		if user is not None and request.form['password'] == 'stinky':
			login_user(user)
			flash('Logged in successfully.')
			return redirect(url_for('guestlist'))
		else:
			flash('Logged in successfully.')
			return render_template('login.html', form=form)
	return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=31337)
	app.run(debug=True)
