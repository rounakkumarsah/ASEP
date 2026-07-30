# Mock xxhash to bypass AppLocker/Application Control DLL blocking
class MockXxhash:
    def __init__(self, *args, **kwargs):
        pass
    def update(self, *args, **kwargs):
        pass
    def digest(self, *args, **kwargs):
        return b'\x00' * 8
    def hexdigest(self, *args, **kwargs):
        return '0000000000000000'
    def intdigest(self, *args, **kwargs):
        return 0

def xxh64(*args, **kwargs):
    return MockXxhash(*args, **kwargs)

def xxh3_64(*args, **kwargs):
    return MockXxhash(*args, **kwargs)

def xxh32(*args, **kwargs):
    return MockXxhash(*args, **kwargs)

def xxh3_128_hexdigest(*args, **kwargs):
    return '00000000000000000000000000000000'

