from tornado import ioloop
from tornado.web import Application
from config import ip, port
from Tornado_Http.views import MainHandle, BlockHandle
from Tornado_Http.views import MinerHandle
from Tornado_Http.views import TransactionHandle
from Tornado_Http.views import NodeHandle
from Block_Chain.Chain.Utils import booting_block_chain

views_list = [
    (r'/', MainHandle),
    (r'/block/sync/prepare', BlockHandle),
    (r'/block/get', BlockHandle),
    (r'/block/add', BlockHandle),
    (r'/miner', MinerHandle),
    (r'/transaction/get', TransactionHandle),
    (r'/node/user/get', NodeHandle),
    (r'/node/request/sync/prepare', NodeHandle),
    (r'/node/response/sync/prepare', NodeHandle),
]

setting = {'debug': True}

application = Application(views_list, **setting)
application.listen(address=ip, port=port)

if __name__ == '__main__':
    booting_block_chain()
    ioloop.IOLoop.current().start()



