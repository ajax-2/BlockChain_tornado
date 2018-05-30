from enum import Enum, unique

class A():
    @unique
    class STATUS(Enum):
        MAIN = 0
        REPLICAS = 1


a = A()
print(a.STATUS.MAIN.value)
