from tornado.web import RequestHandler
from Block_Chain.Chain import Utils
from urllib3 import PoolManager
import logging

httpRequest = PoolManager()


###
# welcome to chain block
###
class MainHandle(RequestHandler):

    def get(self, *args, **kwargs):
        self.write('Hello, welcome to here, you can distribute your suggest in your browser!!')


###
# Block Controller
###
class BlockHandle(RequestHandler):

    uri = None
    url = None

    def prepare(self):
        self.uri = self.request.uri

    def get(self, *args, **kwargs):
        if self.uri == '/block/get':
            self.write(Utils.get_have_sync_block())
        if '/block/sync/' in self.uri:
            self.sync_controller(self.uri.strip('/block/sync/'))

    def post(self, *args, **kwargs):
        if self.uri == '/block/add':
            new_block_dict = self.get_argument('new_block_dict')
            Utils.add_sync_block(new_block_dict=new_block_dict)

    @staticmethod
    def sync_controller(uri_end):
        if uri_end == 'prepare':
            Utils.RequestFlag[Utils.block_new.hash] = False
            Utils.SyncNumber[Utils.block_new.hash] = 0
            for i in Utils.node:
                httpRequest.request(method='GET', url='http://' + i.address +
                                                      '/node/request/sync?hash=' + Utils.block_new.hash)


###
# Transaction Controller
###
class TransactionHandle(RequestHandler):

    uri = None

    def prepare(self):
        uri_request = self.request.uri
        if '?' not in uri_request:
            self.uri = uri_request
        else:
            self.uri = uri_request[:uri_request.index('?')]

    def get(self, *args, **kwargs):
        print(self.uri)
        if self.uri == '/transaction/get':
            self.get_transaction()

    def post(self, *args, **kwargs):
        pass

    def get_transaction(self):
        try:
            hash_temp = self.get_argument('hash')
            self.write(Utils.get_transaction(get_hash=hash_temp, block=Utils.block_chain_have_sync))
        except Exception as e:
            print(e)
            self.write('your must offer a hash!!')


###
# Miner Controller
###
class MinerHandle(RequestHandler):

    miner_flag = None

    def prepare(self):
        try:
            self.miner_flag = self.get_argument('flag')
        except BaseException as e:
            logging.exception(e)
            self.write('your must offer parameter that name is flag')

    def get(self, *args, **kwargs):
        if self.miner_flag == 'get':
            self.write(str(Utils.ChainFlag['miner_flag']))
        elif self.miner_flag == 'start':
            Utils.ChainFlag['miner_flag'] = True
            self.write('your request is success! and %s miner' % self.miner_flag)
        elif self.miner_flag == 'stop':
            Utils.ChainFlag['miner_flag'] = False
            self.write('your request is success! and %s miner' % self.miner_flag)
        else:
            self.write('you must give a valid value to flag')


###
# Node Controller
###
class NodeHandle(RequestHandler):

    uri = None
    url = None

    def prepare(self):
        uri_request = self.request.uri
        if '?' not in uri_request:
            self.uri = uri_request
        else:
            self.uri = uri_request[:uri_request.index('?')]
        self.url = self.request.full_url()

    def get(self, *args, **kwargs):
        if '/node/user/' in self.uri:
            self.node_controller(self.uri.strip('/node/user/'))
        elif '/node/request/' in self.uri:
            self.request_controller(self.uri.strip('/node/request/'))
        elif '/node/response/' in self.uri:
            self.response_controller(self.uri.strip('/node/response/'))

    def node_controller(self, uri_end):
        if uri_end == 'get':
            self.write(Utils.get_node())

    def response_controller(self, uri_end):
        if uri_end == 'sync/pre_prepare':
            self.response_sync_pre_perpare()

    def request_controller(self, uri_end):
        if uri_end == 'sync/pre_prepare':
            self.request_sync_prepare()

    def response_sync_prepare(self):
        try:
            result = self.get_argument('result')
            hash = self.get_argument('hash')
            if result == 'permit' and hash == Utils.block_new.hash and not Utils.RequestFlag[hash]:
                Utils.SyncNumber[hash] += 1
                if Utils.SyncNumber[hash] > len(Utils.NodeNumber.keys()) / 2:
                    Utils.RequestFlag[hash] = True
                    for i in Utils.node:
                        Utils.send_message_to_all(url='http://%s/node/request/commit')
        except BaseException as e:
            self.write('your parameters ia invalid!!')
            logging.exception(e)

    def request_sync_prepare(self):
        try:
            request_hash = self.get_argument('hash')
            if not Utils.SyncNumber:
                Utils.SyncNumber.append(request_hash)
                result = 'permit'
            else:
                result = 'reject'
            for i in Utils.node:
                Utils.send_message_to_all(url='http://%s/node/response/sync?hash=%s&result=%s'
                                                            % (i.address, request_hash, result))
        except BaseException as e:
            logging.exception(e)
            self.write('your hash is invalid !!')
