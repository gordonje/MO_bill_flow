from datetime import datetime
import sqlite3
import json

start_time = datetime.now()

request_year = start_time.year

target_db = '../DBs/bills_' + str(request_year) + '.sqlite'

conn = sqlite3.connect(target_db)
conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
c = conn.cursor()

# Delete the current stages for the the given chamber, then re-insert them, in case they are changed.
c.execute('''DELETE FROM leg_stages WHERE chamber = 'S';''') 
conn.commit()

stages = [
	{"stage": "INTRODUCED SENATE", "sort_order": 1},
	{"stage": "PASS SENATE COMMITTEE", "sort_order": 2},
	{"stage": "PASS SENATE", "sort_order": 3},
	{"stage": "INTRODUCED HOUSE", "sort_order": 4},
	{"stage": "PASS HOUSE COMMITTEE", "sort_order": 5},
	{"stage": "PASS HOUSE", "sort_order": 6},
	{"stage": "PASS CONFERENCE COMMITTEE", "sort_order": 7}
]

for i in stages:
	c.execute('''INSERT INTO leg_stages (chamber, stage, sort_order) VALUES (?,?,?);''', ['S', i["stage"], i["sort_order"]])
conn.commit()

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

# Building the JSON for the counts of Democrat versus Republican sponsored bills that passed each legislative stage.
# This is the format that Google Charts expects
counts_output = {
  "cols": [{"id": "stage", "label": "Stage", "type": "string"},
         {"id": "d_bills", "label": "Dem Bills", "type": "number"},
         {"id": "r_bills", "label": "Rep Bills", "type": "number"}
        ],
  "rows":[]
  }

for i in stages:

	cells = []
	
	cells.append({"v": i["stage"]})

	c.execute('''SELECT count(*) 
					FROM senate_bills
					JOIN senators
					ON senators.last_name = senate_bills.sponsor
					WHERE bill_type + bill_number IN (
						SELECT bill_type + bill_number 
						FROM senate_actions 
						WHERE stage = ?
						)
					AND senators.party = 'D';''', [i["stage"]])

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
					AND senators.party = 'R';''', [i["stage"]])

	cells.append({"v": c.fetchone()[0]})

	counts_output["rows"].append({"c": cells})

# Building the JSON for the average amount of time bills spend in each legislative stage.
# This is the format that Google Charts expects
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

# Finally, write to those JSON files.
jsonFile = open('../app/static/Senate_numbers_gchart.json', 'w')
jsonFile.write(json.dumps(counts_output))
jsonFile.close()

jsonFile = open('../app/static/Senate_avgs_gchart.json', 'w')
jsonFile.write(json.dumps(avgs_output))
jsonFile.close()