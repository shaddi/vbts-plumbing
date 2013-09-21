import math
import sqlite3
import yaml
import time
import syslog
from libvbts import Messenger

def get_conf_dict(conf_file="/etc/vbts_credit.conf"):
    conf_file = open(conf_file, "r")
    return yaml.load("".join(conf_file.readlines()))

conf = get_conf_dict() # do this first so we can use it later

fs = Messenger.Messenger()
logfile_location = conf['log_location'] # "/var/log/credits.log"

def log_credit(user, old_cred, new_cred, reason):
    #should probably have a file lock around this, but I don't have a way
    #to test it -kurtis
    tries = 0;
    while (tries < 10):
        try:
            fh = open(logfile_location, 'a')
            fh.write("%s user: %s, old_credit: %d, new_credit: %d, change: %d, reason: %s\n" % (time.strftime('%Y-%m-%d %H:%M:%S'), user, old_cred, new_cred, new_cred-old_cred, reason))
            fh.close()
            tries = 10
        except IOError:
            time.sleep(1)
            tries += 1

def _round_cost(billsec, rate_per_min):
    """ Round a (cost) value to the max of 0 or the next 100.
        Examples:
            round_cost(5) ==> 100
            round_cost(105) ==> 200
            round_cost(295) ==> 300
    """
    billsec = int(billsec)
    billsec = max(0, billsec - int(conf['free_seconds']))
    raw_cost = billsec / 60.0 * int(rate_per_min)
    return max(0, int(math.ceil(raw_cost / 100.0)) * 100)

def get_service_tariff(service_type):
    """
    Get the tariff for the given service type. Returns "None" if no such type.
    """
    try: 
        return int(conf[str(service_type)])
    except:
        syslog.syslog("Kurtis bad service type")
        return 0

def call_cost(duration_in_seconds, service_type):
    rate_per_min = get_service_tariff(service_type)
    return _round_cost(duration_in_seconds, rate_per_min)

def sms_cost(service_type):
    return get_service_tariff(service_type)

def transfer(amount, from_name, to_name, reason):
    __transfer(amount, from_name, to_name, reason)

def __transfer(amount, from_name, to_name, reason):
    amount = abs(amount) # don't allow negative transfers!
    deduct(amount, from_name, reason)
    add(amount, to_name, reason)

def deduct(amount, name, reason):
    res = __deduct(amount, name, reason)

def __deduct(amount, name, reason):
    curr_credit = get(name)
    new_credit = max(0, curr_credit - amount)
    set_(new_credit, name, reason)
    return new_credit

def add(amount, name, reason):
    res = __add(amount, name, reason)

def __add(amount, name, reason):
    curr_credit = get(name)
    new_credit = curr_credit + amount
    set_(new_credit, name, reason)
    return new_credit

def set_(amount, name, reason):
    res = __set_(amount, name, reason)

def __set_(amount, name, reason):
    amount = int(amount)
    curr_credit = get(name)
    fs.SR_set(("account_balance", str(amount)), ("name", name))
    log_credit(name, curr_credit, amount, reason)
    return amount

def get(name):
    return int(fs.SR_get("account_balance", ("name", name)))

def _name_from_number(number):
    #check if already a name
    res = fs.SR_get("callerid", ("name", number))
    if (res and res != ""):
        return number
    else:
        return fs.SR_get("name", ("callerid", number))

def _number_from_name(name):
    #check if already a number
    res = fs.SR_get("name", ("callerid", name))
    if (res and res !=""):
        return name
    else:
        return fs.SR_get("callerid", ("name", name))
