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

target_db = 'DBs/bills_' + str(request_year) + '.sqlite'

########## Connecting to / setting up the database ##########

# if there's already a database, archive it
if path.exists(target_db):
	print "Archiving old database..."
	time_str = str(start_time.date()) + "-" + str(start_time.hour) + str(start_time.minute) + str(start_time.second)
	shutil.copy2(target_db, 'DBs_Archive/bills_' + time_str + '.sqlite')

conn = sqlite3.connect(target_db)
conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
c = conn.cursor()

print 'Deleting old House records...'

c.execute('''DELETE FROM house_bills''')
c.execute('''DELETE FROM house_actions''')
c.execute('''DELETE FROM house_bills_cosigners''')
c.execute('''DELETE FROM house_bills_cosponsors''')
c.execute('''DELETE FROM house_bills_topics''')
c.execute('''DELETE FROM representatives''')

conn.commit()

########## Gathering bill ids ##########

session = requests.Session()
session.headers.update({"Connection": "keep-alive"})

print "Getting bills..."

all_house_bills = []

for i in scrapers.get_house_bills(request_year, session):
	all_house_bills.append(i)

totalBills = len(all_house_bills)
currentBillCount = 0

print "There are " + str(totalBills) + " bills to download (Approximately " + str((totalBills * 16) / 60) + " minutes to complete)."

########## Getting bill info ##########

for i in all_house_bills:

	sleep(5)

	bill_info = scrapers.get_house_bill_info(i, session)

	bill_output= [
		bill_info['bill_type'],
		bill_info['bill_number'],
		bill_info['url_id'],
		bill_info['bill_string'],
		bill_info['brief_desc'],
		bill_info['sponsor_first_name'],
		bill_info['sponsor_last_name'],
		bill_info['sponsor_district'],
		bill_info['lr_number'],
		bill_info['effective_date'],
		bill_info['last_action_date'],
		bill_info['last_action_desc'],
		bill_info['next_hearing'],
		bill_info['calendar']
	]
		
	if bill_info['has_cosponsors']:
		sleep(3)
		bill_output.append(scrapers.get_house_bill_cosponsors(i, session))
	else:
		bill_output.append('')

	c.execute('INSERT INTO house_bills VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', bill_output)
	conn.commit()

########## Getting actions ##########

	sleep(5)

	actions_output = scrapers.get_house_actions(i, session)

	c.executemany('INSERT INTO house_actions VALUES (?,?,?,?,?)', actions_output)
	conn.commit()

########## Getting cosigners ##########

	if bill_info['has_cosigners']:

		sleep(3)

		cosigners_output = scrapers.get_house_bill_cosigners(i, session)

		c.executemany('INSERT INTO house_bills_cosigners VALUES (?,?,?,?)', cosigners_output)
		conn.commit()

########## Getting cosponsors ##########



########## Keeping track of where we are ##########

	currentBillCount += 1

	if currentBillCount < totalBills:
		stdout.write(" " + i['bill_type'] + " " + str(i['bill_number']) + " completed (" + str(currentBillCount) + " of " + str(totalBills) + ").\r")
		stdout.flush()
	else:
		print "All bills downloaded.                 "

########## Getting bill topics ##########



########## Getting representatives ##########

print "Getting Reprsentatives..."

reps_output = scrapers.get_representatives(session)

c.executemany('INSERT INTO representatives VALUES (?,?,?,?,?,?)', reps_output)
conn.commit()

########## Finishing ##########

conn.close()

duration = datetime.now() - start_time

print "Finished (ran for " + str(duration) + ")."