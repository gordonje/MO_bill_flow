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

conn.commit()

stages = []
for row in c.execute('''SELECT stage FROM leg_stages WHERE chamber = 'S' ORDER BY sort_order;''').fetchall():
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
	# 				FROM senate_bills 
	# 				WHERE bill_type + bill_number IN (
	# 					select bill_type + bill_number
	# 					from senate_actions 
	# 					where stage = ?
	# 				);''', [stage])

	# row_dict["all_bills"] = c.fetchone()[0]

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

	cells.append({"v": c.fetchone()[0]})

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
								FROM senate_actions
								WHERE stage NOT NULL
								GROUP BY bill_type, bill_number, stage
							) AS bills
							JOIN (
								SELECT bill_type, bill_number, stage, action_date, rowid
								FROM senate_actions
							) AS earliest
							ON bills.first_row = earliest.rowid
							JOIN (
								SELECT bill_type, bill_number, stage, action_date, rowid
								FROM senate_actions
							) AS latest
							ON bills.last_row = latest.rowid
							JOIN leg_stages
							ON bills.stage = leg_stages.stage
							AND leg_stages.chamber = 'S'
						) AS all_bills
						GROUP BY all_bills.stage
						ORDER BY all_bills.sort_order;'''
			).fetchall():

	cells = []
	
	cells.append({"v": i[0]})
	cells.append({"v": i[1]})

	avgs_output["rows"].append({"c": cells})


conn.close()

jsonFile = open('Senate_numbers_gchart.json', 'w')
jsonFile.write(json.dumps(numbers_output))
jsonFile.close()

jsonFile = open('Senate_avgs_gchart.json', 'w')
jsonFile.write(json.dumps(avgs_output))
jsonFile.close()