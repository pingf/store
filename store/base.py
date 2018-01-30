from functools import wraps


class StoreError(Exception):
    '''
    store error
    '''
    pass


def transform_key(func):
    @wraps(func)
    def func_wrapper(self, key, *args, **kwargs):
        # pylint: disable=protected-access
        return func(self, self._transform_key(key), *args, **kwargs)

    return func_wrapper


class BaseStore:
    '''
    base store
    '''

    def create(self, key, value):
        # pylint: disable=unused-argument,no-self-use
        raise StoreError('create not implemented!')

    def read(self, key):
        # pylint: disable=unused-argument,no-self-use
        raise StoreError('read not implemented!')

    def update(self, key, value):
        # pylint: disable=unused-argument,no-self-use
        raise StoreError('update not implemented!')

    def delete(self, key):
        # pylint: disable=unused-argument,no-self-use
        raise StoreError('update not implemented!')

    def _transform_key(self, key):
        # pylint: disable=no-self-use
        return key

    @transform_key
    def __getitem__(self, key):
        return self.read(key)

    @transform_key
    def __setitem__(self, key, value):
        return self.update(key, value)

    @transform_key
    def __delitem__(self, key):
        return self.delete(key)

    @transform_key
    def __contains__(self, key):
        return self.read(key) is not None

    def __iter__(self):
        raise StoreError('__iter__ not implemented!')

    def __len__(self):
        raise StoreError('__len__ not implemented!')
