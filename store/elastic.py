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
        # hosts = [{"host": "xx.xxx.x.xx"},
        #          {"host": "xx.xxx.x.xx"},
        #          {"host": "xx.xxx.x.xx"},
        #          {"host": "xx.xxx.x.xx"}, ]
        self.index=None

        hosts = [
            {"host": data.get('host', '127.0.0.1'), "port": data.get('port', 9200)},
        ]

        self.store = elasticsearch.Elasticsearch(
            hosts,
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniffer_timeout=600
        )

    def read_index(self, index='default'):
        return self.store.indices.get(index=index)

    def create_index(self, index='default', settings=None, mappings=None):
        self.index = index
        try:
            existed_index = self.read_index(index=index)
        except elasticsearch.exceptions.NotFoundError as exc:
            pass
        else:

            body = {
                "settings": {index: settings},
                "mappings": {
                    index: {"properties": mappings}
                }
            }
            resp = self.store.indices.create(index=index, body=body)

    def bool_query(self, bool_query_fields, bool_query_type='must', sort='@timestamp:desc', from_=None, to_='now', offset=0,
              size=1000, timefield='@timestamp'):
        body = {
            "query": {
                "bool": {
                    bool_query_type: [
                        {"term": {k: v}} for k, v in bool_query_fields.items()
                    ]
                }
            },
        }
        if from_ is not None:
            body['query']['bool']['filter'] = [{
                "range": {
                    timefield: {
                        "gte": from_,
                        "lt": to_
                    }
                }
            }]
        res = self.store.search(index=self.index,
                             from_=offset,
                             size=size,
                             sort=sort,
                             body=body)
        return res

    def create(self, key, value, lease=None):
        # pylint: disable=arguments-differ
        data = self.read(key)
        return data if data[0] else self.update(key, value, lease)

    @transform_key
    def read(self, key, from_=None, to_='now'):
        # pylint: disable=arguments-differ
        res = self.bool_query(bool_query_fields=key, from_=from_, to_=to_)
        return res


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


if __name__ == '__main__':
    print('>>>>>>>>>>>')
    ElasticStore({"body": {}})
