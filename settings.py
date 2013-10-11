
# URL to your wiki instalation
MEDIAWIKI_URL = 'https://wiki.example.com/' # remember to include the protocol. example: https://wiki.example.com/

# HTTP authentication
# leave empty if the page is public
HTTP_AUTH_USERNAME = ''
HTTP_AUTH_PASSWORD = ''

# leave empty if you want your default $EDITOR
# or choose vim, nano, pico, etc
FORCE_EDITOR = ''

try:
    from local_settings import *
except:
    pass