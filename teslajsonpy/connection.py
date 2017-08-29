import calendar
import datetime
from urllib.parse import urlencode
from urllib.request import Request, build_opener
import json


class Connection(object):
    """Connection to Tesla Motors API"""

    def __init__(self,
                 email='',
                 password='',
                 access_token='',
                ):
        """Initialize connection object

        Sets the vehicles field, a list of Vehicle objects
        associated with your account
        Required parameters:
        email: your login for teslamotors.com
        password: your password for teslamotors.com

        Optional parameters:
        access_token: API access token
        proxy_url: URL for proxy server
        proxy_user: username for proxy server
        proxy_password: password for proxy server
        """
        self.user_agent = 'Model S 2.1.79 (SM-G900V; Android REL 4.4.4; en_US';

        self.client_id = "81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
        self.client_secret = "c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3"
        self.baseurl = 'https://owner-api.teslamotors.com'
        self.api = '/api/1/'

        if access_token:
            self.__sethead(access_token)
        else:
            self.oauth = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "email": email,
                "password": password}
            self.expiration = 0

    def get(self, command):
        """Utility command to get data from API"""
        return self.post(command, None)

    def post(self, command, data={}):
        """Utility command to post data to API"""
        now = calendar.timegm(datetime.datetime.now().timetuple())
        if now > self.expiration:
            auth = self.__open("/oauth/token", data=self.oauth)
            self.__sethead(auth['access_token'],
                           auth['created_at'] + auth['expires_in'] - 86400)
        return self.__open("%s%s" % (self.api, command), headers=self.head, data=data)

    def __sethead(self, access_token, expiration=float('inf')):
        """Set HTTP header"""
        self.access_token = access_token
        self.expiration = expiration
        self.head = {"Authorization": "Bearer %s" % access_token,
                     "User-Agent": self.user_agent
                     }

    def __open(self, url, headers={}, data=None, baseurl=""):
        """Raw urlopen command"""
        if not baseurl:
            baseurl = self.baseurl
        req = Request("%s%s" % (baseurl, url), headers=headers)
        try:
            req.data = urlencode(data).encode('utf-8')  # Python 3
        except:
            try:
                req.add_data(urlencode(data))  # Python 2
            except:
                pass
        opener = build_opener()
        resp = opener.open(req)
        charset = resp.info().get('charset', 'utf-8')
        return json.loads(resp.read().decode(charset))
