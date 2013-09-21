import random, syslog

from nexmomessage import NexmoMessage

import vbts_util

class nexmo_ic(vbts_util.interconnect):

    def __init__(self, conf):
        vbts_util.interconnect.__init__(self, conf)
        self.un = conf['nexmo_acct_sid']
        self.pw = conf['nexmo_auth_token']

    def __get_existing_numbers(self):
        req = {'password': self.pw, 'username': self.un}
        req['type'] = 'numbers'
        res = NexmoMessage(req).send_request()
        nums = []
        for r in res['numbers']:
            if (r['country'] == self.conf['nexmo_country_from']):
                nums.append(r['msisdn'])
        return nums

    def __search_numbers(self):
        req = {'password': self.pw, 'username': self.un}
        req['type'] = 'search'
        req['country'] = self.conf['nexmo_country_from']
        res = NexmoMessage(req).send_request()
        if (len(res['numbers']) < 1):
            raise ValueError("No Numbers Available")
        #may need to filter based on some desired properties, like mobile
        return random.choice(res['numbers'])['msisdn']

    def __buy_number(self, number):
        req = {'password': self.pw, 'username': self.un}
        req['type'] = 'buy'
        req['country'] = self.conf['nexmo_country_from']
        req['msisdn'] = number
        syslog.syslog("Kurtis: " + str(req))
        res = NexmoMessage(req).send_request()
        if (res['code'] == 200):
            return True
        return False

    def get_next_avail_number(self):
        """
        Returns the next available number that we own. If none are available, buys it from nexmo.
        """
        area_code = int(self.conf['twilio_area_code'])
        numbers = [vbts_util.strip_number(str(n)) for n in self.__get_existing_numbers()]
        avail_numbers = vbts_util.get_next_avail_number(numbers)
        if (len(avail_numbers) == 0):
            target = self.__search_numbers()
            if (self.__buy_number(target)):
                avail_numbers.append(str(target))
            else:
                raise ValueError("Purchasing number failed")
        return random.choice(avail_numbers)

    def send(self, to, from_, body, to_country=None, from_country=None):
        """
        Send an SMS to Nexmo. Returns true if the message was accepted, false otherwise.
        """
        # Convert "to" to e.164 format. We always add a plus, and
        # libphonenumber is smart enough to sort it out from there (even if
        # there's already a plus).
        to = vbts_util.convert_to_e164("+" + to, None)

        msg = {'reqtype': 'json', 'password': self.pw, 'from': from_, 'to': to, 'username': self.un}
        sms = NexmoMessage(msg)
        sms.set_text_info(body)
        res = sms.send_request()
        #we're basically creating aformatting AND here for readability
        if (res['message-count'] == '1'):
            if (res['messages'][0]['status'] == '0'):
                return True
        return False
