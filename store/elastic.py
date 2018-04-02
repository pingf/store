import json
import logging
from datetime import datetime

import elasticsearch

from store.base import BaseStore, transform_key


def transform(key):
    if '.' in key:
        key = key.replace('.', '/')
    if not key.startswith('/'):
        key = '/' + key
    return key


class ElasticStore(BaseStore):
    def __init__(self, data):
        log = data.get('log', 'store')
        self.log = logging.getLogger(log)

        # hosts = [{"host": "xx.xxx.x.xx"},
        #          {"host": "xx.xxx.x.xx"},
        #          {"host": "xx.xxx.x.xx"},
        #          {"host": "xx.xxx.x.xx"}, ]
        index = data.get('index')
        self.index = index
        settings = data.get('settings')
        mappings = data.get('mappings')

        # hosts = [
        #     {"host": data.get('host', '127.0.0.1'), "port": data.get('port', 9200)},
        # ]
        self.hosts = data.get('hosts', [{'host': '127.0.0.1', 'port': 9200}])

        create = data.get('create')
        if create:
            self.create_index(index, settings=settings, mappings=mappings)

        self.ids = set()

    def read_index(self, index='default'):

        store = elasticsearch.Elasticsearch(
            self.hosts,
            # sniff_on_start=True,
            # sniff_on_connection_fail=True,
            # sniffer_timeout=600
        )
        return store.indices.get(index=index)

    def create_index(self, index='default', settings=None, mappings=None):
        store = elasticsearch.Elasticsearch(
            self.hosts,
            # sniff_on_start=True,
            # sniff_on_connection_fail=True,
            # sniffer_timeout=600
        )
        self.index = index
        try:
            existed_index = self.read_index(index=index)
        except elasticsearch.exceptions.NotFoundError as exc:
            # None can not be set to body, so {} is needed
            body = {
                "settings": {
                    index: settings or {}
                },
                "mappings": {
                    index: {"properties": mappings or {}}
                }
            }
            try:
                resp = store.indices.create(index=self.index, body=body)
            except elasticsearch.TransportError as e:
                self.log.error('index create failed!')
        else:
            self.log.warning('index already existed')

    def bool_query(self, must_fields=None, filter_fields=None, should_fields=None, must_not_fields=None,
                   sort='@timestamp:desc',  # from_=None, to_='now',
                   offset=0,
                   size=1000):
        store = elasticsearch.Elasticsearch(
            self.hosts,
            # sniff_on_start=True,
            # sniff_on_connection_fail=True,
            # sniffer_timeout=600
        )
        # "term", "range", ...
        body = {
            "query": {"bool": {}},
        }
        if must_fields:
            body['query']['bool']['must'] = must_fields
        if filter_fields:
            body['query']['bool']['filter'] = filter_fields
        if should_fields:
            body['query']['bool']['should'] = should_fields
        if must_not_fields:
            body['query']['bool']['must_not'] = must_not_fields

        res = store.search(index=self.index,
                           from_=offset,
                           size=size,
                           sort=sort,
                           body=body)
        return res

    # def bool_query_type1(self, bool_query_fields, bool_query_type='must', sort='@timestamp:desc', from_=None, to_='now',
        return res

    def create(self, data, id_=None, extra=None):
        store = elasticsearch.Elasticsearch(
            self.hosts,
            # sniff_on_start=True,
            # sniff_on_connection_fail=True,
            # sniffer_timeout=600
        )

        data['@timestamp'] = datetime.utcnow()
        if isinstance(extra, dict):
            data.update(extra)

        res = store.index(index=self.index, doc_type=self.index, body=data, id=id_)
        if isinstance(res, dict):
            res_id = res.get('_id')
            if res_id not in self.ids:
                self.ids.add(res_id)
        return res

    def read(self, key, from_='now-30d', to_='now', offset=0, size=1000):
        store = elasticsearch.Elasticsearch(
            self.hosts,
            # sniff_on_start=True,
            # sniff_on_connection_fail=True,
            # sniffer_timeout=600
        )
        if isinstance(key, str):
            try:
                res = store.get(index=self.index, doc_type=self.index, id=key)
                res = {'total': 1, 'data': res}

            except elasticsearch.exceptions.NotFoundError as exc:
                res = {'total': 0, 'data': None}
        else:
            must_fields = [{"term": {k: v}} for k, v in key.items()]
            filter_fields = [{"range": {"@timestamp": {"gte": from_, "lt": to_}}}]
            res = self.bool_query(must_fields=must_fields, filter_fields=filter_fields, offset=offset, size=size)
            hits = res.get('hits')
            if isinstance(hits, dict):
                total = hits.get('total')
                finds = hits.get('hits')
                res = {'total': total, 'data': finds}

        return res

    def update(self, key, value):
        store = elasticsearch.Elasticsearch(
            self.hosts,
            # sniff_on_start=True,
            # sniff_on_connection_fail=True,
            # sniffer_timeout=600
        )
        data = self.read(key)
        if isinstance(data, dict):
            total = data.get('total')
            if total and total > 0:
                if total == 1:
                    # key is str
                    id_ = data.get('data').get('_id')
                    store.update(index=self.index, doc_type=self.index, id=id_, body={
                        # script is more powerful here
                        "doc": value
                    })
                else:
                    for d in data:
                        id_ = d.get('data').get('_id')
                        store.update(index=self.index, doc_type=self.index, id=id_, body={
                            # script is more powerful here
                            "doc": value
                        })
                return self.read(key)
        if isinstance(key, dict):
            key.update(value)
            self.create(key)
        else:
            self.create(data=value, id_=key)
        return self.read(key)

    def delete(self, key):
        store = elasticsearch.Elasticsearch(
            self.hosts,
            # sniff_on_start=True,
            # sniff_on_connection_fail=True,
            # sniffer_timeout=600
        )
        data = self.read(key)
        if isinstance(data, dict):
            total = data.get('total')
            if total and total > 0:
                if total == 1:
                    id_ = data.get('data').get('_id')
                    store.delete(index=self.index, doc_type=self.index, id=id_)
                    if id_ in self.ids:
                        self.ids.remove(id_)
                else:
                    for d in data:
                        id_ = d.get('data').get('_id')
                        store.delete(index=self.index, doc_type=self.index, id=id_)
                        if id_ in self.ids:
                            self.ids.remove(id_)
                return self.read(key)


if __name__ == '__main__':
    store = ElasticStore({"body": {}, 'index': 'store'})
    store.create_index('store')
    store.create({'hello': 'world'})
    store.read({'hello': 'world'})
    store.read('upbiBWIBcLxfSztCbbZC')
    print('....................')
    store.update('upbiBWIBcLxfSztCbbZC', {'test': '123'})
    store.read('upbiBWIBcLxfSztCbbZC')
    print('....................')
    store.update('1111', {'test': '123'})
    print('....................')
    resp = store.delete('1111')
    # print(resp)
