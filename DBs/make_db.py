from datetime import datetime
from os import path
import shutil
import sqlite3

start_time = datetime.now()

request_year = start_time.year

target_db = 'bills_' + str(request_year) + '.sqlite'

print target_db

# if there's already a database, archive it
if path.exists(target_db):
	print "Archiving old database..."
	time_str = str(start_time.date()) + "-" + str(start_time.hour) + str(start_time.minute) + str(start_time.second)
	shutil.copy2(target_db, 'DBs_Archive/bills_' + time_str + '.sqlite')

conn = sqlite3.connect(target_db)
conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
c = conn.cursor()

####### House tables #######

c.execute('''CREATE TABLE house_bills (
	bill_type VARCHAR(4) NOT NULL,
	bill_number INTEGER NOT NULL,
	url_id VARCHAR(15) NOT NULL,
	bill_string VARCHAR(15) NOT NULL,
	brief_desc TEXT NOT NULL,
	sponsor_first_name VARCHAR(20) NOT NULL,
	sponsor_last_name VARCHAR(40) NOT NULL,
	sponsor_district VARCHAR(4) NOT NULL,
	lr_number VARCHAR(50) NOT NULL,
	effective_date VARCHAR(24) NULL,
	last_action_date DATE NULL,
	last_action_desc TEXT NULL,
	next_hearing VARCHAR(255) NULL,
	calendar VARCHAR(255) NULL,
	co_sponsor_text TEXT NULL,
	PRIMARY KEY (bill_type, bill_number)
	)''')

c.execute('''CREATE TABLE house_actions (
	bill_type VARCHAR(4) NOT NULL,
	bill_number INTEGER NOT NULL,
	action_date DATE NOT NULL,
	journal_page VARCHAR(25) NULL,
	action_desc TEXT NULL,
	stage VARCHAR(15) NULL,
	FOREIGN KEY(bill_type, bill_number) REFERENCES house_bills (bill_type, bill_number)
	)''')

c.execute('''CREATE TABLE house_bills_cosigners (
	bill_type VARCHAR(4) NOT NULL,
	bill_number INTEGER NOT NULL,
	cosigner_name VARCHAR(20) NOT NULL,
	signed_date_time VARCHAR(23) NOT NULL,
	FOREIGN KEY(bill_type, bill_number) REFERENCES house_bills (bill_type, bill_number)
	)''')

c.execute('''CREATE TABLE house_bills_cosponsors (
	bill_type VARCHAR(4) NOT NULL,
	bill_number INTEGER NOT NULL,
	cosponsor_name VARCHAR(20) NOT NULL,
	FOREIGN KEY(bill_type, bill_number) REFERENCES house_bills (bill_type, bill_number)
	)''')

c.execute('''CREATE TABLE house_bills_topics (
	bill_type VARCHAR(4) NOT NULL,
	bill_number INTEGER NOT NULL,
	topic VARCHAR(255),
	FOREIGN KEY(bill_type, bill_number) REFERENCES house_bills (bill_type, bill_number)
	)''')

c.execute('''CREATE TABLE representatives (
	last_name VARCHAR(60) NOT NULL,
	first_name VARCHAR(30) NOT NULL,
	district VARCHAR(4) NOT NULL,
	party VARCHAR(12) NOT NULL,
	phone VARCHAR(14) NOT NULL,
	room VARCHAR(4) NOT NULL
	)''')

###### Senate tables #######

c.execute('''CREATE TABLE senate_bills (
	bill_type VARCHAR(4) NOT NULL,
	bill_number INTEGER NOT NULL,
	url_id INTEGER NOT NULL,
	brief_desc VARCHAR(255),
	sponsor VARCHAR(20),
	lr_number VARCHAR(50),
	committee VARCHAR(20),
	last_action_date DATE,
	last_action_desc TEXT,
	effective_date VARCHAR(24),
	summary TEXT,
	PRIMARY KEY (bill_type, bill_number)
	)''')

c.execute('''CREATE TABLE senate_actions (
	bill_type VARCHAR(4) NOT NULL,
	bill_number INTEGER NOT NULL,
	action_date DATE NOT NULL,
	action_desc TEXT,
	stage VARCHAR(15) NULL,
	FOREIGN KEY(bill_type, bill_number) REFERENCES senate_bills (bill_type, bill_number)
	)''')

c.execute('''CREATE TABLE senate_bills_cosponsors (
	bill_type VARCHAR(4) NOT NULL,
	bill_number INTEGER NOT NULL,
	cosponsor_name VARCHAR(20) NOT NULL,
	cosponsor_district INTEGER NOT NULL,
	FOREIGN KEY(bill_type, bill_number) REFERENCES senate_bills (bill_type, bill_number)
	)''')

c.execute('''CREATE TABLE senate_bills_topics (
	bill_type VARCHAR(4) NOT NULL,
	bill_number INTEGER NOT NULL,
	topic VARCHAR(255),
	FOREIGN KEY(bill_type, bill_number) REFERENCES senate_bills (bill_type, bill_number)
	)''')

c.execute('''CREATE TABLE senators (
	first_name VARCHAR(30) NOT NULL,
	last_name VARCHAR(60) NOT NULL,
	party VARCHAR(1) NOT NULL,
	district INTEGER NOT NULL
	)''')

###### Stages table ######

c.execute('''CREATE TABLE leg_stages (
	chamber VARCHAR(1) NOT NULL,
	stage VARCHAR(30) NOT NULL,
	sort_order INTEGER NOT NULL
	)''')

conn.commit()
conn.close()