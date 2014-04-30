from datetime import datetime
import sqlite3

start_time = datetime.now()

request_year = start_time.year

target_db = 'DBs/bills_' + str(request_year) + '.sqlite'

conn = sqlite3.connect(target_db)
conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
c = conn.cursor()

# This is our mapping of actions descriptions to legislative stages. May change as we learn more about the legislative process.
c.execute('''UPDATE house_actions  
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

# Need to test if this exists, then drop it if so
c.execute('''DROP TABLE IF EXISTS house_numbers''')

conn.commit()

c.execute('''CREATE TABLE house_numbers (
	stage VARCHAR(15) NOT NULL,
	all_bills INTEGER NULL,
	dem_bills INTEGER NULL,
	rep_bills INTEGER NULL
	)'''
)

c.execute('''INSERT INTO house_numbers (stage) SELECT stage FROM house_actions WHERE stage IS NOT NULL GROUP BY stage''')
conn.commit()

stages = []
for row in c.execute('''SELECT DISTINCT stage FROM house_actions WHERE stage IS NOT NULL;''').fetchall():
	stages.append(row[0])

for stage in stages:
	c.execute('''UPDATE house_numbers 
		SET all_bills = (
			SELECT count(*) 
			FROM house_bills 
			WHERE bill_type + bill_number IN (
				select bill_type + bill_number
				from house_actions 
				where stage = ?
				)
		),
		dem_bills = (
			SELECT count(*) 
			FROM house_bills
			JOIN representatives
			ON representatives.district = house_bills.sponsor_district 
			WHERE bill_type + bill_number IN (
				SELECT bill_type + bill_number 
				FROM house_actions 
				WHERE stage = ?
				)
			and representatives.party = 'Democrat'
			),
		rep_bills = (
			SELECT count(*) 
			FROM house_bills
			join representatives
			ON representatives.district = house_bills.sponsor_district 
			WHERE bill_type + bill_number in (
				SELECT bill_type + bill_number 
				FROM house_actions 
				WHERE stage = ?
				)
			AND representatives.party = 'Republican'
			)
		WHERE stage = ?
	''', (stage, stage, stage, stage))
	conn.commit()

conn.close()
