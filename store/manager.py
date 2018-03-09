from store.base import BaseStore
from store.elastic import ElasticStore
from store.etcd import ETCDStore
from store.seaweed import SeaweedStore


class Manager:
    # pylint: disable=too-few-public-methods,no-member
    proxies = {
        'etcd': ETCDStore,
        'elastic': ElasticStore,
        'seaweed': SeaweedStore
    }

    def __new__(cls, name, data):
        return Manager.proxies.get(name, BaseStore)(data)


if __name__ == '__main__':
    # pylint: disable=too-few-public-methods,no-member,unsubscriptable-object,invalid-name
    m = Manager('etcd', data={})
    d = m.read('/', prefix=True)
    d = m['dameng.1']
    print(d)
