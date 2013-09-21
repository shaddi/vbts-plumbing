#!/usr/bin/python
import argparse
import datetime
import re

import vbts_credit

"""
Generate reports for the last N days containing the following:
    - Credit transferred
    - Calls made
    - SMS sent/received
    - Revenue
    - Lifetime calls/SMS/revenue
"""
MONEY_LENGTH = 8

def days_ago(date):
    return (datetime.date.today() - date).days

# given a transfer line item, return a tuple containing (to, from, amount)
def process_transfer(line):
    regexp = re.compile(r".*change: (\d+), reason: SMS transfer from (\d+) to (\d+)")
    m = regexp.match(line)
    if m:
        return (m.group(3), m.group(2), m.group(1))
    else:
        return None

def process_web_update(line):
    regexp = re.compile(r".* user: (IMSI\d+), old_credit: (\d+), new_credit: (\d+), change: (\d+), reason: Update( to (\d+))? from web UI \(add_money\)")
    m = regexp.match(line)
    if m:
        if (m.group(6)):
            return (m.group(6), m.group(4))
        else:
            return (m.group(1), m.group(4))
    else:
        return None

def process_provision_event(line):
    regexp = re.compile(r".* user: (IMSI\d+), old_credit: (\d+), new_credit: (\d+), change: (\d+), reason: Provisioned user (IMSI\d+) number (\d+)")
    m = regexp.match(line)
    if m:
        return (m.group(1), m.group(6))
    else:
        return None

def format_report(lifetime_counts, report_counts, report_days, transfers, updates, lifetime_imsis, report_imsis):
    start_date = str(datetime.date.today() - datetime.timedelta(report_days))
    end_date = str(datetime.date.today())

    res = ""

    res += "Lifetime statistics:\n"
    for category in lifetime_counts:
        res += "\t%s %s\n" % (lifetime_counts[category], category)
    res += "\tNumber of IMSIs: %s\n" % (len(lifetime_imsis))
    res += "\n"
    res += "Statistics for dates %s through %s:\n" % (start_date, end_date)
    for category in report_counts:
        res += "\t%s %s\n" % (report_counts[category], category)
    res += "\tNumber of IMSIs: %s\n" % (len(report_imsis))
    res += "\n"
    res += "Transfer log for dates %s through %s:\n" % (start_date, end_date)
    for r in transfers:
        to, fromm, amount = r
        if (len(amount) < MONEY_LENGTH):
            for i in range(MONEY_LENGTH-len(amount)):
                amount += " "
        res += "\t%s sent %s to %s\n" % (fromm, amount, to)

    res += "\n"
    res += "Updates log for dates %s through %s:\n" % (start_date, end_date)
    for u in updates:
        to, amount = u
        if (len(amount) < MONEY_LENGTH):
            for i in range(MONEY_LENGTH-len(amount)):
                amount+= " "
        res += "\t%s sold to %s via web UI\n" % (amount, to)

    res += "\n"
    res += "Provisions for dates %s through %s:\n" % (start_date, end_date)
    for p in provisions:
        res += "\t%s provisioned with number %s\n" % p

    return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a report from the credit log.")

    parser.add_argument('logfile', action='store', help="credits.log file to use.")
    parser.add_argument('-d', "--days", action='store', default=1, help="Number of days prior to today to generate a report for.")
    args = parser.parse_args()

    report_days = int(args.days)

    lifetime_imsis = set() # unique imsis
    report_imsis = set() # unique imsis
    lifetime = {} # lifetime counts
    report = {} # report range counts
    transfers = [] # list of tuples containing "from A to B" strings and the transfer amount
    updates = []
    provisions = []

    credit_types = ["local_call", "local_sms", "outside_call", "outside_sms", "free_call", "free_sms", "incoming_sms", "error_sms", "transfer"]
    for c in credit_types:
        lifetime[c] = 0
        report[c] = 0


    logfile = open(args.logfile, "r")
    for line in logfile:
        fields = line.split()
        lifetime_imsis.add(fields[3].strip(","))
        date = datetime.datetime.strptime(fields[0], "%Y-%m-%d").date()
        for c in credit_types:
            if c in line:
                lifetime[c] += 1

        #Ignore today's events
        if 0 < days_ago(date) <= report_days:
            report_imsis.add(fields[3].strip(","))
            for c in credit_types:
                if c in line:
                    report[c] += 1
                    if c == "transfer":
                        record = process_transfer(line)
                        if record:
                            transfers.append(record)

            record = process_web_update(line)
            if (record):
                updates.append(record)

            record = process_provision_event(line)
            if (record):
                provisions.append(record)

    # all transfers show up in log twice, so correct for that
    lifetime["transfer"] /= 2
    report["transfer"] /= 2

    print format_report(lifetime, report, report_days, transfers, updates, lifetime_imsis, report_imsis)
