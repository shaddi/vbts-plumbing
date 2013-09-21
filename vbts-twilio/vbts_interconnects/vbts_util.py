import re
import yaml
import phonenumbers

from libvbts import Messenger
messenger = Messenger.Messenger()

def get_conf_dict(conf_file="/etc/vbts_twilio.conf"):
    conf_file = open(conf_file, "r")
    return yaml.load("".join(conf_file.readlines()))

def strip_number(number):
    """
    Strips the number down to just digits.
    """
    number = re.sub("[^0-9]", "", number)
    return number

def convert_to_e164(number, country="US"):
    return str(phonenumbers.format_number(phonenumbers.parse(number, country), phonenumbers.PhoneNumberFormat.E164))

def get_next_avail_number(numbers):
    avail_numbers = []
    for n in numbers:
        if not messenger.SR_dialdata_get("id", ("exten", n)):
            avail_numbers.append(n)
    return avail_numbers

class interconnect:

    def __init__(self, conf):
        self.conf = conf

    def get_next_avail_number(self):
        raise NotImplemented("Virtual Function")

    def send(self, to, from_, body,  to_country="US", from_country="US"):
        raise NotImplemented("Virtual Function")
