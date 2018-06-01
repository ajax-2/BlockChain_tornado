import hashlib


class Account(object):

    def __init__(self, name, signature, timestamp, data):
        self.name = name
        self.signature = signature
        self.timestamp = timestamp
        self.data = data
        self.balance = 0
        self.hash = None

    def user_hash(self):
        sha = hashlib.sha256()
        sha.update((str(self.name) +
                    str(self.signature) +
                    str(self.timestamp) +
                    str(self.data) +
                    str(self.balance)
                    ).encode())
        return sha.hexdigest()

