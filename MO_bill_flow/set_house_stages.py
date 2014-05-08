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
	WHEN Action_Desc LIKE '%Do Pass (H)%' THEN 'PASS HOUSE COMMITTEE'
	WHEN Action_Desc LIKE 'Perfected%' THEN 'PASS HOUSE COMMITTEE'
	WHEN Action_Desc LIKE 'HCS Adopted(H)%' THEN 'PASS HOUSE COMMITTEE'

	WHEN Action_Desc LIKE 'Adopted (H)%' THEN 'PASS HOUSE'
	WHEN Action_Desc LIKE 'Approved (H)' THEN 'PASS HOUSE'

	WHEN Action_Desc LIKE 'Reported to The Senate (S)' THEN 'INTRODUCED SENATE'
	WHEN Action_Desc LIKE 'Public Hearing%(S)%' THEN 'INTRODUCED SENATE'
	WHEN Action_Desc LIKE 'Hearing Cancelled%(S)%' THEN 'INTRODUCED SENATE'
	WHEN Action_Desc LIKE 'Referred%(S)%' THEN 'INTRODUCED SENATE'
	WHEN Action_Desc LIKE 'Removed form Consent Calendar(S)%' THEN 'INTRODUCED SENATE'

	WHEN Action_Desc LIKE '%Do Pass%(S)' THEN 'PASS SENATE COMMITTEE'
	WHEN Action_Desc LIKE '%(S)%Do Pass%' THEN 'PASS SENATE COMMITTEE'
	
	WHEN Action_Desc LIKE 'Adopted (S)%' THEN 'PASS SENATE'
	WHEN Action_Desc LIKE 'Reported to The House with%(H)%' THEN 'PASS SENATE'
	WHEN Action_Desc LIKE 'Approved (S)%' THEN 'PASS SENATE'

	WHEN Action_Desc LIKE 'Delivered to Secretary of State (G)%' THEN 'PASS CONFERENCE COMMITTEE'
	WHEN Action_Desc LIKE 'Delivered to Governor (G)%' THEN 'PASS CONFERENCE COMMITTEE'

	-- WHEN Action_Desc LIKE '%WITHDRAWN (H)%' THEN 'WITHDRAWN'
	ELSE NULL END;'''
)

stages = ['INTRODUCED HOUSE', 'PASS HOUSE COMMITTEE', 'PASS HOUSE', 'INTRODUCED SENATE', 'PASS SENATE COMMITTEE', 'PASS SENATE', 'PASS CONFERENCE COMMITTEE']
# for row in c.execute('''SELECT DISTINCT stage FROM house_actions WHERE stage IS NOT NULL;''').fetchall():
# 	stages.append(row[0])

output = []

for stage in stages:

	row_dict = {"stage": stage}

	c.execute('''SELECT count(*) 
					FROM house_bills 
					WHERE bill_type + bill_number IN (
						SELECT bill_type + bill_number
						FROM house_actions 
						WHERE stage = ?
					);''', [stage])

	row_dict["all_bills"] = c.fetchone()[0]

	c.execute('''SELECT count(*) 
					FROM house_bills
					JOIN representatives
					ON representatives.district = house_bills.sponsor_district 
					WHERE bill_type + bill_number IN (
						SELECT bill_type + bill_number 
						FROM house_actions 
						WHERE stage = ?
					)
					AND representatives.party = 'Democrat';''', [stage])

	row_dict["dem_bills"] = c.fetchone()[0]

	c.execute('''SELECT count(*) 
					FROM house_bills
					JOIN representatives
					ON representatives.district = house_bills.sponsor_district 
					WHERE bill_type + bill_number IN (
						SELECT bill_type + bill_number 
						FROM house_actions 
						WHERE stage = ?
					)
					AND representatives.party = 'Republican';''', [stage])

	row_dict["rep_bills"] = c.fetchone()[0]

	output.append(row_dict)

conn.close()

jsonFile = open('house_numbers.json', 'w')
jsonFile.write(json.dumps(output))
jsonFile.close()