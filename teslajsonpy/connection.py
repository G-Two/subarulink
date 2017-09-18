import calendar
import datetime
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from urllib.error import HTTPError
import json
from time import sleep


class Connection(object):
    """Connection to Tesla Motors API"""
    def __init__(self, email, password, logger):
        """Initialize connection object"""
        self.user_agent = 'Model S 2.1.79 (SM-G900V; Android REL 4.4.4; en_US'
        self.client_id = "81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
        self.client_secret = "c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3"
        self.baseurl = 'https://owner-api.teslamotors.com'
        self.api = '/api/1/'
        self.oauth = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "email": email,
            "password": password}
        self.expiration = 0
        self.logger = logger

    def get(self, command):
        """Utility command to get data from API"""
        return self.post(command, None)

    def post(self, command, data={}):
        """Utility command to post data to API"""
        now = calendar.timegm(datetime.datetime.now().timetuple())
        if now > self.expiration:
            auth = self.__open("/oauth/token", data=self.oauth)
            self.__sethead(auth['access_token'])
        return self.__open("%s%s" % (self.api, command), headers=self.head, data=data)

    def __sethead(self, access_token):
        """Set HTTP header"""
        self.access_token = access_token
        now = calendar.timegm(datetime.datetime.now().timetuple())
        self.expiration = now + 1800
        print(self.expiration)
        self.head = {"Authorization": "Bearer %s" % access_token,
                     "User-Agent": self.user_agent
                     }

    def __open(self, url, headers={}, data=None, baseurl=""):
        """Raw urlopen command"""
        if not baseurl:
            baseurl = self.baseurl
        req = Request("%s%s" % (baseurl, url), headers=headers)
        try:
            req.data = urlencode(data).encode('utf-8')
        except TypeError:
            pass
        opener = build_opener()
        self.logger.debug(req.full_url)
        sleep_time = 1
        while True:
            try:
                resp = opener.open(req)
            except HTTPError as ex:
                self.logger.error('HTTPError: %s %s. Sleeping %s second(s)', sleep_time, ex.code, ex.reason)
                sleep(sleep_time)
                sleep_time *= 2
                continue
            break
        charset = resp.info().get('charset', 'utf-8')
        data = json.loads(resp.read().decode(charset))
        opener.close()
        return data
