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
c.execute('''DELETE FROM leg_stages WHERE chamber = 'H';''') 
conn.commit()

stages = [
	{"stage": "INTRODUCED HOUSE", "sort_order": 1},
	{"stage": "PASS HOUSE COMMITTEE", "sort_order": 2},
	{"stage": "PASS HOUSE", "sort_order": 3},
	{"stage": "INTRODUCED SENATE", "sort_order": 4},
	{"stage": "PASS SENATE COMMITTEE", "sort_order": 5},
	{"stage": "PASS SENATE", "sort_order": 6},
	{"stage": "PASS CONFERENCE COMMITTEE", "sort_order": 7}
]

for i in stages:
	c.execute('''INSERT INTO leg_stages (chamber, stage, sort_order) VALUES (?,?,?);''', ['H', i["stage"], i["sort_order"]])

conn.commit()

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
					FROM house_bills
					JOIN representatives
					ON representatives.district = house_bills.sponsor_district 
					WHERE bill_type + bill_number IN (
						SELECT bill_type + bill_number 
						FROM house_actions 
						WHERE stage = ?
					)
					AND representatives.party = 'Democrat';''', [i["stage"]])

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
					AND representatives.party = 'Republican';''', [i["stage"]])

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

# Finally, write to those JSON files.
jsonFile = open('../app/static/House_numbers_gchart.json', 'w')
jsonFile.write(json.dumps(counts_output))
jsonFile.close()

jsonFile = open('../app/static/House_avgs_gchart.json', 'w')
jsonFile.write(json.dumps(avgs_output))
jsonFile.close()