from copy import copy
from datetime import datetime

from pony.orm import Database, Required, Json, db_session, select, commit
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

        table = data.get("table", "Store")
        if table[0].islower():
            table = table[0].upper() + table[1:]

        self.Store = type(table, (self.db.Entity,), body)
        self.db.generate_mapping(create_tables=True, check_tables=True)
        self.ids = set()

    @db_session
    def create(self, key, value):
        elem = select(e for e in self.Store if e.key == key).first()
        if elem is None:
            self.Store(key=key, value=value)
            self.ids.add(key)
        else:
            elem.value = value
            elem.update_at = datetime.utcnow()

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
    def update(self, key, value):
        elem = select(e for e in self.Store if e.key == key).first()
        if elem is None:
            return
        else:
            value_db = copy(elem.value)
            if isinstance(value_db, dict) and isinstance(value, dict):
                value_db.update(value)
                elem.value = value_db
                elem.update_at = datetime.utcnow()
            elif isinstance(value_db, list) and isinstance(value, list):
                vv = [v for v in value if v not in value_db]
                value_db.extend(vv)
                elem.value = value_db
                elem.update_at = datetime.utcnow()

    @db_session
    def delete(self, key):
        elem = select(e for e in self.Store if e.key == key).first()
        if elem:
            db_delete(e for e in self.Store if e.key == key)
            if key in self.ids:
                self.ids.remove(key)

    @db_session
    def add(self, key, value):
        # value must be a list
        elem = select(e for e in self.Store if e.key == key).first()
        if elem:
            value_db = copy(elem.value)
            if isinstance(value_db, list):
                if isinstance(value, str):
                    vs = [value] if value not in value_db else []
                else:
                    vs = [v for v in value if v not in value_db]
                value_db.extend(vs)
                elem.value = value_db
                elem.update_at = datetime.utcnow()
                commit()
            if key not in self.ids:
                self.ids.add(key)
        else:
            if isinstance(value, str):
                self.Store(key=key, value=[value])
            else:
                self.Store(key=key, value=value)
            if key not in self.ids:
                self.ids.add(key)
        elem = select(e for e in self.Store if e.key == key).first()
        return {
            'key': elem.key,
            'value': elem.value
        }

    @db_session
    def remove(self, key, value):
        # value must be a list
        elem = select(e for e in self.Store if e.key == key).first()
        if elem:
            value_db = copy(elem.value)
            if isinstance(value_db, list):
                if isinstance(value, str):
                    vs = [value] if value in value_db else []
                else:
                    vs = [v for v in value if v in value_db]
                for vv in vs:
                    value_db.remove(vv)
                elem.value = value_db
                elem.update_at = datetime.utcnow()
                commit()
        elem = select(e for e in self.Store if e.key == key).first()
        return {
            'key': elem.key,
            'value': elem.value
        }

    @db_session
    def query(self, value):
        # value must be a list
        if isinstance(value, str):
            value = [value]
        elemss = []
        for i, v in enumerate(value):
            elems = select(e for e in self.Store if v in e.value)[:]
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
    def queryd(self, value):
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

    @db_session
    def reads(self, keys):
        results = []
        for key in keys:
            elem = select(e for e in self.Store if e.key == key).first()
            if elem:
                results.append({
                    'key': elem.key,
                    'value': elem.value,
                })
        return results

    @db_session
    def read_prefix(self, key, pagenum=1, pagesize=20):
        elems = select(e for e in self.Store if e.key.startswith(key)).page(pagenum=pagenum, pagesize=pagesize)
        results =[]
        for elem in elems:
            results.append({
                'key': elem.key,
                'value': elem.value,
            })
        return results

    @db_session
    def read_suffix(self, key, pagenum=1, pagesize=20):
        elems = select(e for e in self.Store if e.key.endswith(key)).page(pagenum=pagenum, pagesize=pagesize)
        results =[]
        for elem in elems:
            results.append({
                'key': elem.key,
                'value': elem.value,
            })
        return results

    @db_session
    def read_in(self, key, pagenum=1, pagesize=20):
        elems = select(e for e in self.Store if key in e.key).page(pagenum=pagenum, pagesize=pagesize)
        results =[]
        for elem in elems:
            results.append({
                'key': elem.key,
                'value': elem.value,
            })
        return results




if __name__ == '__main__':
    s = PostgresStore({"table": "hello_world"})
    s.create('1', {1: 3})
    s.create('2', {'hello': 'world'})
    s.create('3', {'hello': {1: 'world', 2: '世界'}})
    s.create('4', {'t': ["你好", "世界", "测试"]})
    s.create('5', {'t': ["世界", "你好", "改动"]})
    s.create('6', {'t': ["刺激", "1995", "改动一下"]})
    s.create('7', {'t': ["明天", "幸福"]})
    s.create('8', {'t2': ["明天", "幸福"]})
    s.create('9', {'t3': ["明天", "幸福"]})
    s.create('10', {'测试': ["明天", "幸福"]})
    s.create('11', ['测试'])
    # r = s.query('hello')
    r = s.queryd({'t': ["世界", "1995"]})
    print(r)
    r = s.queryd({'t': ["幸福"]})
    print(r)
    r = s.query(["测试"])
    r = s.query("测试")
    print(r)
    print('.' * 80)
    s.add('12', "t1")
    s.add('12', ["t1"])
    s.add('12', ["t1", "t2", "t3", "t4"])
    s.remove('12', "t1")
    s.remove('12', ["t2", "t4"])
    print('.' * 80)
    s.create('http://127.0.0.1', ['测试'])
    s.create('https://127.0.0.1', ['测试'])
    r = s.read_prefix('https')
    print(r)
    r = s.read_in('')
    print(r)
    r = s.reads(['1', '2'])
    print(r)
    # r = s.query('hello')

    # r = s.query({'hello': 'world'})
    # print(r)
    # r = s.query({'hello':{1:'world', 2: '世界'}})
    # print(r)
    # s.delete('1')
    # with open('test.txt', 'r') as f:
    #     content = f.read()
    # r = s.create('hello.txt', 'test.txt', mode='file')
    # print(s.read(r))
