import etcd3
import pytest

from store.etcd import ETCDStore
from store.manager import Manager
from unittest.mock import patch, MagicMock


@pytest.fixture
def m():
    m = Manager('etcd', data={})
    yield m
    m.delete('/test', prefix=True)


def test_create_should_have_expected_after_create_when_empty(m):
    with patch.object(ETCDStore, 'read', return_value=(None, None)) as mock_read:
        with patch.object(ETCDStore, 'update', return_value=('expected', None)) as mock_update:
            r = m.create('/test/1', 'xxxx_i_dont_care')
            assert r[0] == 'expected'


def test_create_should_return_existed_after_create_when_already_exsited(m):
    with patch.object(ETCDStore, 'read', return_value=('expected', None)) as mock_read:
        r = m.create('/test/1', 'xxxx_i_dont_care')
        assert r[0] == 'expected'


def test_read_should_return_expected_when_prefix_is_true(m):
    with patch.object(etcd3.Etcd3Client, 'get_prefix', return_value='expected') as mock_get_prefix:
        r = m.read('/test/1', True)

        assert r == 'expected'


def test_read_should_return_expected_when_prefix_is_false(m):
    with patch.object(etcd3.Etcd3Client, 'get', return_value='expected') as mock_get:
        r = m.read('/test/1', False)
        assert r == 'expected'


def test_update_should_called_put_and_read_once(m):
    with patch.object(etcd3.Etcd3Client, 'get', return_value='expected') as mock_get:
        with patch.object(etcd3.Etcd3Client, 'get_prefix', return_value='expected') as mock_get_prefix:
            with patch.object(etcd3.Etcd3Client, 'put', return_value='expected') as mock_put:
                r = m.update('/test/1', 'hello')
                mock_put.assert_called_with('/test/1', 'hello', None)
                mock_get.assert_called_with('/test/1')

