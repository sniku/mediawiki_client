MEDIAWIKI_URL = 'http://en.wikipedia.org/' # remember to include the protocol. example: https://wiki.example.com/
HTTP_AUTH_USERNAME = ''
HTTP_AUTH_PASSWORD = ''


try:
    from local_settings import *
except:
    pass