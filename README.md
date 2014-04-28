MO_bill_flow
=============

Intro
-----

MO_bill_flow is a news app that aggregates data about House and Senate bills in Missouri so that you can visualize their flow through the legislative process. What percentage of bills introduced voted on by either chamber? How many bills are sitting in committee right now? Where are the bottlenecks in legislative the process? These are the sorts of questions MO_bill_flow aims to answer.

This is a project for our [Advanced Data Journalism](https://github.com/cjdd3b/advanced-data-journalism/ "Advanced Data Journalism") taught by [Chase Davis](http://chasedavis.com/ "Chase Davis") and [Mike Jenner](http://journalism.missouri.edu/staff/michael-m-jenner/ "Mike Jenner") at the University of Missouri School of Journalism.

Dependencies
------------

* Python 2.7.x
* SQLite3
* [BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup/ "BeautifulSoup4")
* [lxml parser](http://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser "lxml parser")
* [Requests](http://docs.python-requests.org/en/latest/ "Requests")
* [Flask](http://flask.pocoo.org/ "Flask")

Scrapers
--------

The first general component of this project is what you might call 'data acquisition', which we're happens via couple of scripts:
* [get_house_data.py](https://github.com/gordonje/MO_bill_flow/blob/master/MO_bill_flow/get_house_data.py "get_house_data.py"), which scrapes data from the [Missouri State House website](http://www.house.mo.gov/ "Missouri State House website")
* [get_senate_data.py](https://github.com/gordonje/MO_bill_flow/blob/master/MO_bill_flow/get_senate_data.py "get_senate_data.py"), which scrapes data from the [Missouri State Senate website](http://www.senate.mo.gov/ "Missouri State Senate website")

These scripts share a module of functions -- scrapers.py -- which gathers records from specific web pages and prepares them to save to the database. You'll note there over a dozen functions in scrapers.py, half for each chamber. Since both the structure of web pages and the records we could extract from [house.mo.gov](http://www.house.mo.gov/ "house.mo.gov") and [senate.mo.gov](http://www.senate.mo.gov/ "senate.mo.gov") were similar but not entirely the same, there seemed no practical way to avoid distinct sets of functions for each chamber.

get_house_data.py and get_senate_data.py are also quite similar to each other. The general steps for each script are as follows:
1. First, check to see if there's already a version of the given year's database. If so, a copy is saved in the 'DBs_Archive/' directory so that you can easily revert to the previous version.
1. Delete all records from tables related to the given chamber.
1. Gathers a list of all bills introduced in the given chamber for the given year.
1. Request and stores info for each of these bills.
1. Request and stores all actions for each bill.
1. Request and stores a list of all legislators in the given chamber for the given year.

With roughly 1,400 House Bills per regular annual session and accounting for the deliberate throttling of requests we're sending (because we want to be kind to other people's web servers), get_house_data.py may need to run for _over six hours_. Since there are fewer Senate Bills in a given regular session, get_senate_data.py requires _at least two and half hours_.

It's worth saying that scraping was a means of last resort in order acquire all the data we wanted and refresh it on a daily basis. We did reach out to administrators for the Missouri State Senate and the State House. The State Senate administrators were quite responsive, setting up [this portal](http://www.senate.mo.gov/BTSPortal/ "this portal") for downloading data for the current and previous ten years. However, the data for the current year is only updated weekly. The State House administrators never returned any of our calls or emails.

Databases
---------

The ['DBs/' directory](https://github.com/gordonje/MO_bill_flow/tree/master/MO_bill_flow/DBs ['DBs/' directory]) contains a database for each year for which legislative data has been required. It may have been preferably to merge these all into a single database, but since we are hosting the SQLite files on GitHub, we figured it best to keep these on the small-ish side.

If for whatever reason you need to create a new empty database, you can do so by running [make_db.py](https://github.com/gordonje/MO_bill_flow/blob/master/MO_bill_flow/make_db.py "make_db.py"), which will also archive your current version of the given year's database.

Web App
-------

We are using Flask to serve up numbers with json. That's about all we know right now.
