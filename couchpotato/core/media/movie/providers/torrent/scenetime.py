from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.scenetime import Base
from couchpotato.core.media.movie.providers.base import MovieProvider

log = CPLog(__name__)

autoload = 'scenetime'


class scenetime(MovieProvider, Base):

    cat_ids = [
        ([59, 81, 102], ['720p', '1080p']),
        ([1, 57, 82, 103], ['cam', 'ts', 'dvdrip', 'tc', 'r5', 'scr', 'brrip', 'webrip', 'web-dl']),
        ([3], ['dvdr']),
        ([64], ['3d']),
    ]
