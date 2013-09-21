import argparse
import vbts_credit

"""
Basic algorithm: read a credits.log file, update the user_dates and user_credit
map each time we see a newer item for the user.

We do not assume that later log file entries have later dates, hence the date
calculation each time.
"""

"""
This compares a credit log date time. Returns true if first date is newer than
second date, false otherwise. If the dates are equal, should return true.
"""
def date_is_newer(daytime1, daytime2):
    day1, time1 = daytime1.split(None, 1)
    day2, time2 = daytime2.split(None, 1)
    year1, month1, day1 = day1.split("-", 2)
    year2, month2, day2 = day2.split("-", 2)
    year1, month1, day1 = int(year1), int(month1), int(day1)
    year2, month2, day2 = int(year2), int(month2), int(day2)

    if (year1 > year2) or (month1 > month2) or (day1 > day2):
        return True

    hour1, min1, sec1 = time1.split(":", 2)
    hour2, min2, sec2 = time1.split(":", 2)
    hour1, min1, sec1 = int(hour1), int(min1), int(sec1)
    hour2, min2, sec2 = int(hour2), int(min2), int(sec2)

    return (hour1 > hour2) or (min1 > min2) or (sec1 >= sec2) # if equal, return true


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processes a credits.log file to restore all users to last-known credit value.")

    parser.add_argument('logfile', action='store', help="credits.log file to restore from.")
    parser.add_argument('--restore', action='store_true', help="Restore all users to last known credit amount. WARNING: THIS CHANGES VALUES IN THE DB.")
    args = parser.parse_args()

    first_date = None
    last_date = None
    user_credit = {} # IMSI -> last known credit
    user_dates = {} # IMSI -> last known credit update date

    logfile = open(args.logfile, "r")
    for line in logfile:
        fields = line.split()
        date = fields[0] + " " + fields[1]
        credits = fields[7].strip(",")

        if first_date is None:
            first_date = date
        last_date = date

        user = fields[3].strip(",")
        if user in user_dates:
            if date_is_newer(date, user_dates[user]):
                user_dates[user] = date
                user_credit[user] = credits
        else:
            user_dates[user] = date
            user_credit[user] = credits

    for user in user_credit:
        print "%s: %s (%s)" % (user, user_credit[user], user_dates[user])
    print "Last known credit values for period %s through %s" % (first_date, last_date)

    if args.restore:
        print "ABOUT TO UPDATE THE DB. THIS WILL CHANGE PEOPLE'S ACCOUNT BALANCES."
        print "Are you sure you want to continue (yes/no)?",
        response = raw_input()
        if response == "y" or response == "yes":
            for u in user_credit:
                vbts_credit.set_(user_credit[u], u, "credits.log restore")
            print "Credits restored!"
        else:
            print "Did not restore credit values."
