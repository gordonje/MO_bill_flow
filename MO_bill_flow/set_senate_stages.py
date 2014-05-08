from datetime import datetime
import sqlite3
import json

start_time = datetime.now()

request_year = start_time.year

target_db = 'DBs/bills_' + str(request_year) + '.sqlite'

conn = sqlite3.connect(target_db)
conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
c = conn.cursor()

# This is our mapping of actions descriptions to legislative stages. May change as we learn more about the legislative process.
c.execute('''UPDATE senate_actions  
	SET stage = CASE
	WHEN Action_Desc LIKE '%Introduced%' THEN 'INTRODUCED SENATE' 
	WHEN Action_Desc LIKE '%Prefiled%' THEN 'INTRODUCED SENATE' 
	WHEN Action_Desc LIKE '%Second Read and Referred S%Committee' THEN 'INTRODUCED SENATE'
	WHEN Action_Desc LIKE 'S First Read%' THEN 'INTRODUCED SENATE'
	WHEN Action_Desc LIKE '%Hearing Cancelled S%' THEN 'INTRODUCED SENATE'
	WHEN Action_Desc LIKE '%Hearing Conducted S%' THEN 'INTRODUCED SENATE'
	WHEN Action_Desc LIKE '%Hearing Scheduled But Not Heard S%' THEN 'INTRODUCED SENATE'
	WHEN Action_Desc LIKE 'Referred S%Committee' THEN 'INTRODUCED SENATE'

	WHEN Action_Desc LIKE 'Voted Do Pass%S%Committee' THEN 'PASS SENATE COMMITTEE'
	WHEN Action_Desc LIKE '%Bill Placed on Informal Calendar%' THEN 'PASS SENATE COMMITTEE'
	WHEN Action_Desc LIKE '%Reported from S%Committee%' THEN 'PASS SENATE COMMITTEE'
	WHEN Action_Desc LIKE '%Perfected%' THEN 'PASS SENATE COMMITTEE'
	WHEN Action_Desc LIKE '%Reported Truly Perfected S%' THEN 'PASS SENATE COMMITTEE'
	WHEN Action_Desc LIKE 'SCS Voted Do Pass S%' THEN 'PASS SENATE COMMITTEE'

	WHEN Action_Desc LIKE 'S Third Read and Passed%' THEN 'PASS SENATE' 
	WHEN Action_Desc LIKE '%S adopted' THEN 'PASS SENATE'

	WHEN Action_Desc LIKE 'H First Read%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'H Second Read%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'Hearing Conducted H%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'Hearing Scheduled but not heard H%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'Referred%H%Committee%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'Reported to the House%' THEN 'INTRODUCED HOUSE'

	WHEN Action_Desc LIKE '%Voted Do Pass%H%Committee' THEN 'PASS HOUSE COMMITTEE'
	WHEN Action_Desc LIKE 'Reported Do Pass%H%Committee%' THEN 'PASS HOUSE COMMITTEE'

	WHEN Action_Desc LIKE 'H Third Read and Passed%' THEN 'PASS HOUSE'
	WHEN Action_Desc LIKE 'HCS Reported Do Pass H%' THEN 'PASS HOUSE'
	WHEN Action_Desc LIKE 'H adopted%' THEN 'PASS HOUSE'


	WHEN Action_Desc LIKE '%DELIVERED TO GOVERNOR%' THEN 'PASS CONFERENCE COMMITTEE' 
	WHEN Action_Desc LIKE '%Truly Agreed To and Finally Passed' THEN 'PASS CONFERENCE COMMITTEE'  

	-- WHEN Action_Desc LIKE '%Bill Withdrawn%' THEN 'WITHDRAWN'  
	-- WHEN Action_Desc LIKE 'Bill Combined%' THEN 'BILL COMBINED'
	ELSE Null
	END;'''
)

stages = ['INTRODUCED SENATE', 'PASS SENATE COMMITTEE', 'PASS SENATE', 'INTRODUCED HOUSE', 'PASS HOUSE COMMITTEE', 'PASS HOUSE', 'PASS CONFERENCE COMMITTEE']
# for row in c.execute('''SELECT DISTINCT stage FROM senate_actions WHERE stage IS NOT NULL;''').fetchall():
# 	stages.append(row[0])

output = []

for stage in stages:

	row_dict = {"stage": stage}

	c.execute('''SELECT count(*) 
					FROM senate_bills 
					WHERE bill_type + bill_number IN (
						select bill_type + bill_number
						from senate_actions 
						where stage = ?
					);''', [stage])

	row_dict["all_bills"] = c.fetchone()[0]

	c.execute('''SELECT count(*) 
					FROM senate_bills
					JOIN senators
					ON senators.last_name = senate_bills.sponsor
					WHERE bill_type + bill_number IN (
						SELECT bill_type + bill_number 
						FROM senate_actions 
						WHERE stage = ?
						)
					AND senators.party = 'D';''', [stage])

	row_dict["dem_bills"] = c.fetchone()[0]

	c.execute('''SELECT count(*) 
					FROM senate_bills
					JOIN senators
					ON senators.last_name = senate_bills.sponsor 
					WHERE bill_type + bill_number in (
						SELECT bill_type + bill_number 
						FROM senate_actions 
						WHERE stage = ?
						)
					AND senators.party = 'R';''', [stage])

	row_dict["rep_bills"] = c.fetchone()[0]

	output.append(row_dict)

conn.close()

jsonFile = open('senate_numbers.json', 'w')
jsonFile.write(json.dumps(output))
jsonFile.close()