from urllib3 import PoolManager
import json
http = PoolManager()
http.request(method='POST', url='http://18.18.117.118:30000/block/add', fields={'new_block': '1651561'.encode()})
