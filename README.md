MO_bill_flow
=============

Intro
-----

MO_bill_flow is a news app that aggregates data about House and Senate bills in Missouri so that you can visualize their flow through the legislative process. What percentage of bills introduced are voted on by either chamber? How many bills are sitting in committee right now? Where are the bottlenecks in legislative the process? These are the sorts of questions MO_bill_flow aims to answer.

This is a project for my [Advanced Data Journalism](https://github.com/cjdd3b/advanced-data-journalism/ "Advanced Data Journalism") taught by [Chase Davis](http://chasedavis.com/ "Chase Davis") and [Mike Jenner](http://journalism.missouri.edu/staff/michael-m-jenner/ "Mike Jenner") at the University of Missouri School of Journalism.

MO_bill_flow has three high-level components:

1.	*Data Acquisition:* Python scripts that scrape legislation data from [house.mo.gov](http://www.house.mo.gov/ "house.mo.gov") and [senate.mo.gov](http://www.senate.mo.gov/ "senate.mo.gov") and save to a local SQLite database.
2.	*Analysis:* Python scripts that run aggregate queries on the SQLite database and write these aggregates to several JSON files.
3.	*Vizualization:* A Flask app and html/javascript template that presents the aggregates in a series of Google Charts.

Dependencies
------------

Running MO_bill_flow from end-to-end requires the following:

* 	Python 2.7.x
* 	[SQLite3](http://www.sqlite.org "SQLite3")
* 	[Requests](http://docs.python-requests.org/en/latest/ "Requests")
* 	[BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup/ "BeautifulSoup4")
* 	[lxml parser](http://lxml.de/index.html#download "lxml parser")
* 	[Flask](http://flask.pocoo.org/ "Flask")

Data Acquisition
----------------

Scraping Missouri legislative chambers respective websites -- [house.mo.gov](http://www.house.mo.gov/ "house.mo.gov") and [senate.mo.gov](http://www.senate.mo.gov/ "senate.mo.gov") -- is necessary in order to acquire all of the data I believe are potentially useful for this project and to keep the database updated in a timely manner.

[MO_bill_flow/scrapers/](https://github.com/gordonje/MO_bill_flow/tree/master/scrapers "MO_bill_flow/scrapers/") contains [get_house_data.py](https://github.com/gordonje/MO_bill_flow/blob/master/MO_bill_flow/get_house_data.py "get_house_data.py") and [get_senate_data.py](https://github.com/gordonje/MO_bill_flow/blob/master/MO_bill_flow/get_senate_data.py "get_senate_data.py"), each of which you can run to get the current year's data from each chamber. These two scripts are quite similar to each other, each executing the following general steps:

1. 	First, check to see if there's already a version of the given year's database. If so, a copy is saved in the 'DBs/Archive/' directory so that you can easily revert to the previous version.
2. 	Delete all records from tables related to the given chamber.
3. 	Gather a list of all bills introduced in the given chamber for the given year.
4. 	Request, parse and store more detailed info for each bill.
5. 	Request, parse and store each bill's co-sponsors[^1] (and the co-signers for House Bills[^2]).
6. 	Request, parse and store all actions for each bill.
7. 	Request, parse and store all the bill topics index for the given chamber.[^3] 
8. 	Request, parse and store a list of all legislators in the given chamber for the given year.

These scripts share a module of functions -- [scrapers.py](https://github.com/gordonje/MO_bill_flow/blob/master/scrapers/scrapers.py "scrapers.py") -- which gathers records from specific web pages and prepares them to save to the database. You'll note there are over a dozen functions in scrapers.py, half for each chamber. I preferred putting these functions in their own file so that I can run anyone of these steps individually and verify the output without having to save it to the database.

With roughly 1,400 House Bills per regular annual session and accounting for the deliberate throttling of requests sent (as we want to be kind to other people's web servers), get_house_data.py may need to run for _over five hours_ in order to gather all available legislative data. Since there are fewer Senate Bills in a given regular session, get_senate_data.py requires _at least two hours_.

It's worth saying that, initially, I made several attempts to contact the clerks and administrators of each chamber, asking them to provide full copies of their databases, in accordance with [Missouri's Sunshine Laws](http://www.house.mo.gov/ "http://www.moga.mo.gov/STATUTES/C610.HTM"). 

The State Senate administrators were quite helpful and responsive, setting up [this portal](http://www.senate.mo.gov/BTSPortal/ "this portal") for downloading data for the current and previous ten years. However, the data for the current year is only updated weekly. 

The House Clerk eventually responded and stated, rather oddly, that honoring my request could "expos[e] the House infrastructure network to possible security breaches". He did provide a link to an [xml file](http://www.house.mo.gov/export/allbills.xml "xml file"). However, the data here was neither up-to-date nor accurate, and anyway, by the time I got response, I had already written the scraping script.

Databases
---------

The ['MO_bill_flow/DBs/' directory](https://github.com/gordonje/MO_bill_flow/tree/master/MO_bill_flow/DBs ['MO_bill_flow/DBs/' directory]) contains a database for each year for which legislative data has been acquired[^4]. 

The each database has 12 tables:

*	*house_bills* and *senate_bills* each contain distinct records of House Bills and Senate Bills. The primary key for these records is the combination of bill_type and bill_number.
*	*house_actions* and *senate_actions* contain records of each legislative action taken against a House Bill or a Senate Bill, respectively, including each action's date (action_date) and the description (action_desc). In most cases, the same bill will have multiple action records.
*	*house_bills_topics* and *senate_bills_topics* represent the general topics of each bill[^5]. Note that there is a many-to-many relationship between bills and topics.
*	*house_bills_cosponsors*[^6] and *senate_bills_cosponsors* contain records of each bill's cosponsors those who join with the sponsor in introducing the bill. Note that the sponsor of the bill is not included in the list of cosponors. Rather, the sponsor's name and/or district is stored directly on house_bills and senate_bills. There's also *house_bills_cosigners*, and for a given House Bill, the list of cosigners may not include all or any of the legislators who are cosponsors.
*	*representatives* and *senators* contain records of currently elected legislators of each chamber.
*	*leg_stages* contain the distinct list of general legislative stages through which a House Bill or Senate Bill my pass. The sort_order value represents the order of the stage in the legislative process (more on these in the [Analysis} (https://github.com/gordonje/MO_bill_flow#databases "Analysis") section.

If, for whatever reason, you need to create a new empty database, you can do so by running [make_db.py](https://github.com/gordonje/MO_bill_flow/blob/master/MO_bill_flow/make_db.py "make_db.py"), which will also archive your current version of the current year's database.

Analysis
--------

MO_bill_flow curently aims to answer three basic question about Missouri's legislative process:

1. 	How many bills pass each general stage of legislation?
2. 	What proportion of these bills are sponsored by either political party?
3. 	What is the average amount of time that a bill will sit in each legislative stage before moving on to the next one?

Obviously, an important prerequisite is a better understanding of what are the general stages of the legislative process. Based on these helpful explainers (for the [House](http://www.house.mo.gov/content.aspx?info=/info/howbill.htm "House") and [Senate](http://www.house.mo.gov/content.aspx?info=/info/howbill.htm "Senate")), I surmised that the process for each chamber is more or less the same, and summarized the legislative stages thusly:

4. 	*Introduced* in the orginating chamber
5. 	*Passed by committee* relevant in the orginating chamber
6. 	*Passed* by the originating chamber
7. 	*Introduced* in the other chamber
8. 	*Passed by committee* relevant in the other chamber
9. 	*Passed* by the other chamber
10. *Passed by conference committee*, which is actually only relevant for bills that were amended or substituted in both chambers

With that, the next requirement was to map each of the distinct action_desc values (roughly 700 for house_actions and 1,500 for senate_actions) into the appropriate legislative stage. This was done rather manually by sorting the distinct action_desc values and then discerning patterns I then incorporated into a couple of SQL UPDATE statements that set the value of house_actions.stage and senate_actions.stage.

Since you'll want to continually update the database, we'll also need to reapply the stages. So these UPDATE statements were the basis for a couple of other Python scripts: [set_house_stages.py](https://github.com/gordonje/MO_bill_flow/blob/master/MO_bill_flow/set_house_stages.py "set_house_stages.py") and [set_senate_stages.py](https://github.com/gordonje/MO_bill_flow/blob/master/MO_bill_flow/get_senate_data.py "set_senate_stages.py"), both of which are in [MO_bill_flow/scrapers/](https://github.com/gordonje/MO_bill_flow/tree/master/scrapers "MO_bill_flow/scrapers/").

These queries execute the following steps in order:

1. 	Delete the leg_stages records for the given chamber
2. 	Insert the leg_stages records for the given chamber (in case you decided to modify these)
3. 	Update all the records in the chamber's actions table, setting the value of stage according the mapping of action_desc values to general legislative stages. Note that not every action record will have a stage value, as these records represent actions that are merely perfunctory or too discrete to care about.
4. 	Query the database for counts of Democratic-sponsored versus Republican-sponsored bills for each legislative stage
5. 	Query the database for the average amount of time bills will spend in each legislative stage
6. 	Output the results of the above two queries to JSON files in [MO_bill_flow/app/static](https://github.com/gordonje/MO_bill_flow/tree/master/app/static "MO_bill_flow/app/static"). 

In case you wanted to change the mappings of action descriptions to legislative stages (and there are plenty of reasons you might), note that any new distinct stages you create will need to be added to the INSERT statement toward the top of these scripts.

Visualization
-------------



Future Plans
------------

* View current legislative stages
* View discrete legislative stages
* Drill into get bills
* View data for previous legislative sessions
* Prediction model

[^1]: Admittedly, the collection of House Bill co-sponsors is not optimal due to the inconsistency in HTML formatting of the relevant web page. Currently, all co-sponsor names are collected in a single text field on the house_bills table.
[^2]: Not yet sure what the differences are between co-sponsors and co-signers. Though, I do know that not all co-sponsors of a given bill are co-signers and vice-versa.
[^3]: This is also not currently working for the House. Sorry.
[^4]: It may have been preferable to merge these all into a single database, but since we are hosting the SQLite files on GitHub, we figured it best to keep these on the small-ish size.
[^5]: Currently, no records are written to house_bills_topics.
[^6]: Currently, no records are writtent to house_bills_cosponsors. Rather, the a comma-delimited list of co-sponsors is being saved in house_bills.co_sponsor_text. 