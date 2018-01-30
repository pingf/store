import etcd3
from loader.dictionary import unpack

from store.base import BaseStore, transform_key


def transform(key):
    if '.' in key:
        key = key.replace('.', '/')
    if not key.startswith('/'):
        key = '/' + key
    return key


class ETCDStore(BaseStore):
    def __init__(self, data):
        (
            host, port, user, password, timeout
        ) = unpack(data,
                   ('host', 'localhost'),
                   ('port', 2379),
                   'user', 'password', 'timeout')

        self.store = etcd3.client(host=host, port=port, timeout=timeout,
                                  user=user, password=password)

    def _transform_key(self, key):
        if '.' in key:
            key = key.replace('.', '/')
        if not key.startswith('/'):
            key = '/' + key
        return key

    def create(self, key, value, lease=None):
        # pylint: disable=arguments-differ
        data = self.read(key)
        return data if data[0] else self.update(key, value, lease)

    @transform_key
    def read(self, key, prefix=False):
        # pylint: disable=arguments-differ
        return self.store.get_prefix(key) if prefix else self.store.get(key)

    def update(self, key, value, lease=None):
        # pylint: disable=arguments-differ
        self.store.put(key, value, lease)
        value = self.read(key)
        return value

    def delete(self, key, prefix=False):
        # pylint: disable=arguments-differ
        return self.store.delete_prefix(key) if prefix else self.store.delete(key)

    @transform_key
    def __contains__(self, key):
        return self.read(key)[0] is not None

    def __iter__(self):
        return iter(self.read('/', prefix=True))

    def __len__(self):
        return len(self.read('/', prefix=True))
