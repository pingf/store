import pytest

from store.etcd import ETCDStore
from store.manager import Manager
from unittest.mock import patch


@pytest.fixture
def m():
    m = Manager('etcd', data={})
    yield m
    m.delete('/test', prefix=True)


def test_create_should_existed_as_epected_when_empty(m):
    r = m.create('/test/1', 'expected')
    assert r[0] == b'expected'


def test_create_should_return_existed_as_epected_when_already_existed(m):
    r = m.create('/test/1', 'expected')
    assert r[0] == b'expected'
    r = m.create('/test/1', 'expected2')
    assert r[0] == b'expected'


def test_read_should_return_existed_as_epected_when_existed(m):
    r = m.create('/test/1', 'expected')
    r = m.read('/test/1')
    assert r[0] == b'expected'

def test_update_should_update_to_new(m):
    r = m.create('/test/1', 'old')
    r = m.update('/test/1', 'new')
    assert r[0] == b'new'
