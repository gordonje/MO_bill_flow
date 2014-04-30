from datetime import datetime
import sqlite3

start_time = datetime.now()

request_year = start_time.year

target_db = 'DBs/bills_' + str(request_year) + '.sqlite'

conn = sqlite3.connect(target_db)
conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
c = conn.cursor()

# This is our mapping of actions descriptions to legislative stages. May change as we learn more about the legislative process.
c.execute('''UPDATE senate_actions  
SET stage = CASE  
	WHEN Action_Desc LIKE '%Introduced%' THEN 'INTRODUCED HOUSE' 
	WHEN Action_Desc LIKE '%Prefiled%' THEN 'INTRODUCED HOUSE' 
	WHEN Action_Desc LIKE '%Offered%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE '%Read First Time%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE '%First Read%' THEN 'INTRODUCED HOUSE' 
	WHEN Action_Desc LIKE '%Read Second Time%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE '%Second Read%' THEN 'INTRODUCED HOUSE' 
	WHEN Action_Desc LIKE '%Public Hearing Completed (H)%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE '%Public Hearing Continued (H)%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE '%Public Hearing Scheduled, Bill not Heard (H)%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'Referred: %(H)' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'Rules %(H)' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'Rules - Returned%(H)' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'Action Postponed (H)' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'Placed on Informal Calendar%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE '%Read Third Time%' THEN 'INTRODUCED HOUSE'

	WHEN Action_Desc LIKE 'Third Read and Passed%(H)%' THEN 'PASS HOUSE COMMITTEE'

	WHEN Action_Desc LIKE '%Do Pass%(H)' THEN 'PASS HOUSE COMMITTEE'
	WHEN Action_Desc LIKE '%Do Pass%(S)' THEN 'PASS SENATE COMMITTEE'
	WHEN Action_Desc LIKE '%(S)%Do Pass%' THEN 'PASS SENATE COMMITTEE'
	WHEN Action_Desc LIKE 'Perfected%' THEN 'PASS HOUSE COMMITTEE'

	WHEN Action_Desc IS 'Adopted (H)' THEN 'PASS HOUSE'
	WHEN Action_Desc LIKE 'Public Hearing%(S)%' THEN 'PASS HOUSE'

	WHEN Action_Desc IS 'Adopted (S)' THEN 'PASS SENATE'
	WHEN Action_Desc IS 'Approved (H)' THEN 'PASS HOUSE'
	WHEN Action_Desc IS 'Reported to The Senate (S)' THEN 'PASS HOUSE'
	WHEN Action_Desc LIKE 'Reported to The House with%(H)%' THEN 'PASS SENATE'
	WHEN Action_Desc IS 'Approved (S)' THEN 'PASS SENATE'

	WHEN Action_Desc IS 'Delivered to Secretary of State (G)' THEN 'PASS CONFERENCE COMMITTEE'

	WHEN Action_Desc LIKE '%WITHDRAWN (H)%' THEN 'WITHDRAWN'
	ELSE NULL END;'''
)

c.execute('''DROP TABLE IF EXISTS senate_numbers''')

conn.commit()

c.execute('''CREATE TABLE senate_numbers (
	stage VARCHAR(15) NOT NULL,
	all_bills INTEGER NULL,
	dem_bills INTEGER NULL,
	rep_bills INTEGER NULL
	)'''
)

c.execute('''INSERT INTO senate_numbers (stage) SELECT stage FROM senate_actions WHERE stage IS NOT NULL GROUP BY stage''')
conn.commit()

stages = []
for row in c.execute('''SELECT DISTINCT stage FROM senate_actions WHERE stage IS NOT NULL;''').fetchall():
	stages.append(row[0])

for stage in stages:
	c.execute('''UPDATE senate_numbers 
		SET all_bills = (
			SELECT count(*) 
			FROM senate_bills 
			WHERE bill_type + bill_number IN (
				select bill_type + bill_number
				from senate_actions 
				where stage = ?
				)
		),
		dem_bills = (
			SELECT count(*) 
			FROM senate_bills
			JOIN senators
			ON senators.last_name = senate_bills.sponsor
			WHERE bill_type + bill_number IN (
				SELECT bill_type + bill_number 
				FROM senate_actions 
				WHERE stage = ?
				)
			and senators.party = 'D'
			),
		rep_bills = (
			SELECT count(*) 
			FROM senate_bills
			JOIN senators
			ON senators.last_name = senate_bills.sponsor 
			WHERE bill_type + bill_number in (
				SELECT bill_type + bill_number 
				FROM senate_actions 
				WHERE stage = ?
				)
			AND senators.party = 'R'
			)
		WHERE stage = ?
	''', (stage, stage, stage, stage))
	conn.commit()

conn.close()
