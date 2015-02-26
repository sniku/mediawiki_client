#!/usr/bin/python

import base64
from cmd import Cmd
import re
import os
import sys
import datetime

from subprocess import call, Popen, PIPE
import urllib
import urlparse
import tempfile
from os.path import expanduser
import ConfigParser
from BeautifulSoup import BeautifulSoup
import twill.commands
import twill

CONFIG_FILE = expanduser('~/.config/wiki_client.conf')

class Settings(dict):
    def __init__(self):
        super(Settings, self).__init__()
        if self.check_config_file():
            self.read_config()
            self.validate_settings()

    def read_config(self):
        booleans = ['verbose']
        config = ConfigParser.ConfigParser()
        config.read(CONFIG_FILE)
        options = config.options('defaults')
        for option in options:
            if option in booleans:
                self[option] = config.getboolean('defaults', option)
            else:
                self[option] = config.get('defaults', option)

        self['editor'] = self.get('force_editor', None) or os.environ.get('EDITOR', 'vim')

    def check_config_file(self):
        if not os.path.isfile(CONFIG_FILE):
            raise Exception(u'Config file %s is missing.'%CONFIG_FILE)
        return True

    def validate_settings(self):
        if not self.get('mediawiki_url', None):
            raise Exception(u"Config directive 'mediawiki_url' is empty of missing. You must provide URL to your mediawiki installation")

settings = Settings()

class MediaWikiEditor(object):

    def open_article(self, initial_content, title=""):

        assert(type(initial_content) == unicode)

        if title: # sanitize for security
            title = "".join(x for x in title if x.isalnum())
        prefix = (title or "tmp") + "__["


        edited_content = u''
        with tempfile.NamedTemporaryFile(prefix=prefix, suffix="].tmp.wiki", delete=False,) as tmpfile:
            tmpfile.write(initial_content.encode('utf8'))
            tmpfile.flush()
            editor_with_args = settings['editor'].split(" ")  + [tmpfile.name]
            # print editor_with_args
            call(editor_with_args)
            tmpfile.flush()
            tmpfile.close()

            edited_file = open(tmpfile.name)
            edited_content = edited_file.read().decode('utf8')
            edited_file.close()

            os.unlink(tmpfile.name) 

        return edited_content, initial_content


class MediaWikiBrowser(object):
    """
    This class emulates a browser. It defines several helper classes for extracting/saving content.
    """

    def __init__(self):
        self.twill_browser = twill.get_browser()

        if not settings.get('verbose', True):
            twill.set_output(open(os.devnull, 'w'))
            #twill.browser.OUT = open(os.devnull, 'w')

        # Handle HTTP authentication
        if settings.get('http_auth_username', None) and settings.get('http_auth_password', None):
            base64string = base64.encodestring('%s:%s' % (settings['http_auth_username'], settings['http_auth_password'])).replace('\n', '')
            twill.commands.add_auth("wiki", settings['mediawiki_url'], settings['http_auth_username'], settings['http_auth_password'])
            #self.twill_browser._session.headers.update([("Authorization", "Basic %s" % base64string)])
            twill.commands.add_extra_header("Authorization", "Basic %s" % base64string)

        # Handle Mediawiki authentication
        if settings.get('mediawiki_username', None) and settings.get('mediawiki_password', None):
            login_url = urlparse.urljoin(settings['mediawiki_url'], '/index.php?title=Special:UserLogin')
            self.openurl(login_url)

            self._set_form_value('userlogin', 'wpName', settings.get('mediawiki_username'))
            self._set_form_value('userlogin', 'wpPassword', settings.get('mediawiki_password'))

            self.twill_browser.submit()

        self.openurl(settings['mediawiki_url'])

    def _set_form_value(self, formname, fieldname, fieldvalue):
        """
        This is a workaround for a bug in twill
        """

        # for some unknown to me reason this doesn't set the form field in new twill
        # but at least it selects the form
        twill.commands.formvalue(formname, fieldname, fieldvalue)

        form = self.twill_browser.get_form(formname)

        # this on the other hand sets the form field in new twill but fails in old one (!?)
        if hasattr(form, 'fields'):
            form.fields[fieldname] = fieldvalue


    #@deprecated
    def add_auth(self, url):
        """
        Handle HTTP authentication
        """
        base64string = base64.encodestring('%s:%s' % (settings['http_auth_username'], settings['http_auth_password'])).replace('\n', '')
        self.twill_browser._session.headers.update([("Authorization", "Basic %s" % base64string)])

        if settings.get('http_auth_username', None) and settings.get('http_auth_password', None):
            self.twill_browser._set_creds( (url, (settings['http_auth_username'], settings['http_auth_password'])) )


    def save_article(self, url, new_content):

        new_content = new_content.encode("utf8")

        self.openurl(url)

        self._set_form_value('editform', 'wpTextbox1', new_content)

        self.twill_browser.submit("wpSave")

    def openurl(self, url):
        # self.add_auth(url)
        self.twill_browser.go(url)
        content = self.twill_browser.result.get_page()
        return content

    def is_redirect(self, content):
        """
        checks if this page redirects to somewhere else
        """
        if content.startswith("#REDIRECT"):
            s = re.findall(r"\#REDIRECT \[\[(.*?)\]\]", content)
            if s:
                print "Redirecting to {}".format(s[0])
                return True, s[0]
        return False, None

    def rename_article(self, current_name, new_name, leave_redirect):

        url = urlparse.urljoin(settings['mediawiki_url'], '/index.php/Special:MovePage/' + urllib.quote_plus(current_name) )
        self.openurl(url)
        self._set_form_value('movepage', "wpNewTitleMain", new_name)
        self._set_form_value('movepage', "wpReason", "moved using mediawiki client on " + datetime.datetime.now().isoformat())
        self._set_form_value('movepage', "wpLeaveRedirect", leave_redirect)
        self.twill_browser.submit("wpMove")



    def get_page_content(self, url):
        self.openurl(url)

        form = self.twill_browser.get_form('editform')
        content = self.twill_browser.get_form_field(form, 'wpTextbox1').value

        if type(content) == str:
            content = content.decode("utf-8")

        assert( type(content) == unicode )


        need_redirect, where = self.is_redirect(content)

        if need_redirect:
            new_url = urlparse.urljoin(settings['mediawiki_url'], '/index.php?action=edit&title=' + urllib.quote_plus(where) )
            return self.get_page_content(new_url)

        return content


    def upload_file(self, filepath, alt_filename):
        UPLOAD_FORM_URL = '/index.php/Special:Upload'
        FORM_ID = 'mw-upload-form'
        self.openurl(UPLOAD_FORM_URL)
        form = self.twill_browser.get_form(FORM_ID)
        self._set_form_value(FORM_ID, 'wpIgnoreWarning', '1')
        filename = alt_filename or os.path.split(filepath)[1]
        twill.commands.formfile(FORM_ID, 'wpUploadFile', filepath)
        self._set_form_value(FORM_ID, 'wpDestFile', filename)
        self._set_form_value(FORM_ID, 'wpUploadDescription', "uploaded with mediawiki_client")

        self.twill_browser.submit("wpUpload")

        html = self.twill_browser.result.get_page()
        soup = BeautifulSoup(html)
        div = soup.find('div', attrs={'class': 'fullMedia'})
        a = div.find('a')
        url_to_uploaded_asset = urlparse.urljoin(settings['mediawiki_url'], a['href'])
        return url_to_uploaded_asset

    @staticmethod
    def _parse_search_results(html):
        soup = BeautifulSoup(html)

        container = soup.find('ul', attrs={'class': 'mw-search-results'})
        if not container:
            return []

        results = []

        results_li = container.findAll('li')
        for index, li in enumerate(results_li, start=1):
            a = li.find('a')
            title = a['title']
            url = a['href']

            match = li.find('div', {'class': 'searchresult'})
            for span in match.findAll('span'):
                span.replaceWith('   \033[92m'+span.text+'\033[0m   ')  # make it green

            rendered_match = u''.join(match.contents)
            rendered_match = re.sub("\s\s+", " ", rendered_match)

            hit = {'what': 'search_result', 'index': index, 'title': title, 'match': rendered_match, 'url': url}
            results.append(hit)

        return results

    @staticmethod
    def paste_to_clipboard(content, p=True, c=True):
        """
        puts the "content" into clipboard.
        """
        if p:
            p = Popen(['xsel', '-pi'], stdin=PIPE)
            p.communicate(input=content)
        if c:
            p = Popen(['xsel', '-bi'], stdin=PIPE)
            p.communicate(input=content)


    def search(self, keyword):
        url = urlparse.urljoin(settings['mediawiki_url'], '/index.php?go=Go&search='+urllib.quote_plus(keyword) )
        html = self.openurl(url)

        if "search=" in self.twill_browser.result.get_url():
            # we are on the search page
            search_results = self._parse_search_results(html)
            return search_results
        else:
            # perfect match - redirected to the page
            # page name can have different capitalization
            return [{'what': 'perfect_match', 'page_name': self.twill_browser.result.get_url().rsplit('/', 1)[1]}]



class MediaWikiInteractiveCommands(Cmd):
    """
    This class implements all the interactive commands.
    """
    def __init__(self, *args, **kwargs):
        Cmd.__init__(self)
        #super(MediaWiki, self).__init__(*args, **kwargs)
        self.prompt = '\nWiki command: '
        self.browser = MediaWikiBrowser()
        self.editor = MediaWikiEditor()
        self.last_search_results = []
        self.last_search_query = ''


    def do_search(self, keyword, quiet=False):
        """ Search for a keyword """
        self.last_search_query = keyword
        self.last_search_results = self.browser.search(self.last_search_query )
        if not quiet:
            print 'Searching for', self.last_search_query
            self.display_search_list()

    def display_search_list(self):
        """ Display the last search result """
        if not self.last_search_results:
            print u'No results for "%s"' % self.last_search_query
        else:
            # directly display the page
            if len(self.last_search_results) == 1 and self.last_search_results[0]['what'] == 'perfect_match':
                print 'Opening', self.last_search_query
                self.do_go(self.last_search_results[0]['page_name'])
            else:
                for result in self.last_search_results:
                    print result['index'], result['title'], '\n\t', result['match']

    def do_go(self, page_name):
        """ go to a specified page. Type "go <pagetitle>" """
        url = urlparse.urljoin(settings['mediawiki_url'], '/index.php?action=edit&title=' + urllib.quote_plus(page_name) )
        self.display_article(url, page_name)

    def display_article(self, url, title=""):
        """ Display the last search result """
        page = self.browser.get_page_content(url)
        new_content, old_content = self.editor.open_article(page, title)

        if old_content != new_content:
            self.browser.save_article(url, new_content)

    def log_and_save(self, page_name, text_to_log):
        """
        Log is the same as append, but it adds a datetime in front of the text
        """
        now = u"{:%Y-%m-%d %H:%M} ".format(datetime.datetime.now())
        text_to_log = now + text_to_log
        self.append_to_article_and_save(page_name, text_to_log)


    def append_to_article_and_save(self, page_name, text_to_append):
        """
        appends text to the bottom of an article and saves
        """
        assert( type(text_to_append) == unicode )

        url = urlparse.urljoin(settings['mediawiki_url'], '/index.php?action=edit&title=' + urllib.quote_plus(page_name) )
        page_content = self.browser.get_page_content(url)
        page_content += text_to_append.strip()
        self.browser.save_article(url, page_content)

    def cat(self, page_name):
        """
        simply print the content of the article
        """
        url = urlparse.urljoin(settings['mediawiki_url'], '/index.php?action=edit&title=' + urllib.quote_plus(page_name) )
        page_content = self.browser.get_page_content(url)
        print page_content

    def mv(self, current_name, new_name, leave_redirect=True):
        """
        rename article
        """
        self.browser.rename_article(current_name, new_name, leave_redirect=leave_redirect)



    def append_to_article_and_open(self, page_name, text_to_append):

        assert( type(text_to_append) == unicode )

        url = urlparse.urljoin(settings['mediawiki_url'], '/index.php?action=edit&title=' + urllib.quote_plus(page_name) )
        page_content = self.browser.get_page_content(url)
        page_content += text_to_append.strip()
        new_content, old_content = self.editor.open_article(page_content, page_name)
        self.browser.save_article(url, new_content)

    def do_upload_file(self, filepath, alt_filename):
        filepath = os.path.abspath(filepath)
        if not os.path.exists(filepath):
            print(u"File path \"{}\" doesn't exist - nothing uploaded".format(filepath))
        else:
            file_url = self.browser.upload_file(filepath, alt_filename)
            print u"Uploaded file: {}".format(file_url)
            self.browser.paste_to_clipboard(file_url)


    def do_display_search_result(self, index):
        """ displays the article specified by the index in the search list  """
        try:
            index = int(index) - 1 # we enumerated starting on 1
            hit = self.last_search_results[index]
        except IndexError:
            print 'Wrong index - try again'
        else:
            print 'Opening', hit['title']

            url = urlparse.urljoin(settings['mediawiki_url'], '/index.php?action=edit&title=' + urllib.quote_plus(hit['title']) )
            self.display_article(url, hit['title'])

    def do_EOF(self, line):
        """ quit """
        print '\nbye'
        return True

    def precmd(self, line):
        if not line or len(line) == 0:
            return line
        line = unicode(line)

        cmd = line.split()[0]

        if line.startswith('/'):
            line = 'search ' + line[1:]
        elif cmd.isnumeric():
            line = 'display_search_result '+cmd

        return line

    def postloop(self):
        print

def run(args):
    m = MediaWikiInteractiveCommands()
    stdin_data = None
    interactive = False

    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read()

        tty = open('/dev/tty', 'r')
        os.dup2(tty.fileno(), 0)


    if args['<article_name>']:

        if args['append']:
            if args['<text>']:
                # append text to extisting article and save
                text_to_append = args['<text>'].decode('utf8')
                m.append_to_article_and_save(args['<article_name>'], text_to_append)
        elif args['log']:
            if args['<text>']:
                text_to_log = args['<text>'].decode('utf8')
                m.log_and_save(args['<article_name>'], text_to_log)
        elif args["mv"]:
            m.mv(args['<article_name>'], args['<new_name>'], args['--leave_redirect'])
        elif stdin_data is not None:
            stdin_data = stdin_data.decode('utf8')
            m.append_to_article_and_open(args['<article_name>'], stdin_data)
        elif args['cat']:
            m.cat(args['<article_name>'])
        elif args['<article_name>'][0] == "/":  # search
            m.do_search(args['<article_name>'][1:])
            interactive = True
        else:
            # just open article
            m.do_go(args['<article_name>'])
            interactive = True
    elif args['upload']:
            m.do_upload_file(args['<filepath>'], args['<alt_filename>'])
    else:
        interactive = True


    if interactive:
        # and go to interactive mode
        a = m.cmdloop()



if __name__ == '__main__':
    try:
        run(sys.argv)
    except:
        import pdb
        pdb.set_trace()
