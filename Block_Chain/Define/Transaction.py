import hashlib
from enum import Enum, unique


class Transaction(object):
    @unique
    class STATUS(Enum):
        SUCCESS = 0
        FAIL = 1
        VERIFY = 2

    def __init__(self, index, timestamp, data, gas_price):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.gas_price = gas_price
        self.status = None
        self.hash = self.transaction_hash()

    def transaction_hash(self):
        sha = hashlib.sha256()
        sha.update((
            str(self.data) +
            str(self.timestamp) +
            str(self.gas_price) +
            str(self.status)
        ).encode())
        return sha.hexdigest()