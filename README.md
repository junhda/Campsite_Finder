# Campsite Reservation Checker

This program will scrape Recreation.gov for available campsites at defined parks over defined stay periods. Discovered availability information will be emailed to some defined set of recipients.

## Author
Daniel Jun
Credit to https://github.com/banool/recreation-gov-campsite-checker and https://realpython.com/python-send-email/ for code and ideas on how to make this program work.

## Development Version
Python 3.8.5

## Required Modules
fake_useragent
requests
smtplib

## Deployment
The following parameters should be set up in the params.json file associated with this package.

| Parameter          | Example Value                                                         | Mandatory | Notes                                  |
|--------------------|-----------------------------------------------------------------------|-----------|----------------------------------------|
| holidays          | [["2021-12-24","2021-12-26"]]               |   yes     | List of date ranges to check reservations for  |
| recipients        | ["danjun95@gmail.com"]                      |   yes     | List of email addresses to send reservation availability result to |
| parks             | [232447,232449,232450,232448]               |   yes     | List of park ids to find availability data for. Park IDs can be found from recreation.gov campsite URLs. The urls are in form https://www.recreation.gov/camping/campgrounds/<number>. Pull out the <number> value as the park_id                |
| campsite_type     | "STANDARD NONELECTRIC"                      |   no     | Optional parameter to define a specific campsite type (types found on Recreation.gov) |

Once you've populated params.json to your liking, you are ready to run the terminal program. In terminal, navigate the the project directory and run 'python3 main.py' to execute. 

## Expected Outcome
An email is sent to all recipients listed to provide infomation on what camp sites are available over each date range and park provided in the params.json. The information will be sent as a JSON file attachment, which will also include a link to the park's reservations page, a list of which campsites are available for which date ranges, and the park name. There is some small email messaging changes if no reservations are available.