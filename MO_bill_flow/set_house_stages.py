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

	WHEN Action_Desc LIKE 'Reported Do Pass%(H)%' THEN 'PASS HOUSE COMMITTEE'
	WHEN Action_Desc LIKE 'Motion to Do Pass Failed%' THEN 'INTRODUCED HOUSE'
	WHEN Action_Desc LIKE 'Perfected%' THEN 'PASS HOUSE COMMITTEE'
	WHEN Action_Desc LIKE 'HCS Adopted (H)%' THEN 'PASS HOUSE COMMITTEE'
	WHEN Action_Desc LIKE 'HCS Voted Do Pass%' THEN 'PASS HOUSE COMMITTEE'
	WHEN Action_Desc LIKE 'HCS Reported Do Pass%' THEN 'PASS HOUSE COMMITTEE' 

	WHEN Action_Desc LIKE 'Adopted (H)%' THEN 'PASS HOUSE'
	WHEN Action_Desc LIKE 'Approved (H)' THEN 'PASS HOUSE'
	WHEN Action_Desc LIKE 'Third Read and Passed (H)%' THEN 'PASS HOUSE'
	WHEN Action_Desc LIKE 'Third Read and Passed%(H)%' THEN 'PASS HOUSE'

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

conn.commit()

stages = []
for row in c.execute('''SELECT stage FROM leg_stages WHERE chamber = 'H' ORDER BY sort_order;''').fetchall():
	stages.append(row[0])

numbers_output = {
  "cols": [{"id": "stage", "label": "Stage", "type": "string"},
         {"id": "d_bills", "label": "Dem Bills", "type": "number"},
         {"id": "r_bills", "label": "Rep Bills", "type": "number"}
        ],
  "rows":[]
  }

for stage in stages:

	cells = []
	
	cells.append({"v": stage})

	# c.execute('''SELECT count(*) 
	# 				FROM house_bills 
	# 				WHERE bill_type + bill_number IN (
	# 					SELECT bill_type + bill_number
	# 					FROM house_actions 
	# 					WHERE stage = ?
	# 				);''', [stage])

	# row_dict["all_bills"] = c.fetchone()[0]

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

	cells.append({"v": c.fetchone()[0]})

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

	cells.append({"v": c.fetchone()[0]})

	numbers_output["rows"].append({"c": cells})


avgs_output = {
  "cols": [{"id": "stage", "label": "Stage", "type": "string"},
         {"id": "avg", "label": "Average Duration", "type": "number"}
        ],
  "rows":[]
  }

for i in c.execute('''SELECT all_bills.stage, avg(all_bills.duration)
						FROM ( 
							SELECT 
								bills.bill_type, 
								bills.bill_number, 
								bills.stage, 
								leg_stages.sort_order,
								earliest.action_date, 
								latest.action_date, 
								julianday(latest.action_date) - julianday(earliest.action_date) AS duration
							FROM (
								SELECT bill_type, bill_number, stage, min(rowid) AS first_row, max(rowid) AS last_row
								FROM house_actions
								WHERE stage NOT NULL
								GROUP BY bill_type, bill_number, stage
							) AS bills
							JOIN (
								SELECT bill_type, bill_number, stage, action_date, rowid
								FROM house_actions
							) AS earliest
							ON bills.first_row = earliest.rowid
							JOIN (
								SELECT bill_type, bill_number, stage, action_date, rowid
								FROM house_actions
							) AS latest
							ON bills.last_row = latest.rowid
							JOIN leg_stages
							ON bills.stage = leg_stages.stage
							AND leg_stages.chamber = 'H'
						) AS all_bills
						GROUP BY all_bills.stage
						ORDER BY all_bills.sort_order;'''
			).fetchall():

	cells = []
	
	cells.append({"v": i[0]})
	cells.append({"v": i[1]})

	avgs_output["rows"].append({"c": cells})

conn.close()

jsonFile = open('House_numbers_gchart.json', 'w')
jsonFile.write(json.dumps(numbers_output))
jsonFile.close()

jsonFile = open('House_avgs_gchart.json', 'w')
jsonFile.write(json.dumps(avgs_output))
jsonFile.close()