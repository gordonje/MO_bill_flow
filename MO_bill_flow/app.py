########## IMPORTS (DON'T CHANGE THESE) ##########

import os
import sqlite3
import json
from flask import Flask, g, render_template, make_response

app = Flask(__name__)
app.config.from_object(__name__)

########## SETTINGS (CHANGE THESE AS APPROPRIATE) ##########

DATABASE = 'DBs/bills_2014.sqlite'
USERNAME = ''
PASSWORD = ''

########## DATABASE CONNECTION BOILERPLATE (DO NOT CHANGE THIS) ##########

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, DATABASE),
    DEBUG=True,
    SECRET_KEY='',
    USERNAME=USERNAME,
    PASSWORD=PASSWORD
))

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

########## APP CODE (YOUR FUNCTION GOES HERE) ##########

@app.route("/")
def hello():
    return 'Hello, World.'

@app.route("/house_bills")
def bills():
    connection = get_db()
    cursor = connection.execute('select count(*) as Bill_Count from house_bills;')

    house_bills = []
    for row in cursor.fetchall():
        house_bills.append(dict(row))

    template = json.dumps(house_bills)

    response = make_response(template)
    response.headers['Content-Type'] = 'applicaton/json'
    return response

@app.route("/senate_bills")
def bills():
    connection = get_db()
    cursor = connection.execute('select count(*) as Bill_Count from senate_bills;')

    senate_bills = []
    for row in cursor.fetchall():
        senate_bills.append(dict(row))

    template = json.dumps(senate_bills)

    response = make_response(template)
    response.headers['Content-Type'] = 'applicaton/json'
    return response

########## EXECUTION BOILERPLATE (ALSO DON'T CHANGE THIS) ##########

if __name__ == "__main__":
    app.run(debug=True)