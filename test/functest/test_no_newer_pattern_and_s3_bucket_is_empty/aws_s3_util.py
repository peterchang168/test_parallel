import new_domain_service_util
import new_domain_service_common
from botocore.client import Config
from botocore.session import Session
import boto3
import sys
import os
import time
import subprocess

class AWSError(Exception): pass
class AWS_S3Error(AWSError): pass
class AWS_S3COPYError(AWS_S3Error): pass
class AWS_S3DELETEError(AWS_S3Error): pass

GENKEY_AES64  = 0
GENKEY_AES128 = 1
GENKEY_AES256 = 2

AES64_BLOCK_SIZE  = 8
AES128_BLOCK_SIZE = 16
AES256_BLOCK_SIZE = 32

def genkey(aes_type):
    if aes_type == GENKEY_AES64 :
        block_size = AES64_BLOCK_SIZE
    elif aes_type == GENKEY_AES128 :
        block_size = AES128_BLOCK_SIZE
    else :
        block_size = AES256_BLOCK_SIZE
    customer_key= os.urandom(block_size)
    return customer_key


class S3Handler(object):
    def __init__(self, proxy=None, proxy_port = None, connect_timeout= 30 , read_timeout= 60):
        if proxy and proxy_port:
            os.environ['HTTP_PROXY'] = 'http://%s:%d' %(proxy, proxy_port)
            os.environ['HTTPS_PROXY'] = 'http://%s:%d' %(proxy, proxy_port)
        config = Config(connect_timeout= connect_timeout , read_timeout= read_timeout, region_name = 'us-west-2')
        session = Session()
        #session.set_debug_logger()
        #self.conn = boto3.client('s3' , config = config )

    def check_resp_has_lost_structure(self, resp, check_structure):
        lost_structure = {}
        has_lost = False
        if not type(resp) == dict :
            return (True, check_structure)
        for key in check_structure.keys():
            if key in resp:
                if type(resp[key]) == dict and type(check_structure[key]) == dict :
                    (child_has_lost, child_lost_struct) = self.check_resp_has_lost_structure(resp[key], check_structure[key])
                    if child_has_lost:
                        lost_structure[key] = child_lost_struct
                        has_lost = True
        return (has_lost, lost_structure)                     

    def cp_local_file_to_s3(self, bucket_name, src_path, dst_key , customer_sse_key=None , encrypt_algm='AES256', kwargs={}):
        if not os.path.exists(bucket_name):
            os.mkdir(bucket_name)
        tokens = dst_key.split('/')
        dst_path = bucket_name
        if len(tokens) >1:
            dir_tokens = tokens[:-1]
            for token in dir_tokens:
                dst_path= os.path.join(dst_path, token)
                if not os.path.exists(dst_path):
                    os.mkdir(dst_path)
        filename = tokens[-1]
        dst_path = os.path.join(dst_path, filename) 
        subprocess.Popen("cp -f %s %s" % (src_path, dst_path) , shell = True).wait()
        

    def cp_s3_file_to_local(self, bucket_name, src_path, dst_key , customer_sse_key=None , encrypt_algm='AES256', kwargs={}):
        pass

    def list_bucket_content(self, bucket_name, prefix = None, kwargs = {}):
        file_list = []
        return file_list

    def cp_s3_file_to_s3(self, bucket_name, src_path, dst_key , customer_sse_key=None , encrypt_algm='AES256', kwargs={}):
        pass

    def del_s3_file(self, bucket_name, dst_key, kwargs = {}):
        pass
