from datetime import datetime

from pony.orm import Database, Required, Json, db_session, select
from pony.orm import delete as db_delete

from store.base import BaseStore

from pony import options

options.CUT_TRACEBACK = False


class PostgresStore(BaseStore):
    def __init__(self, data):
        db_type = data.get('type', 'postgres')
        db_user = data.get('user', 'dameng')
        db_password = data.get('password', 'hello')
        db_host = data.get('host', 'localhost')
        db_name = data.get('name', 'store')

        self.db = Database(db_type, user=db_user, password=db_password, host=db_host, database=db_name)
        body = dict(__doc__='docstring',
                    create_at=Required(datetime, sql_default='CURRENT_TIMESTAMP', default=lambda: datetime.utcnow()),
                    update_at=Required(datetime, sql_default='CURRENT_TIMESTAMP', default=lambda: datetime.utcnow()),

                    key=Required(str, index=True, unique=True),
                    value=Required(Json, volatile=True)

                    )

        self.Store = type("Store", (self.db.Entity,), body)
        self.db.generate_mapping(create_tables=True, check_tables=True)
        self.ids = set()

    @db_session
    def create(self, key, value):
        elem = select(e for e in self.Store if e.key == key).first()
        if elem is None:
            self.Store(key=key, value=value)
            self.ids.add(key)
        else:
            value_db = elem.value
            value_db.update(value)
            elem.value = value

    @db_session
    def read(self, key):
        elem = select(e for e in self.Store if e.key == key).first()
        if elem:
            return {
                'key': elem.key,
                'value': elem.value,
            }
        return None

    @db_session
    def update(self, key, value, mode='data'):
        elem = select(e for e in self.Store if e.key == key).first()
        if elem is None:
            return
        else:
            value_db = elem.value
            value_db.update(value)
            elem.value = value

    @db_session
    def delete(self, key):
        elem = select(e for e in self.Store if e.key == key).first()
        if elem:
            db_delete(e for e in self.Store if e.key == key)
            if key in self.ids:
                self.ids.remove(key)

    @db_session
    def query(self, value):
        keys = []
        values = []
        for k, v in value.items():
            keys.append(k)
            values.append(v)

        elemss = []
        for i, k in enumerate(keys):
            elems = select(e for e in self.Store if k in e.value and e.value[k] == values[i])[:]
            elemss.extend(elems)
        results = []
        for elem in elemss:
            e = {
                'key': elem.key,
                'value': elem.value
            }
            results.append(e)
        return results

    @db_session
    def query_in(self, value):
        # select from list, key must be matched, value is or relation
        keys = []
        values = []
        for k, v in value.items():
            if isinstance(v, str):
                keys.append(k)
                values.append(v)
            elif isinstance(v, list):
                for vv in v:
                    keys.append(k)
                    values.append(vv)

        elemss = []
        for i, k in enumerate(keys):
            elems = select(e for e in self.Store if k in e.value and values[i] in e.value[k])[:]
            elemss.extend(elems)
        results = []
        for elem in elemss:
            e = {
                'key': elem.key,
                'value': elem.value
            }
            results.append(e)
        return results


if __name__ == '__main__':
    s = PostgresStore({})
    s.create('1', {1: 3})
    s.create('2', {'hello': 'world'})
    s.create('3', {'hello': {1: 'world', 2: '世界'}})
    s.create('4', {'t': ["你好", "世界", "测试"]})
    s.create('5', {'t': ["世界", "你好", "改动"]})
    s.create('6', {'t': ["刺激", "1995", "改动一下"]})
    s.create('7', {'t': ["明天", "幸福"]})
    s.create('8', {'t2': ["明天", "幸福"]})
    s.create('9', {'t3': ["明天", "幸福"]})
    # r = s.query('hello')
    r = s.query_in({'t': ["世界", "1995"]})
    print(r)
    r = s.query_in({'t': ["幸福"]})
    print(r)
    # r = s.query({'hello': 'world'})
    # print(r)
    # r = s.query({'hello':{1:'world', 2: '世界'}})
    # print(r)
    # s.delete('1')
    # with open('test.txt', 'r') as f:
    #     content = f.read()
    # r = s.create('hello.txt', 'test.txt', mode='file')
    # print(s.read(r))
