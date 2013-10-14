#!/usr/bin/python

from BeautifulSoup import BeautifulSoup
import base64
from cmd import Cmd
import re
import os
from subprocess import call
import urllib
import urlparse
import settings
import tempfile
import twill

EDITOR = settings.FORCE_EDITOR or os.environ.get('EDITOR', 'vim')

class MediaWikiEditor(object):

    def open_article(self, initial_content):

        edited_content = ''
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as tmpfile:
            tmpfile.write(initial_content)
            tmpfile.flush()
            call([EDITOR, tmpfile.name])
            tmpfile.flush()
            tmpfile.close()

            edited_file = open(tmpfile.name)
            edited_content = edited_file.read()
            edited_file.close()


        return edited_content, initial_content


class MediaWikiBrowser(object):
    """
    This class emulates a browser. It defines several helper classes for extracting/saving content.
    """

    def __init__(self):
        self.twill_browser = twill.get_browser()
        twill.browser.OUT = open('/dev/null', 'w')

        # Handle HTTP authentication
        if settings.HTTP_AUTH_USERNAME and settings.HTTP_AUTH_PASSWORD:
            base64string = base64.encodestring('%s:%s' % (settings.HTTP_AUTH_USERNAME, settings.HTTP_AUTH_PASSWORD)).replace('\n', '')
            #twill_browser.addheaders( ("Authorization", "Basic %s" % base64string) )
            self.twill_browser._browser.addheaders += [("Authorization", "Basic %s" % base64string)]

        self.twill_browser.go(settings.MEDIAWIKI_URL)

    def save_article(self, url, new_content):
        self.twill_browser.go(url)
        self.twill_browser._browser.select_form('editform')

        twill.commands.formvalue('editform', 'wpTextbox1', new_content)

        self.twill_browser.submit()

        #TODO: validate settings and print error messages

    def openurl(self, url):
        self.twill_browser.go(url)
        return self.twill_browser.result.page


    def get_page_content(self, url):
        self.twill_browser.go(url)

        form = self.twill_browser.get_form('editform')
        content = self.twill_browser.get_form_field(form, 'wpTextbox1')._value
        return content

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

    def search(self, keyword):
        url = urlparse.urljoin(settings.MEDIAWIKI_URL, '/index.php?go=Go&search='+urllib.quote_plus(keyword) )
        html = self.openurl(url)

        if "search=" in self.twill_browser.result.url:
            # we are on the search page
            search_results = self._parse_search_results(html)
            return search_results
        else:
            # perfect match - redirected to the page
            # page name can have different capitalization
            return [{'what': 'perfect_match', 'page_name': self.twill_browser.result.url.rsplit('/', 1)[1]}]



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
        """ Search for the keyword """
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
        """ go to specified page """
        url = urlparse.urljoin(settings.MEDIAWIKI_URL, '/index.php?action=edit&title=' + urllib.quote_plus(page_name) )
        self.display_article(url)

    def display_article(self, url):
        """ Display the last search result """
        page = self.browser.get_page_content(url)
        # print page
        new_content, old_content = self.editor.open_article(page)

        if old_content != new_content:
            self.browser.save_article(url, new_content)



    def do_display_search_result(self, index):
        """ displays the article specified by the index in the search list  """
        try:
            index = int(index) - 1 # we enumerated starting on 1
            hit = self.last_search_results[index]
        except IndexError:
            print 'Wrong index - try again'
        else:
            print 'Opening', hit['title']

            url = urlparse.urljoin(settings.MEDIAWIKI_URL, '/index.php?action=edit&title=' + urllib.quote_plus(hit['title']) )
            self.display_article(url)

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
            line = 'search ' +line[1:]
        elif cmd.isnumeric():
            line = 'display_search_result '+cmd

        return line

    def postloop(self):
        print

def run():
    m = MediaWikiInteractiveCommands()
    a = m.cmdloop()


if __name__ == '__main__':
    run()
