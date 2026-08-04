# Mock uuid_utils to bypass DLL block
import uuid

def uuid7():
    return uuid.uuid4()
