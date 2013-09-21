import random

import twilio

import vbts_util

from twilio.rest import TwilioRestClient

class twilio_ic(vbts_util.interconnect):
    
    def __init__(self, conf):
        vbts_util.interconnect.__init__(self, conf)
        self.twilio_client = TwilioRestClient(self.conf['twilio_acct_sid'], self.conf['twilio_auth_token'])

    def get_next_avail_number(self):
        """
        Returns the next available number that we own. If none are available, buys it from Twilio.
        """
        area_code = int(self.conf['twilio_area_code'])
        numbers = [vbts_util.strip_number(str(n.phone_number)) for n in self.twilio_client.phone_numbers.list()]
        avail_numbers = vbts_util.get_next_avail_number(numbers)
        if (len(avail_numbers) == 0):
            # if we have none, get a new number
            new_numbers = self.twilio_client.phone_numbers.search(area_code=area_code)
            if not new_numbers:
                raise ValueError("No numbers available in area code %d" % area_code)
            num = new_numbers[0]
            if not num.purchase(): # this does the buy!
                raise ValueError("Purchasing number failed")
            # setup new number
            bought_num = self.twilio_client.phone_numbers.list(phone_number=num.phone_number)[0]
            bought_num.update(sms_url=self.conf['twilio_sms_url'], voice_url=self.conf['twilio_voice_url'], sms_fallback_url=self.conf['twilio_sms_fallback_url'], voice_method=self.conf['twilio_voice_method'], sms_method=self.conf['twilio_sms_method'], sms_fallback_method=self.conf['twilio_sms_fallback_method'])
            avail_numbers.append(vbts_util.strip_number(str(bought_num.phone_number)))

        return random.choice(avail_numbers)
    
    def send(self, to, from_, body, to_country="US", from_country="US"):
        """
        Send an SMS to Twilio. Returns true if the message was accepted, false otherwise.
        """
        # Clean up the to number before we send it out.  We always add a plus, and
        # libphonenumber is smart enough to sort it out from there (even if there's
        # already a plus).
        to = vbts_util.convert_to_e164("+" + to, None)

        # Our callerid is always in E.164.
        from_ = vbts_util.convert_to_e164(from_, from_country)
        try:
            message = self.twilio_client.sms.messages.create(to=to, from_=from_, body=body)
        except twilio.TwilioRestException:
            return False
        if message.status != "failed":
            # We consider it a success if Twilio reports message is queued,
            # sending, or sent.
            return True
        return False
