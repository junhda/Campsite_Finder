import json
from datetime import datetime, timedelta
import calendar
import requests
from os.path import exists
from fake_useragent import UserAgent

from emailer import send_mail


INPUT_DATE_FORMAT = "%Y-%m-%d"
ISO_DATE_FORMAT_REQUEST = "%Y-%m-%dT00:00:00.000Z"
ISO_DATE_FORMAT_RESPONSE = "%Y-%m-%dT00:00:00Z"
BASE_URL = "https://www.recreation.gov"
AVAILABILITY_ENDPOINT = "/api/camps/availability/campground/"
MAIN_PAGE_ENDPOINT = "/api/camps/campgrounds/"

# functions send_request, format_date, and valid_date are adapted from
# https://github.com/banool/recreation-gov-campsite-checker


def send_request(url):
    '''
    Send out an HTTP Get request to an input URL.
    Includes a "random user agent" header to emulate a new user accessing
    the data with each call. Returns the HTTP Get response.
    '''
    resp = requests.get(url, headers={"User-Agent": UserAgent().random})
    if resp.status_code != 200:
        raise RuntimeError(
            "failedRequest",
            "ERROR, {} code received from {}: {}".format(
                resp.status_code, url, resp.text
            ),
        )
    # with open('response_dump.json', 'w') as f:
    #     json.dump(resp.json(), f, indent=1)
    return resp.json()


def format_date(date_object, format_string=ISO_DATE_FORMAT_REQUEST):
    """
    Format date for Recreation.gov API call (request and response)
    """
    if not isinstance(date_object, datetime):
        raise TypeError(
            "date_object parameter entries expect input of type datetime")
    if not isinstance(format_string, str):
        raise TypeError(
            "format_string parameter entries expect input of type string")

    date_formatted = datetime.strftime(date_object, format_string)
    return date_formatted


def valid_date(s):
    '''
    converts string date into a datetime to return. Throws an error if conversion doesn't work.
    '''
    try:
        return datetime.strptime(s, INPUT_DATE_FORMAT)
    except TypeError:
        msg = 'Expecting input of type string'
        raise TypeError(msg)
    except ValueError:
        msg = "Not a valid date: " + s
        raise ValueError(msg)

# end of code adapted from
# https://github.com/banool/recreation-gov-campsite-checker


def last_date_month(d):
    '''
    takes in a datetime parameter and returns the last day of the same month
    '''
    year = d.year
    month = d.month
    month_range = calendar.monthrange(year, month)
    return d.replace(day=month_range[1])


def date_range(start_date, end_date):
    '''
    returns a list of dates (type string) in Recreation.gov response format. Will include
    all dates between start_date and end_date provided, inclusive.
    Entry types are validated earlier in program
    '''
    if end_date < start_date:
        raise ValueError(
            "Expecting an end date that is greater than or equal to start date.")
    date_delta = end_date - start_date
    date_range = []
    for i in range(date_delta.days + 1):
        date_range.append(
            format_date(
                start_date +
                timedelta(
                    days=i),
                ISO_DATE_FORMAT_RESPONSE))
    return date_range


def availability_check(stay_range, json, campsite_type=None):
    '''
    Given the response HTTP get response from recreation.gov about a specific campsite,
    a date range filter, and a campsite type filter, this function checks if all dates
    and filtering criteria are satisfied for the given park. Returns a list of available
    campsites. (Empty list means that no availabilities exist for the given filters).
    entries are validated earlier in program.
    '''
    # stay_range = date_range(start_date, end_date)
    campsites = json["campsites"]
    available_camps = []
    for camp_id in campsites:
        if campsite_type is not None:
            if campsites[camp_id]["campsite_type"] != campsite_type:
                continue

        availability_check = True
        for date in stay_range:
            keys = campsites[camp_id]["availabilities"].keys()
            if date not in keys:
                availability_check = False
                continue
            if date in keys and campsites[camp_id]["availabilities"][date] != 'Available':
                availability_check = False
        if availability_check:
            available_camps.append(camp_id)
    return available_camps


def campsite_checker(parks, stays, campsite_type=None):
    '''
    runs through all parks and all date ranges provided and finds if a desired availability
    exists. Compiles all of the checks into a single dictionary to return
    '''
    availability = {}

    for park in parks:
        availability[park] = {}

        # get park name
        url = BASE_URL + MAIN_PAGE_ENDPOINT + str(park)
        resp = send_request(url)
        park_name = resp["campground"]["facility_name"]
        availability[park]["park_name"] = park_name

        # get park availability data
        availability[park]["park_url"] = BASE_URL + \
            '/camping/campgrounds/' + str(park)
        availability[park]["stays"] = {}

        # find camp sites available for list of date ranges
        for stay_range in stays:
            dates = stay_range[0] + ' - ' + stay_range[1]
            print(
                "Checking for reservation availability in park",
                str(park),
                "over",
                dates)
            # print(dates)
            start_date = valid_date(stay_range[0])
            end_date = valid_date(stay_range[1])

            # split if dates span multi-month
            if end_date.month - start_date.month > 0:
                available_camps = []
                for i in range(end_date.month - start_date.month + 1):
                    start_date_eff = start_date.replace(
                        month=start_date.month + i)
                    if start_date_eff.month > start_date.month:
                        start_date_eff = start_date_eff.replace(day=1)

                    if end_date.month > start_date_eff.month:
                        last_day_month = last_date_month(start_date_eff).day
                        end_date_eff = start_date_eff.replace(
                            day=last_day_month)
                    else:
                        end_date_eff = end_date

                    first_day_month = format_date(
                        start_date_eff.replace(
                            day=1)).replace(
                        ':', '%3A')
                    request_url = BASE_URL + AVAILABILITY_ENDPOINT + \
                        str(park) + '/month?start_date=' + first_day_month
                    # print(request_url)
                    data = send_request(request_url)
                    sub_available_camps = availability_check(date_range(
                        start_date_eff, end_date_eff), data, campsite_type)
                    available_camps.extend(sub_available_camps)
            else:
                first_day_month = format_date(
                    start_date.replace(
                        day=1)).replace(
                    ':', '%3A')
                request_url = BASE_URL + AVAILABILITY_ENDPOINT + \
                    str(park) + '/month?start_date=' + first_day_month
                # print(request_url)
                data = send_request(request_url)
                available_camps = availability_check(
                    date_range(start_date, end_date), data, campsite_type)

            availability[park]["stays"][dates] = available_camps

    print("Reservation checking complete")
    # check if an available reservation exists within the given search
    # parameters
    reservation_exists = False
    for park in availability:
        for stay in availability[park]["stays"]:
            if len(availability[park]["stays"][stay]) > 0:
                reservation_exists = True

    if reservation_exists:
        print("There are available reservations!")
    else:
        print("Bummer! There are no available reservations.")

    availability["campsite_type"] = campsite_type
    return availability, reservation_exists


def main(params_path):
    if exists(params_path) == False:
        raise FileNotFoundError(
            "The provided file path is invalid",
            params_path)
    try:
        # parse params from json file
        with open(params_path, 'r') as f:
            params = json.load(f)
        if not isinstance(params["parks"], list):
            raise TypeError("parks param is expecting a list type entry")
        if not isinstance(params["holidays"], list):
            raise TypeError("holidays param is expecting a list type entry")
        if not isinstance(params["campsite_type"], str):
            raise TypeError(
                "campsite_type param is expecting a string type entry")

        parks = params["parks"]
        holidays = params["holidays"]
        if params["campsite_type"] == '':
            campsite_type = None
        else:
            campsite_type = params["campsite_type"]

        # get data for reservation availability
        availability_json, reservation_exists = campsite_checker(
            parks, holidays, campsite_type)
        with open('camp_sites.json', 'w') as f:
            json.dump(availability_json, f, indent=1)

        # send email with availability data
        if reservation_exists:
            body = "You've got some camping to do!"
        else:
            body = "Bummer! We see no availabilities for the search criteria that you've included. Try updating your search filters."

        for recipient in params["recipients"]:
            send_mail(recipient, body, ["camp_sites.json"])
    except TypeError as ex:
        print(ex)
        raise TypeError(ex)
    except KeyError as ex:
        print(ex)
        raise KeyError(ex)
    except Exception as ex:
        print(ex)
        raise Exception(ex)


if __name__ == "__main__":
    main('params.json')
