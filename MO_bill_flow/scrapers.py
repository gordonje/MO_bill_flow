import re
from datetime import date, timedelta
from bs4 import BeautifulSoup


def get_house_bills (year, requests_session):

####### Returns a list of bills introduced in the House of Representatives, each of which is a dict with a bill_number, href and year #######

	bills = []

	bill_list_url = 'http://www.house.mo.gov/billlist.aspx'

	response = requests_session.get(bill_list_url)
	soup = BeautifulSoup(response.content)

	table = soup.find('table', id = "billAssignGroup")

	for a in table.findAll('a', attrs = {'href': re.compile("billsummary.aspx?.+")}):

		bill = {}

		# going to collect the bill string from the list and details page for now, will compare later. probably drop one or the other
		bill['url_id'] = re.search('=.+&y', a['href']).group().lstrip('=').rstrip('&y')
		bill['bill_year'] = year
		
		bills.append(bill)

	return bills


def get_house_bill_info (bill, requests_session):

####### Returns a bill, represented as a dict, with all info, ready to save to the database #######

	payload = {'year': bill['bill_year'], 'code': 'R', 'bill': bill['url_id']}
	response = requests_session.get('http://www.house.mo.gov/billsummary.aspx', params = payload)

	soup = BeautifulSoup(response.content)

	bill_details = soup.find('div', id = 'BillDetails')

	bill['bill_type'] = bill_details.find('span', attrs = {'class':'entry-title'}).text.split(' ')[0]
	bill['bill_number'] = int(bill_details.find('span', attrs = {'class':'entry-title'}).text.split(' ')[1])
	bill['brief_desc'] = bill_details.find('div', attrs = {'class':'BillDescription'}).text.strip('"').strip()
	bill['has_cosponsors'] = False
	
	details_table = bill_details.find('table')

	for tr in details_table.findAll('tr'):
		if tr.find('td') != None:

			th = tr.findChild('th')

			if tr.find('th').text == 'Sponsor:':
				bill['sponsor_last_name'] = re.search('\w+,', th.findNextSibling('td').text).group().rstrip(',')
				bill['sponsor_first_name'] = re.search(',\s\w+', th.findNextSibling('td').text).group().lstrip(', ')
				bill['sponsor_district'] = re.search('(\d+)', th.findNextSibling('td').text).group().lstrip('(').rstrip(')')
			if tr.find('th').text == 'Co-Sponsor:':
				bill['has_cosponsors'] = True
			if tr.find('th').text == 'LR Number:':
				bill['lr_number'] = th.findNextSibling('td').text
			if tr.find('th').text == 'Proposed Effective Date:':
				bill['effective_date'] = th.findNextSibling('td').text
			else:
				bill['effective_date'] = ''
			if tr.find('th').text == 'Last Action:':
				bill['last_action_desc'] = th.findNextSibling('td').text.split(' - ', 1)[0]
				if bill['last_action_desc'] != 'This Bill Replaced with a Substitute Bill':
					bill['last_action_date'] = date(int(bill['last_action_desc'].split('/')[2]), int(bill['last_action_desc'].split('/')[0]), int(bill['last_action_desc'].split('/')[1]))
					bill['last_action_desc'] = th.findNextSibling('td').text.split(' - ', 1)[1]
				else:
					bill['last_action_date'] = ''
			if tr.find('th').text == 'Bill String:':
				bill['bill_string'] = th.findNextSibling('td').text
			if tr.find('th').text == 'Next Hearing':
				bill['next_hearing'] = th.findNextSibling('td').text
			else:
				bill['next_hearing'] = ''
			if tr.find('th').text == 'Calendar':
				bill['calendar'] = th.findNextSibling('td').text
			else:
				bill['calendar'] = ''
	
	sections = soup.find('div', attrs = {'class': 'Sections'})
	cosigners_link = sections.find("a", attrs = {'href': re.compile('CoSigners.aspx.+')})
	if cosigners_link != None:
		bill['has_cosigners'] = True
	else:
		bill['has_cosigners'] = False

	return bill


def get_house_actions (bill, requests_session):

####### Returns a list of the bill's actions, each of which is represented as a list, ready to save to the database #######

	payload = {'bill': bill['url_id'], 'year': bill['bill_year'], 'code': 'R'}
	response = requests_session.get('http://www.house.mo.gov/BillActions.aspx', params = payload)

	soup = BeautifulSoup(response.content)

	div = soup.find('div', id = 'activitytable')
	table = div.find('table')

	actions = []

	for tr in table.findAll('tr')[1:]:

		action = [ 
			bill['bill_type'], 
			bill['bill_number']
		]

		for td in tr.findAll('td'):

			action.append(td.text.strip())

		action[2] = date(int(action[2].split('/')[2]), int(action[2].split('/')[0]), int(action[2].split('/')[1]))

		actions.append(action)

	return actions


def get_house_bill_cosigners (bill, requests_session):

####### Returns a list of the house bill's co-signers, each of which is represented as a list, ready to save to the database #######

	payload = {'bill': bill['url_id'], 'year': bill['bill_year'], 'code': 'R'}
	response = requests_session.get('http://www.house.mo.gov/CoSigners.aspx', params = payload)

	soup = BeautifulSoup(response.content)
	
	cosigners = []

	table = soup.find("table", id = "CoSigners")

	for tr in table.findAll('tr')[1:]:
		cosigner = [bill['bill_type'], bill['bill_number']]
		for td in tr.findAll('td'):
			cosigner.append(td.text)

		cosigners.append(cosigner)

	return cosigners


def get_house_bill_cosponsors (bill, requests_session):

####### Returns a list of the bill's cosponsors, each of which is represented as a list, ready to save to the database #######

	response = requests_session.get('http://www.house.mo.gov/billtracking/bills141/biltxt/intro/' + bill['url_id'] + 'I.HTM')

	soup = BeautifulSoup(response.content)
	
	cosponsors = []

	p1 = soup.find('p', attrs = {'style':'margin-bottom: 0.104167in; margin-bottom: 0.104167in'})
	if p1 != None:
		p2 = p1.findNextSibling('p', attrs = {'style':'margin-bottom: 0.104167in; margin-bottom: 0.104167in'})
		p3 = p2.findNextSibling('p', attrs = {'style':'text-align: center; margin-bottom: 0.104167in'})

		span_text = p3.findChild('span').text.encode('utf-8', 'ignore').replace('\n', ' ').replace('\r', '')

		return span_text
	else:
		return ''

	# for i in span_text.split(', ')[1:]:

	# 	if re.search('\(Co-sponsors\)', i):
	# 		return i.decode('utf-8', 'ignore')

	# 		cosponsors.append([bill['bill_type'], bill['bill_number'], i.split(' AND ')[0]])
	# 		cosponsors.append([bill['bill_type'], bill['bill_number'], i.split(' AND ')[1].rstrip( ' (Co-sponsors).')])
	# 	else:
	# 		cosponsors.append([bill['bill_type'], bill['bill_number'], i])

	# return cosponsors


def get_house_bill_topics (requests_session):

####### Gets the topics applied to each bill for the given year, ready to save to the database #######

	response = requests_session.get('http://house.mo.gov/subjectindexlist.aspx')

	soup = BeautifulSoup(response.content)

	return bills_topics


def get_representatives (requests_session):

####### Gets info about the given years representatives, including the name, party and district #######

	response = requests_session.get('http://www.house.mo.gov/member.aspx')

	soup = BeautifulSoup(response.content)

	reps = []

	table = soup.find('table', id = 'ContentPlaceHolder1_gridMembers_DXMainTable')

	for tr in table.findAll('tr')[1:]:

		rep = []

		for td in tr.findAll('td'):

			rep.append(td.text.strip())

		if rep[0] != 'Vacant':
			reps.append(rep)

	return reps




def get_senate_bills (year, requests_session):

####### Returns a list of bills introduced in the Senate, each of which is a dict with a bill_type, bill_number and url_id #######

	bills = []

	bill_list_url = 'http://www.senate.mo.gov/' + str(year).lstrip("20") + 'info/BTS_Web/BillList.aspx?SessionType=R'

	response = requests_session.get(bill_list_url)
	soup = BeautifulSoup(response.content)

	bill_list = soup.findAll('table', id='Table2')

	for i in bill_list:

		bill = {}

		bill_link = i.find("a", id = re.compile("dgBillList__ctl\d+_hlBillNum"))

		bill['bill_type'] = bill_link.text.split(" ")[0]
		bill['bill_number'] = bill_link.text.split(" ")[1]
		bill['url_id'] = re.search('\d+', bill_link["href"]).group()
		bill['bill_year'] = year
		
		bills.append(bill)

	return bills


def get_senate_bill_info (bill, requests_session):

####### Returns a bill, represented as a dict, with all info, ready to save to the database #######

	payload = {'SessionType': 'R', 'BillID': str(bill['url_id'])}
	response = requests_session.get('http://www.senate.mo.gov/' + str(bill['bill_year']).lstrip("20") + 'info/BTS_Web/Bill.aspx', params = payload)

	soup = BeautifulSoup(response.content)

	bill['brief_desc'] = soup.find("span", id = "lblBriefDesc").text.encode('utf-8')
	bill['sponsor'] = soup.find("a", id = "hlSponsor").text.encode('utf-8')
	bill['lr_number'] = soup.find("span", id = "lblLRNum").text.encode('utf-8')
	bill['committee'] = soup.find("a", id = "hlCommittee").text.encode('utf-8')
	bill['effective_date'] = soup.find("span", id = "lblEffDate").text.encode('utf-8')
	bill['summary'] = soup.find("span", id = "lblSummary").text.encode('utf-8')
	bill['last_action_desc'] = soup.find("span", id = "lblLastAction").text.split(" - ", 1)[1]
	last_action_date = soup.find("span", id = "lblLastAction").text.split(" - ", 1)[0]
	bill['last_action_date'] = last_action_date.split("/")[2] + '-' + last_action_date.split("/")[0] + '-' + last_action_date.split("/")[1]

	bill['has_cosponsors'] = False
	cosponsors_link = soup.find("a", id = "hlCoSponsors")
	if cosponsors_link.text == "Co-Sponsor(s)":
		bill['has_cosponsors'] = True

	return bill


def get_senate_actions (bill, requests_session):

####### Returns a list of the bill's actions, each of which is represented as a list, ready to save to the database #######

	payload = {'SessionType': 'R', 'BillID': str(bill['url_id'])}
	response = requests_session.get('http://www.senate.mo.gov/' + str(bill['bill_year']).lstrip("20") + 'info/BTS_Web/Actions.aspx', params = payload)

	soup = BeautifulSoup(response.content)

	div = soup.find("div")

	actions = []

	for tr in div.findAll("tr"):

		date_td = tr.findChild('td')
		action_date = date(int(date_td.text.split('/')[2]), int(date_td.text.split('/')[0]), int(date_td.text.split('/')[1]))

		# excluding actions that haven't yet to occur

		tomorrow = date.today() + timedelta(days=1)

		if action_date < tomorrow:

			description = date_td.findNextSibling('td')

			action = [ 
				bill['bill_type'], 
				bill['bill_number'],
				str(action_date),
				description.text.encode('utf-8')
				]

			actions.append(action)

	return actions


def get_senate_bill_cosponsors (bill, requests_session):

####### Returns a list of the bill's cosponsors, each of which is represented as a list, ready to save to the database #######

	payload = {'SessionType': 'R', 'BillID': str(bill['url_id'])}
	response = requests_session.get('http://www.senate.mo.gov/' + str(bill['bill_year']).lstrip("20") + 'info/BTS_Web/CoSponsors.aspx', params = payload)

	cosponsors = []

	soup = BeautifulSoup(response.content)

	cosponsors_table = soup.find("table", id = "dgCoSponsors")

	for a in cosponsors_table.findAll('a'):
		name = a.text.split(", ")[0]
		district = a.text.split(", ")[1].lstrip("District ")

		cosponsor = [bill['bill_type'], bill['bill_number'], name, district]

		cosponsors.append(cosponsor)

	return cosponsors


def get_senate_bill_topics (year, requests_session):

####### Gets the topics applied to each bill for the given year, ready to save to the database #######

	response = requests_session.get('http://www.senate.mo.gov/' + str(year).lstrip("20") + 'info/BTS_Web/Keywords.aspx?SessionType=R')

	soup = BeautifulSoup(response.content)

	bills_topics = []
	
	for h3 in soup.findAll('h3'):

		bill_count = re.search(' \(.+', h3.text).group()
		topic  = h3.text.rstrip(bill_count)

		bills_on_topic = h3.findNextSibling('span')


		for b in bills_on_topic.findAll('b'):
			bill_topic = [
				b.text.split(" ")[0],
				b.text.split(" ")[1],
				topic
				]
			bills_topics.append(bill_topic)

	return bills_topics

def get_senators (year, requests_session):

####### Gets info about the given years senators, including the name, party and district #######

	response = requests_session.get('http://www.senate.mo.gov/' + str(year).lstrip("20") + 'info/senateroster.htm')

	soup = BeautifulSoup(response.content)

	outer = soup.find('td', attrs = {'valign':"top", 'width': "49%"})
	
	inner = outer.find('table', attrs = {'border':"0", 'width':"90%"})

	senators = []

	for tr in inner.findAll('tr')[1:]:

		raw_senator = []

		for td in tr.findAll('td')[:2]:

			raw_senator.append(td.text.strip())

		name = raw_senator.pop(0)

		if name == 'Vacant':
			pass
		else:
			senator = []

			senator.append(re.search('^\w+', name).group())
			senator.append(re.search('\w+$', name).group())

			party_district = raw_senator.pop(-1).split('-')

			senator.append(party_district[0])
			senator.append(int(party_district[1]))

			senators.append(senator)

	return senators