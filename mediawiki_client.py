#!/usr/bin/python
from BeautifulSoup import BeautifulSoup
import base64
from cmd import Cmd
import re
import sys
import os
from subprocess import call
import urllib
import urllib2
import urlparse
import settings
import tempfile


EDITOR = os.environ.get('EDITOR','vim')

class MediaWikiEditor(object):

    def open_article(self, initial_content):
        with tempfile.NamedTemporaryFile(suffix=".tmp") as tmpfile:
            tmpfile.write(initial_content)
            tmpfile.flush()
            call([EDITOR, tmpfile.name])
            edited_content = open(tmpfile.name).read()

            if edited_content != initial_content:
                pass
                #TODO: should save the edited article

class MediaWikiBrowser(object):
    """
    This class emulates a browser. It defines several helper classes for extracting/saving content.
    """

    def openurl(self, url):
        request = urllib2.Request(url)

        # Handle HTTP authentication
        if settings.HTTP_AUTH_USERNAME and settings.HTTP_AUTH_PASSWORD:
            base64string = base64.encodestring('%s:%s' % (settings.HTTP_AUTH_USERNAME, settings.HTTP_AUTH_PASSWORD)).replace('\n', '')
            request.add_header("Authorization", "Basic %s" % base64string)

        result = urllib2.urlopen(request)
        html_content = result.read()
        return html_content

    def get_page_content(self, url):
        html = self.openurl(url)
        soup = BeautifulSoup(html)
        return soup.find('textarea').text

    def _parse_search_results(self, html):
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
                span.replaceWith('   \033[92m'+span.text+'\033[0m   ')

            rendered_match = u''.join(match.contents)
            rendered_match = re.sub("\s\s+" , " ", rendered_match)

            hit = {'index': index, 'title': title, 'match': rendered_match, 'url': url}
            results.append(hit)

        return results


    def search(self, keyword):
        url = urlparse.urljoin(settings.MEDIAWIKI_URL, '/index.php?go=Go&search='+urllib.quote_plus(keyword) )
        html = self.openurl(url)
        search_results = self._parse_search_results(html)
        if not search_results:
            print u'No results for "%s"'% keyword
        else:
            for result in search_results:
                print result['index'], result['title'], '\n\t', result['match']
        return search_results


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


    def do_search(self, keyword):
        """ Search for the keyword """
        print 'Searching for', keyword
        self.last_results = self.browser.search(keyword)


    def do_display_article(self, url):
        page = self.browser.get_page_content(url)
        # print page
        self.editor.open_article(page)

    def do_display_search_result(self, index):
        print 'Displaying', index
        try:
            index = int(index) - 1 # we enumerated starting on 1
            hit = self.last_results[index]
        except IndexError:
            print 'Wrong index - try again'
        else:
            url = urlparse.urljoin(settings.MEDIAWIKI_URL, '/index.php?action=edit&title=' + urllib.quote_plus(hit['title']) )
            self.do_display_article(url)


    def edit(self, url):
        pass

    def save(self, content, url):
        pass

    def do_EOF(self, line):
        print 'bye'
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

if __name__ == '__main__':
    m = MediaWikiInteractiveCommands()
    a = m.cmdloop()
