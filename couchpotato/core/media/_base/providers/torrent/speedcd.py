from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import toUnicode
from couchpotato.core.helpers.variable import tryInt, tryFloat
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from re import findall
from time import mktime, time
from dateutil.parser import parse
import traceback


log = CPLog(__name__)


class Base(TorrentProvider):

    urls = {
        'test': 'http://speed.cd/',
        'login': 'http://speed.cd/take_login.php',
        'login_check': 'http://speed.cd/inbox.php',
        'detail': 'http://speed.cd/t/%s',
        'search': 'http://speed.cd/V3/API/API.php',
        'download': 'http://speed.cd/download.php?torrent=%s',
    }

    http_time_between_calls = 1  # Seconds

    def _searchOnTitle(self, title, media, quality, results):
        query = '"%s" %s' % (title, media['info']['year'])

        data = self.getJson(query, quality, 1)  # get first result page
        try:
            torrents = data.get('Fs', [])[0].get('Cn', {}).get('torrents', [])
        except AttributeError:  # no results at all
            return

        pager = data.get('Fs', [])[0].get('Cn', {}).get('pager', [])
        maxpage = findall(r'Last Page\' id=\'(?P<maxpage>\d+)\'', pager)  # find maxpage

        if tryInt(maxpage) > 1:  # fetch remaining pages
            for page in range(2, tryInt(maxpage)):
                data = self.getJson(query, quality, page)
                torrents.extend(data.get('Fs', [])[0].get('Cn', {}).get('torrents', []))  # append to list

        try:
            for torrent in torrents:
                if self.conf('minimal_seeds') and self.conf('minimal_seeds') > tryInt(torrent.get('seed')):
                    continue

                if self.conf('freelech_only') and not int(torrent['free']):  # filter freelech only
                    continue
                age = findall('^<span.*?title="(?P<date>[,:\w\s{1}]+)">', torrent['added'])[0]
                if age:
                    age = '%.1f' % ((time() - mktime(parse(age).timetuple())) / (24 * 3600))

                results.append({
                    'id': torrent['id'],
                    'name': ''.join(BeautifulSoup(torrent['name']).findAll(text=True)).strip(),
                    'url': self.urls['download'] % (torrent['id']),
                    'detail_url': self.urls['detail'] % torrent['id'],
                    'size': self.parseSize(torrent.get('size')),
                    'seeders': tryInt(torrent.get('seed')),
                    'leechers': tryInt(torrent.get('leech')),
                    'age': tryFloat(age),
                })
        except:
                log.error('Failed getting results from %s: %s', (self.getName(), traceback.format_exc()))

    def getJson(self, query, quality, page):
        data = {
            'jxt': 4,
            'jxw': 'b',
            'search': query,
            'p': page,
        }
        cat = self.getCatId(quality)
        for acat in cat:
            data['c%s' % acat] = 1
        return self.getJsonData(self.urls['search'], data=data)

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
    'name': 'speedcd',
    'groups': [
        {
            'tab': 'searcher',
            'list': 'torrent_providers',
            'name': 'Speed.cd',
            'description': '<a href="http://speed.cd/">Speed.cd</a>',
            'wizard': True,
            'icon': 'AAABAAEAEBAAAAAAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAQAQAAAAAAAAAAAAAAAAAAAAAAAD///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B ////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/ //8B////Af///wH///8B////AQAAABUAAACDAAAAkwAAAIUAAACBAAAAgQAAAIEAAABxAAAAEf// /wH///8BAAAAUf///wH///8B////Af///wEAAADNAH8A/wDCAP8ArQD/AH8A/wBwAP8AYAD/AAAA /wAAALH///8BAAAAIQAAAP8AAABB////Af///wH///8BAAAA/wD/AP8A/wD/APoA/wDaAP8AwwD/ AK8A/wCaAP8AAADB////AQAAAKEASob/AAAAwf///wH///8B////AQAAALsA7gD/AP8A/wD4AP8A 3wD/AMMA/wCvAP8AUQD/AAAAoQAAACEAAAD/AMj//wAMKP8AAABD////Af///wEAAABJAD4A/wD/ AP8A9wD/AOAA/wDDAP8ArwD/AAAA/wAAACEAAAChAGK7/wDM//8Auff/AAAAxf///wH///8B//// AQAAAMcA2wD/APUA/wDgAP8AwwD/AGAA/wAAAKEAAAAhAAAA/wCx//8Az///AOT//wApO/8AAABH ////Af///wEAAABFACMA/wDxAP8A3QD/AMMA/wAAAP8AAAAhAAAAoQBSu/8Asf//ANH//wDm//8A 0fr/AAAAyf///wH///8B////AQAAAMMAxQD/ANsA/wCGAP8AAAChAAAAIQAAAP8Anv//ALH//wDR //8A6f//APr//wBBTf8AAABL////Af///wEAAABBAAkA/wDaAP8AAAD/AAAAIQAAAKEARbv/AJ7/ /wCy//8A0f//AOz//wD8//8A5v3/AAAAy////wH///8B////AQAAAMUAlQD/AAAAof///wEAAADB AIn//wCe//8Asv//AMr//wDw//8A////AP///wAAAP////8B////Af///wEAAABBAAAA/wAAACH/ //8BAAAAsQAAF/8AVLv/AGS7/wBzu/8AptP/AL7b/wCCjv8AAADP////Af///wH///8B////AQAA AFH///8B////AQAAABEAAABxAAAAgQAAAIEAAACBAAAAhQAAAJUAAACFAAAAFf///wH///8B//// Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B ////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/ //8BAAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA //8AAP//AAD//w==',
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
