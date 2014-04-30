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
	WHEN Action_Desc LIKE '%Introduced%' THEN 'Bill Introduced' 
	WHEN Action_Desc LIKE '%Offered%' THEN 'Bill Introduced'
	WHEN Action_Desc LIKE '%Read First Time%' THEN 'Bill Read: 1'
	WHEN Action_Desc LIKE '%First Read%' THEN 'Bill Read: 1' 
	WHEN Action_Desc LIKE '%Read Second Time%' THEN 'Bill Read: 2'
	WHEN Action_Desc LIKE '%Second Read%' THEN 'Bill Read: 2' 
	WHEN Action_Desc LIKE '%Third Read%' THEN 'Bill Read: 3'
	WHEN Action_Desc LIKE '%Read Third Time%' THEN 'Bill Read: 3'
	WHEN Action_Desc LIKE '%Referred%' THEN 'Referred to Committee' 
	WHEN Action_Desc LIKE '%Withdrawn%' THEN 'Bill Withdrawn'
	WHEN Action_Desc LIKE '%Adopted%' THEN 'Bill Passed' 
	WHEN Action_Desc LIKE '%Truly Agreed To and Finally Passed%' THEN 'Bill Passed' 
	WHEN Action_Desc LIKE '%Third Read and Passed%' THEN 'Bill Passed' 
	WHEN Action_Desc LIKE 'Adopted (S)%' THEN 'Bill Passed'
	WHEN Action_Desc LIKE 'Adopted (H)%' THEN 'Bill Passed'
	WHEN Action_Desc LIKE '%Approved by Governor%' THEN 'Governor Signed'  
	ELSE NULL END;'''
)

# Need to test if this exists, then drop it if so
c.execute('''DROP TABLE house_numbers''')

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
