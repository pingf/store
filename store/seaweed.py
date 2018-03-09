from pyseaweed import WeedFS

from store.base import BaseStore, StoreError


class SeaweedStore(BaseStore):
    def __init__(self, data):
        host = data.get('host', 'localhost')
        port = data.get('port', 9333)
        self.store = WeedFS(host, port)  # weed-fs master address and port
        self.ids = {}

    def create(self, key, value, mode='data'):
        if mode == 'file':
            resp = self.store.upload_file(path=value)
            self.ids[resp] = key
            return resp
        if mode == 'data':
            resp = self.store.upload_file(name=key, stream=value)
            self.ids[resp] = key
            return resp

    def read(self, key):
        # pylint: disable=unused-argument,no-self-use
        existed = self.store.file_exists(key)
        if existed:
            return self.store.get_file(key)

    def update(self, key, value, mode='data'):
        return self.create(key, value, mode)

    def delete(self, key):
        self.ids.pop(key, None)
        return self.store.delete_file(key)


if __name__ == '__main__':
    s = SeaweedStore({})
    # with open('test.txt', 'r') as f:
    #     content = f.read()
    r = s.create('hello.txt', 'test.txt', mode='file')
    print(s.read(r))
