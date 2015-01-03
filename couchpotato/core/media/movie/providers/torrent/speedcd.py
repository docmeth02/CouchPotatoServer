from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.speedcd import Base
from couchpotato.core.media.movie.providers.base import MovieProvider

log = CPLog(__name__)

autoload = 'speedcd'


class speedcd(MovieProvider, Base):

    cat_ids = [
        ([43, 28, 47], ['720p', '1080p']),
        ([1, 28], ['cam', 'ts', 'dvdrip', 'tc', 'r5', 'scr', 'brrip']),
        ([40], ['dvdr']),
        ([48], ['3d']),
    ]
