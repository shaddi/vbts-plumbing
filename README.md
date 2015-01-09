# vbts-plumbing: Interconnect and Billing for VBTS

This is a collection of tools used for adding interconnect and billing to VBTS. It's based on tools developed for the Papua VBTS network, a project of UC Berkeley TIER. You can read our paper about the network [here](http://www.eecs.berkeley.edu/~kheimerl/pubs/vbts_ictd_13.pdf).

This project includes:

 * vbts-twilio: A (misnamed) implementation of interconnection that support send and receive of SMS through both Nexmo and Twilio.
 * vbts-credit: A prepaid billing and credit transfer system.
 * vbts-configs: Basic Freeswitch dialplan and chatplan that allow you to integrate with [libvbts](https://github.com/kheimerl/libvbts), vbts-twilio, and vbts-credit. 


## Installation
You should first go through the [OpenBTS installation procedure](http://wush.net/trac/rangepublic/wiki/BuildInstallRun), and [set up Freeswitch](http://wush.net/trac/rangepublic/wiki/freeswitchConfig) too. Make sure you build and install ```mod_xml_cdr``` when you're setting up Freeswitch.

Set up the dependencies:

 * Install the following Python packages using pip: snowflake, requests, webpy, smspdu, twilio, phonenumbers, flup.
 * Instal [pylibnexmo](https://github.com/kheimerl/libpynexmo).
 * Install lighttpd, and configure it to run on port 8081.

After that, just install vbts-credit and vbts-twilio as you normally do Python packages.

```bash
cd vbts-credit
python setup.py install
cd ../vbts-twilio
python setup.py install
```

You can then develop your own Freeswitch diaplan/chatplan based on the sample ones provided in vbts-configs.


## Contact
There are a lot of potential hangups in all this: building your own mini-phone network isn't simple. We're working on making the process easier, so please let us know if you run into trouble.

 * [Kurtis Heimerl](http://www.eecs.berkeley.edu/~kheimerl/)
 * [Shaddi Hasan](http://www.eecs.berkeley.edu/~shaddi/)


If you're looking for a ready-to-use solution, check out [Endaga](http://www.endaga.com)!
