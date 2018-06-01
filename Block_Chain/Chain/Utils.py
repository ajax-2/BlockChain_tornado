from Block_Chain.Define.Block import Block
from Block_Chain.Define.Transaction import Transaction
from Block_Chain.Define.Node import Node
from Block_Chain.Define.Account import Account
from datetime import datetime
from config import ip, port, transaction_limit
from hashlib import sha256
import json
import os
import time
import threading
from urllib3 import PoolManager
from DB.FileDB import insert_into_file, get_last_file
import logging
import requests
import zipfile

base_path = os.path.abspath('.')
log_path = os.path.join(base_path, 'Log')
log_file_name = 'server_error.log'

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
handle = logging.FileHandler(os.path.join(log_path, log_file_name))
handle.setLevel(level=logging.INFO)
logger.addHandler(handle)

block_chain_have_sync = []
node = []
block_new = None
transaction_not_verify_cache = []
transaction_have_verify_cache = []
httpRequest = PoolManager()
main_node = None
ChainFlag = {}
RequestNumber = {}
RequestFlag = {}
ResponseFlag = {}
ResponseNumber = {}
NodeNumber = {}
SyncNumber = []
ChainFlag.setdefault('miner_flag', False)
ChainFlag.setdefault('sync_flag', False)


###
# register node
###
def register_node(address, data):
    timestamp = datetime.datetime.now()
    node_register = Node(address, data, timestamp)
    node_register.status = node_register.STATUS.REPLICAS
    node_register.hash = node_register.node_hash()
    node.append(node_register)


###
# get node
###
def get_node():
    return json.dumps([json.dumps(obj=node_per, default=parse_node) for node_per in node])


###
# parse a node to str
###
def parse_node(node_per):
    return {
        'address': node_per.address,
        'timestamp': node_per.timestamp,
        'data': node_per.data,
        'status': node_per.status,
        'hash': node_per.hash
    }


###
# register account
###
def register_account(name, signature, data):
    account_register = Account(name, signature, str(datetime.now()), data)
    account_register.hash = account_register.user_hash()
    block_new.account[account_register.hash] = json.dumps(obj=account_register, default=parse_account)


###
# create genesis block
###
def create_genesis_block():
    index = 0
    data = 'Genesis Block: this block will confirm your data file and your parameters, ' \
           'if invalid, we will warn you and quit your running!'
    previous_hash = None
    block = Block(index, data, previous_hash)
    block.timestamp = str(datetime.now())
    block.have_sync = True
    block.hash = block.hash_block()
    block_chain_have_sync.append(block)
    parse_block_to_file(new_block=block_chain_have_sync, file_name="genesis", block_size=1)


###
# create new block and this block is not sync
###
def create_new_block():
    block_last = block_chain_have_sync[-1]
    index = block_last.index + 1
    timestamp = str(datetime.now())
    data = "this is %s block, the block is created by chain at %s" % (index, timestamp)
    previous_hash = block_last.hash
    global block_new
    block_new = Block(index, data, previous_hash)
    block_new.timestamp = timestamp


###
# submit a transaction in transaction cache
###
def prepare_transaction(data, gas_price):
    timestamp = str(datetime.now())
    transaction = Transaction(timestamp, data, gas_price)
    transaction.status = transaction.STATUS.VERIFY
    transaction_not_verify_cache.append(transaction)
    return transaction.hash


###
# parse a block and return a map
###
def parse_block(block_one):
    map_parse_block = {
            'index': block_one.index,
            'timestamp': block_one.timestamp,
            'data': block_one.data,
            'previous_hash': block_one.previous_hash,
            'transaction': block_one.transaction,
            'contract_data': json.dumps(block_one.contract_data),
            'gas_limit': block_one.gas_limit,
            'block_size': block_one.block_size,
            'have_sync': block_one.have_sync,
            'account': json.dumps(block_one.account),
            'hash': block_one.hash,
            }
    return map_parse_block


###
# parse a map and return a block
###
def load_block(block_dict):
    b = Block(None, None, None)
    b.index = block_dict['index']
    b.timestamp = block_dict['timestamp']
    b.data = block_dict['data']
    b.previous_hash = block_dict['previous_hash']
    b.gas_limit = block_dict['gas_limit']
    b.block_size = block_dict['block_size']
    b.hash = block_dict['hash']
    b.have_sync = block_dict['have_sync']
    b.contract_data = json.loads(block_dict['contract_data'])
    b.transaction = block_dict['transaction']
    b.account = json.loads(block_dict['account'])
    return b


###
# parse account to map
###
def parse_account(account_one):
    return {
        'name': account_one.name,
        'signature': account_one.signature,
        'timestamp': account_one.timestamp,
        'data': account_one.data,
        'balance': account_one.balance,
        'hash': account_one.hash,
    }


###
# load a map to account
###
def load_account(account_dict):
    account = Account(None, None, None, None)
    account.name = account_dict['name']
    account.signature = account_dict['signature']
    account.data = account_dict['data']
    account.timestamp = account_dict['timestamp']
    account.balance = account_dict['balance']
    account.hash = account_dict['hash']
    return account


###
# parse a transaction and return a map
###
def parse_transaction(tran_one):
    return {
        "timestamp": tran_one.timestamp,
        'data': tran_one.data,
        'gas_price': tran_one.gas_price,
        'status': tran_one.status,
        'hash': tran_one.hash,
    }


###
# parse a map and return a transaction
###
def load_transaction(tran_dict):
    temp = Transaction(None, None, None)
    temp.timestamp = tran_dict['timestamp']
    temp.data = tran_dict['data']
    temp.gas_price = tran_dict['gas_price']
    temp.hash = tran_dict['hash']
    temp.status = tran_dict['status']
    return temp


###
# method of calculate when worker miner
###
def proof_pow(y):
    x = 5
    while sha256(f'{x*y}'.encode()).hexdigest()[:5] != "00000":
        y += 1


###
# send message to all node in this net
###
def send_message_to_all(url=None, data_map=None, method='GET'):
    if method == 'GET':
        httpRequest.request(method='GET', url=url)
    elif method == 'POST':
        httpRequest.request(method='POST', url=url, fileds=data_map)


###
# add synchronized block in the end of block_chain
###
def add_sync_block(new_block_dict):
    new_block = json.loads(new_block_dict, object_hook=load_block(new_block_dict))
    global block_chain_have_sync
    block_chain_have_sync.extend(new_block)


###
# parse all block, and be purpose to storage or send to other node
###
def parse_all_block(block_sync_list=[]):
    return [json.dumps(obj=block_per, default=parse_block) for block_per in block_sync_list]


###
# parse dicts to block_chain
###
def load_all_block(block_list):
    return [json.loads(block_per, object_hook=load_block) for block_per in block_list]


###
# storage block_chain on disk
###
def parse_block_to_file(new_block, file_name, block_size):
    block_list_to_file = parse_all_block(block_sync_list=new_block[:block_size])
    with open(os.path.join(base_path, "temp" + os.sep + file_name), 'w') as file_dump:
        json.dump(obj=block_list_to_file, fp=file_dump)
    global block_chain_have_sync
    if block_size == 1:
        insert_into_file(name=file_name, last_block_index=block_chain_have_sync[0].index)
    else:
        insert_into_file(name=file_name, last_block_index=block_chain_have_sync[block_size - 1].index)
        block_chain_have_sync = block_chain_have_sync[block_size:]


###
# get online block
###
def get_have_sync_block():
    return json.dumps(parse_all_block(block_chain_have_sync))


###
# boot block_chain with history file.
###
def start_chain_block(file_history_name):
    # load or create genesis block and create new block
    global main_node
    main_node = Node(address=ip + ':' + str(port),
                     data='main_node,_this_is_chain_main_node,_and_not_need_you_register!!',
                     timestamp=str(datetime.now()))
    main_node.status = main_node.STATUS.REPLICAS
    main_node.hash = main_node.node_hash()
    if file_history_name:
        with open(os.path.join(os.path.abspath('.') + "/temp/", file_history_name), 'r') as file_load:
            block_load = json.load(fp=file_load)
        block_list_all = load_all_block(block_load)
        global block_chain_have_sync
        block_chain_have_sync = block_list_all[:]
        del block_load
        del block_list_all
        create_new_block()

    else:
        create_genesis_block()
        create_new_block()


###
# inspect hash is exists in block
###
def compare_hash(hash_com, block_hash):
    for i in block_hash.transaction:
        if i.hash == hash_com:
            return i
    return None


###
# get a transaction message base from hash
###
def get_transaction(get_hash, block):
    history_number = len(block) - 1
    while history_number >= 0 and not compare_hash(get_hash, block[history_number]):
        history_number -= 1
    if history_number >= 0:
        return json.dumps(obj=block[history_number], default=parse_transaction)
    if block[0].index == 0:
        return 'Error: your transaction hash is invalid!!'
    else:
        file_path = os.path.join(base_path, "temp" + os.sep + str(block[0].index - 1))
        if not os.path.exists(file_path):
            return 'Error: history data file error, maybe somebody delete it!!'
        with open(file_path, 'r') as file_load:
            block_load = json.load(fp=file_load)
        list_block = load_all_block(block_load)
        del block_load
        return get_transaction(hash=hash, block=list_block[:])


###
# miner method
###
def miner_continue():
    while True:
        if ChainFlag['miner_flag']:
            if not ChainFlag['sync_flag']:
                proof_pow(0)
                block_new.timestamp = str(datetime.now())
                size = transaction_limit
                if len(transaction_have_verify_cache) < transaction_limit:
                    size = len(transaction_have_verify_cache)
                block_new.transaction = transaction_have_verify_cache[:size]
                for i in range(size):
                    transaction_have_verify_cache.pop(0)
                print("create new block !!")
                ChainFlag['sync_flag'] = True
                if len(NodeNumber.keys()) == 0:
                    block_new.have_sync = True
                    block_new.hash = block_new.hash_block()
                    block_chain_have_sync.append(block_new)
                    create_new_block()
                    ChainFlag['sync_flag'] = False
                else:
                    httpRequest.request(method='GET', url='http://%s/block/sync/prepare' % node[0].address)
                time.sleep(.3)
            else:
                print('synchronize block, please witting litter!!')
                time.sleep(.7)
        else:
            time.sleep(10)


###
# when a node register, we will send it all block
###
def block_get_all():
    return json.dumps({
        'block_chain_have_sync': parse_all_block(block=block_chain_have_sync),
        'address': node[0].address,
    })


###
# decompress a file
###
def unzip_file(file_path):
    try:
        with zipfile.ZipFile(file_path) as zip_file:
            zip_file.extractall(path='')
    except zipfile.BadZipFile as e:
        logging.info('Zip:', e)


###
# get data file from network
###
def get_data_from_http(address):
    url = "http://" + address + "/download/history_file"
    response = requests.request("GET", url, stream=True, data=None, headers=None)
    save_path = "data.zip"
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()
    unzip_file(save_path)


###
# boot method
###
def booting_block_chain():
    filename = 'No File' or get_last_file()
    if 'No File' in filename:
        start_chain_block(file_history_name=None)
    else:
        start_chain_block(file_history_name=filename)
    threading.Thread(target=miner_continue).start()
