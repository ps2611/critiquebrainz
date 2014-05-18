import hashlib
import memcache
from critiquebrainz import app

cache = memcache.Client(app.config['MEMCACHED_SERVERS'], debug=0)


def generate_cache_key(id, type=None, source=None, params=[]):
    key = app.config['MEMCACHED_NAMESPACE'] + ':'
    if source is not None:
        key += str(source) + ':'
    if type is not None:
        key += str(type) + ':'
    key += str(id)
    for param in params:
        if not isinstance(param, basestring):
            param = str(param)
        key += '_' + param.encode('ascii', 'ignore')
    key = key.replace(' ', '_')
    if len(key) > 250:  # 250 bytes is the maximum key length in memcached
        key = hashlib.sha1(key).hexdigest()
    return key