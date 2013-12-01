import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from geopy.geocoders import GoogleV3
import re

# configuration
DATABASE = './activity_finder.db'
DEBUG=True
SECRET_KEY='development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create the application
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def address_validator(address):
    address = re.sub("b.c.", "bc", address.lower())
    geolocator = GoogleV3()
    geocoded_address, (latitude, longitude) = geolocator.geocode(address)
    geocoded_address = geocoded_address.lower()
    for x, y in zip(address.split(",")[0:2], geocoded_address.split(",")[0:2]):
        if x != y:
            raise NameError("Addresses don't match")
    return [latitude, longitude]

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def show_entries():
    cur = g.db.execute('select title, description from entries order by id desc')
    entries = [dict(title=row[0], description=row[1]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)




# add validation 
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    form_input_fields = ('title', 'description', 'address', 'min_age', 'max_age', 'schedule', 'fee')
    form_input_data = []
    for form_input_field in form_input_fields:
        form_input_data.append(request.form[form_input_field])
    try:
        lat_long = address_validator(form_input_data[2])
        g.db.execute('insert into entries (title, description, address, min_age, max_age, schedule, fee, lat, long) values (?, ?, ?, ?, ?, ?, ?, ?, ?)', form_input_data+lat_long)
        g.db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('show_entries'))
    except:
        flash('Invalid address entered.')
        return redirect(url_for('show_entries'))





@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password.'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run()
