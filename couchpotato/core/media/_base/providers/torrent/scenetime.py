from couchpotato.core.helpers.encoding import toUnicode
from couchpotato.core.helpers.variable import tryInt, tryFloat
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from time import mktime, time
from dateutil.parser import parse
from bs4 import BeautifulSoup
import re
import traceback


log = CPLog(__name__)


class Base(TorrentProvider):

    urls = {
        'test': 'https://www.scenetime.com/',
        'login': 'https://www.scenetime.com/takelogin.php',
        'login_check': 'https://www.scenetime.com/inbox.php',
        'detail': 'https://www.scenetime.com/%s',
        'search': 'https://www.scenetime.com/browse_API.php',
        'download': 'https://www.scenetime.com/%s',
    }

    http_time_between_calls = 1  # Seconds

    def _searchOnTitle(self, title, media, quality, results):
        try:
            data = {}
            query = '"%s" %s' % (title, media['info']['year'])
            data[0] = self.getPage(query, quality, 0)  # get first result page
            pages = re.findall(r'.*?browse.php.*?&page=(?P<page>\d{1,2})">', data[0])

            if len(pages):  # get the remaining pages if any
                pages = list(set(pages))  # make the pages list unique
                for pageid in pages:
                    data[pageid] = self.getPage(query, quality, pageid)

            for page_id, page_data in data.items():  # parse all pages
                html = BeautifulSoup(page_data)
                table = html.find('table')
                if table is None:  # No results
                    return

                torrents = table.findAll('tr', attrs={'class': 'browse'})
                for atorrent in torrents:
                    try:
                        cells = atorrent.findAll('td')
                        # apply some regex on the raw html
                        details, tid = re.match(r'.*?href="(?P<details>details.php\?id=(?P<id>\d+))">',
                                                str(cells)).groups()
                        download = re.match(r'.*?href="(?P<download>download.php/.*?\.torrent)', str(cells)).groups()

                        # strip html tags for the rest
                        text = [acell.text for acell in cells]
                        if len(text) != 8:  # invalid text representation
                            continue
                        name, freeleech, date = re.match(r'(?P<name>.*?)(?P<freeleech>\[Freeleech\])' +
                                                         r'?(?:\W+NEW!)?(?P<date>[\d\-\:\s{1}]+)$', text[1]).groups()
                        if self.conf('freelech_only') and freeleech is None:  # filter freelech only
                            continue
                        date = '%.1f' % ((time() - mktime(parse(date).timetuple())) / (24 * 3600))
                        size = self.parseSize(text[5])
                        seed = tryInt(text[6])
                        leech = tryInt(text[7])
                        if self.conf('minimal_seeds') and self.conf('minimal_seeds') > seed:  # filter minimal seeders
                            continue
                        results.append({'id': tid,
                                        'name': name.strip(),
                                        'url': self.urls['download'] % download,
                                        'detail_url': self.urls['detail'] % details,
                                        'age': date,
                                        'size': size,
                                        'seeders': seed,
                                        'leechers': leech})

                    except Exception as e:
                        log.debug("%s: Parse Failed: %s -> %s", (self.getName(), e, traceback.format_exc()))
                        continue
        except:
                log.error('Failed getting results from %s: %s', (self.getName(), traceback.format_exc()))

    def getPage(self, query, quality, page):
        data = {'sec': 'jax',
                'cata': 'yes',
                'search': query,
                'page': page
                }
        cat = self.getCatId(quality)
        for acat in cat:
            data['c%s' % acat] = 1
        return self.getHTMLData(self.urls['search'], data=data)

    def getLoginParams(self):
        return {
            'username': self.conf('username'),
            'password': self.conf('password'),
            'submit': 'submit',
        }

    def loginSuccess(self, output):
        return 'Password not correct' not in output

    def loginCheckSuccess(self, output):
        return 'logout.php' in output.lower()


config = [{
    'name': 'scenetime',
    'groups': [
        {
            'tab': 'searcher',
            'list': 'torrent_providers',
            'name': 'Scenetime',
            'description': '<a href="https://www.scenetime.com/">Scenetime</a>',
            'wizard': True,
            'icon': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAYBQTFRFAaYpAUsCA3sMAFwAAZ0mA4wbBWYCAWIAACEABXsRApYeS8hwAKIhA1MKBWAAAmUAAKIaAJcCApQhCGsAAJ4bB2wCHG4UCGEAATYAKYkvSsZtB2kAAKUhAFkABUYBAFEABIQVABYAAKMpBmwHAGgAAIYDBDgAAFYABDcABXMLAG0AV8p3AJEGBnQMSKBRrMuoAIEOAKElMLBPQ8VmttG1KoEqA6sxAJoeAG8XBnMMCGQAAIkUAHAETchwSMVuAAAAAJkQAmQVB20IAG8EYZ5eSsdt5PToruC7AKUmB2cEYr13qN+4VpNQ1OTUjcqXls2fXKBdpNesIZgyKY0zKJU4AHoaSMZqJKM9QMNjw+DHRcJnu9S36PHnA1sPAp8icMyH2erbAaUsAJkZJ5w7AHsAAKUfAHcJAKsqAJEYAJUTDGUEbKhuAIgRBIwXAHEABnQHSotDA4UXBYQRlOCpTo5IBIUYt+LDGY4quOXEAJ8TLHonPok8Ai8AAEAA////Tllp9BBY3gAAAIB0Uk5T/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////wA4BUtnAAABCklEQVR42hTPZ1PCQBSF4RuSGINCQgIsCCGFEAL2XlFRUbH3Lvbeu0bc/esuH99n7syZC4S8NTcVCqXuna2G0ighQPYa5YvkTyjZJ8vJqxCBo3DFOgl3fmM8P25Zs5vQdcpx/TfTGOOZFo6DAdi+VpTMHG38mfErlSKcDfP8+SrtpbV7nvcXYaPDeHlcpvCV/zCMh0NYvxTFfBuFXdsniq8BiE/mBkeEYypxuzXnC0CvnU7bfysU7rSJ9BMDnlDWfnsOKEzp5bpICjwW6c+1VXyrIZRIQTSI9PdaLzAIITUGmjCkRfcX2z0mSA8kE4gpqUKWzbKqmohIY/RbUl913JjrOK5bNQn5F2AAsfc/sRwBciAAAAAASUVORK5CYII=',

            'options': [
                {
                    'name': 'enabled',
                    'type': 'enabler',
                    'default': False,
                },
                {
                    'name': 'username',
                    'default': '',
                },
                {
                    'name': 'password',
                    'default': '',
                    'type': 'password',
                },
                {
                    'name': 'minimal_seeds',
                    'type': 'int',
                    'default': 1,
                    'advanced': True,
                    'description': 'Only return releases with minimal X seeds',
                },
                {
                    'name': 'freelech_only',
                    'label': 'Freelech only',
                    'type': 'bool',
                    'default': False,
                    'advanced': True,
                    'description': 'Only download Freelech releases.',
                },
                {
                    'name': 'seed_ratio',
                    'label': 'Seed ratio',
                    'type': 'float',
                    'default': 2,
                    'description': 'Will not be (re)moved until this seed ratio is met.',
                },
                {
                    'name': 'seed_time',
                    'label': 'Seed time',
                    'type': 'int',
                    'default': 40,
                    'description': 'Will not be (re)moved until this seed time (in hours) is met.',
                },
                {
                    'name': 'extra_score',
                    'advanced': True,
                    'label': 'Extra Score',
                    'type': 'int',
                    'default': 20,
                    'description': 'Starting score for each release found via this provider.',
                }
            ],
        },
    ],
}]
