from datetime import datetime
from os import path
import shutil
import sqlite3
import requests
import scrapers
from time import sleep
from sys import stdout

start_time = datetime.now()
print "Started at " + str(start_time) + "."

request_year = start_time.year

target_db = '../DBs/bills_' + str(request_year) + '.sqlite'

########## Connecting to / setting up the database ##########

# if there's already a database, archive it
if path.exists(target_db):
	print "Archiving old database..."
	time_str = str(start_time.date()) + "-" + str(start_time.hour) + str(start_time.minute) + str(start_time.second)
	shutil.copy2(target_db, '../DBs/Archive/bills_' + time_str + '.sqlite')

conn = sqlite3.connect(target_db)
conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
c = conn.cursor()

print 'Deleting old Senate records...'

c.execute('''DELETE FROM senate_bills''')
c.execute('''DELETE FROM senate_actions''')
c.execute('''DELETE FROM senate_bills_cosponsors''')
c.execute('''DELETE FROM senate_bills_topics''')
c.execute('''DELETE FROM senators''')

conn.commit()

########## Gathering bill ids ##########

session = requests.Session()
session.headers.update({"Connection": "keep-alive"})

print "Getting bills..."

all_senate_bills = []

for i in scrapers.get_senate_bills(request_year, session):
	all_senate_bills.append(i)

totalBills = len(all_senate_bills) - 247
currentBillCount = 0

print "There are " + str(totalBills) + " bills to download (Approximately " + str((totalBills * 16) / 60) + " minutes to complete)."

########## Getting bill info ##########

for i in all_senate_bills:

	sleep(5)

	bill_info = scrapers.get_senate_bill_info(i, session)

	bill_output= [
		bill_info['bill_type'],
		bill_info['bill_number'],
		bill_info['url_id'],
		bill_info['brief_desc'],
		bill_info['sponsor'],
		bill_info['lr_number'],
		bill_info['committee'],
		bill_info['last_action_date'],
		bill_info['last_action_desc'],
		bill_info['effective_date'],
		bill_info['summary']
	]

	c.execute('''INSERT INTO senate_bills (
					bill_type,
					bill_number,
					url_id,
					brief_desc,
					sponsor,
					lr_number,
					committee,
					last_action_date,
					last_action_desc,
					effective_date,
					summary)
				VALUES (?,?,?,?,?,?,?,?,?,?,?)''', bill_output)
	conn.commit()

########## Getting actions ##########

	sleep(5)

	actions_output = scrapers.get_senate_actions(i, session)

	c.executemany('''INSERT INTO senate_actions (
						bill_type, 
						bill_number, 
						action_date, 
						action_desc)
					VALUES (?,?,?,?)''', actions_output)
	conn.commit()

########## Getting cosponsors ##########

	if bill_info['has_cosponsors']:

		sleep(3)

		cosponsors_output = scrapers.get_senate_bill_cosponsors(i, session)

		c.executemany('''INSERT INTO senate_bills_cosponsors (
							bill_type,
							bill_number,
							cosponsor_name,
							cosponsor_district)
						VALUES (?,?,?,?)''', cosponsors_output)
		conn.commit()

########## Keeping track of where we are ##########

	currentBillCount += 1

	if currentBillCount < totalBills:
		stdout.write(" " + i['bill_type'] + " " + str(i['bill_number']) + " completed (" + str(currentBillCount) + " of " + str(totalBills) + ").\r")
		stdout.flush()
	else:
		print "All bills downloaded.                 "

########## Getting bill topics ##########

print "Getting topics..."

sleep(3)

topics_output = scrapers.get_senate_bill_topics(request_year, session)
	
c.executemany('''INSERT INTO senate_bills_topics (
					bill_type,
					bill_number,
					topic)
				VALUES (?,?,?)''', topics_output)
conn.commit()

########## Getting senators ##########

print "Getting Senators..."

senators_output = scrapers.get_senators(request_year, session)

c.executemany('''INSERT INTO senators (
					first_name,
					last_name,
					party,
					district) 
				VALUES (?,?,?,?)''', senators_output)
conn.commit()

########## Finishing ##########

conn.close()

duration = datetime.now() - start_time

print "Finished (ran for " + str(duration) + ")."