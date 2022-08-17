# OP_RETURN.py
#
# Python script to generate and retrieve OP_RETURN bitcoin transactions
#
# Copyright (c) Coin Sciences Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from curses import meta
import subprocess, json, time, random, os.path, binascii, struct, string, re, hashlib
from pprint import pprint


# Python 2-3 compatibility logic

try:
	basestring
except NameError:
	basestring = str
	
  
# User-defined quasi-constants

OP_RETURN_BITCOIN_IP='127.0.0.1' # IP address of your bitcoin node
OP_RETURN_BITCOIN_USE_CMD=True # use command-line instead of JSON-RPC?

if OP_RETURN_BITCOIN_USE_CMD:
	OP_RETURN_BITCOIN_PATH='/opt/homebrew/bin/bitcoin-cli' # path to bitcoin-cli executable on this server
	
else:
	OP_RETURN_BITCOIN_PORT='' # leave empty to use default port for mainnet/testnet
	OP_RETURN_BITCOIN_USER='bbn' # leave empty to read from ~/.bitcoin/bitcoin.conf (Unix only)
	OP_RETURN_BITCOIN_PASSWORD='bbnmaster' # leave empty to read from ~/.bitcoin/bitcoin.conf (Unix only)
	
OP_RETURN_BTC_FEE=0.0001 # BTC fee to pay per transaction
OP_RETURN_BTC_DUST=0.00001 # omit BTC outputs smaller than this

OP_RETURN_MAX_BYTES=80 # maximum bytes in an OP_RETURN (80 as of Bitcoin 0.11)
OP_RETURN_MAX_BLOCKS=10 # maximum number of blocks to try when retrieving data

OP_RETURN_NET_TIMEOUT=10 # how long to time out (in seconds) when communicating with bitcoin node


# User-facing functions

def OP_RETURN_send(send_address, send_amount, metadata, fee=0.0001, testnet=True):
	# Validate some parameters
	
	if not OP_RETURN_bitcoin_check(testnet):
		return {'error': 'Please check Bitcoin Core is running and OP_RETURN_BITCOIN_* constants are set correctly'}

	result=OP_RETURN_bitcoin_cmd('validateaddress', testnet, send_address)
	if not ('isvalid' in result and result['isvalid']):
		return {'error': 'Send address could not be validated: '+send_address}
	
	if isinstance(metadata, basestring):
		metadata=metadata.encode('utf-8') # convert to binary string

	metadata_len=len(metadata)
		
	if metadata_len>65536:
		return {'error': 'This library only supports metadata up to 65536 bytes in size'}
		
	if metadata_len>OP_RETURN_MAX_BYTES:
		return {'error': 'Metadata has '+str(metadata_len)+' bytes but is limited to '+str(OP_RETURN_MAX_BYTES)+' (see OP_RETURN_MAX_BYTES)'}
	
	raw_txn=OP_RETURN_create_data_transaction(fee, metadata, testnet)

	return OP_RETURN_sign_send_txn(raw_txn, testnet)

def OP_RETURN_create_data_transaction(fee, metadata, testnet):
	# List and sort unspent inputs by amount in descending order

	unspent_inputs=OP_RETURN_bitcoin_cmd('listunspent', testnet, 0)		
	if not isinstance(unspent_inputs, list):
		return {'error': 'Could not retrieve list of unspent inputs'}
		
	unspent_inputs.sort(key=lambda unspent_input: unspent_input['amount'], reverse=True)
	
	inputs = []
	inputs.append(unspent_inputs[0])

	change_address=OP_RETURN_bitcoin_cmd('getrawchangeaddress', testnet)
	result = float(unspent_inputs[0]['amount']) - fee
	
	outputs= {
		change_address: float('%.4f' % result),
		"data": OP_RETURN_bin_to_hex(metadata),
	}

	return OP_RETURN_bitcoin_cmd('createrawtransaction', testnet, inputs, outputs)

def OP_RETURN_sign_send_txn(raw_txn, testnet):
	signed_txn=OP_RETURN_bitcoin_cmd('signrawtransactionwithwallet', testnet, raw_txn)
	if not ('complete' in signed_txn and signed_txn['complete']):
		return {'error': 'Could not sign the transaction'}
	
	send_txid=OP_RETURN_bitcoin_cmd('sendrawtransaction', testnet, signed_txn['hex'])
	if not (isinstance(send_txid, basestring) and len(send_txid)==64):
		return {'error': 'Could not send the transaction'}
	
	return str(send_txid)

# Talking to bitcoin-cli

def OP_RETURN_bitcoin_check(testnet):
	info=OP_RETURN_bitcoin_cmd('getwalletinfo', testnet)
	
	return isinstance(info, dict) and 'balance' in info


def OP_RETURN_bitcoin_cmd(command, testnet, *args): # more params are read from here
	if OP_RETURN_BITCOIN_USE_CMD:
		sub_args=[OP_RETURN_BITCOIN_PATH]
		if testnet:
			sub_args.append('-testnet')
		
		sub_args.append(command)
		
		for arg in args:
			sub_args.append(json.dumps(arg) if isinstance(arg, (dict, list, tuple)) else str(arg))
		
		raw_result=subprocess.check_output(sub_args).decode("utf-8").rstrip("\n")
		
		try: # decode JSON if possible
			result=json.loads(raw_result)
		except ValueError:
			result=raw_result

	else:
		request={
			'id': str(time.time())+'-'+str(random.randint(100000,999999)),
			'method': command,
			'params': args,
		}
		
		port=OP_RETURN_BITCOIN_PORT
		user=OP_RETURN_BITCOIN_USER
		password=OP_RETURN_BITCOIN_PASSWORD
		
		if not (len(port) and len(user) and len(password)):
			conf_lines=open(os.path.expanduser('~')+'/Library/Application Support/Bitcoin/bitcoin.conf').readlines()
			
			for conf_line in conf_lines:
				parts=conf_line.strip().split('=', 1) # up to 2 parts
				
				if (parts[0]=='rpcport') and not len(port):
					port=int(parts[1])
				if (parts[0]=='rpcuser') and not len(user):
					user=parts[1]
				if (parts[0]=='rpcpassword') and not len(password):
					password=parts[1]
		
		if not len(port):
			port=18332 if testnet else 8332
			
		if not (len(user) and len(password)):
			return None # no point trying in this case
		
		url='http://'+OP_RETURN_BITCOIN_IP+':'+str(port)+'/'
		
		try:
			from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, build_opener, install_opener, urlopen
		except ImportError:
			from urllib.request import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, build_opener, install_opener, urlopen

		passman=HTTPPasswordMgrWithDefaultRealm()
		passman.add_password(None, url, user, password)
		auth_handler=HTTPBasicAuthHandler(passman)
		opener=build_opener(auth_handler)
		install_opener(opener)
		print(request)
		raw_result=urlopen(url, json.dumps(request).encode('utf-8'), OP_RETURN_NET_TIMEOUT).read()
		
		result_array=json.loads(raw_result.decode('utf-8'))
		result=result_array['result']

	return result

def OP_RETURN_get_ref_parts(ref):
	if not re.search('^[0-9]+\-[0-9A-Fa-f]+$', ref): # also support partial txid for second half
		return None
	
	parts=ref.split('-')
		
	if re.search('[A-Fa-f]', parts[1]):
		if len(parts[1])>=4:
			txid_binary=OP_RETURN_hex_to_bin(parts[1][0:4])
			parts[1]=ord(txid_binary[0:1])+256*ord(txid_binary[1:2])+65536*0
		else:
			return None
			
	parts=list(map(int, parts))
	
	if parts[1]>983039: # 14*65536+65535
		return None
		
	return parts


def OP_RETURN_get_ref_heights(ref, max_height):
	parts=OP_RETURN_get_ref_parts(ref)
	if not parts:
		return None
		
	return OP_RETURN_get_try_heights(parts[0], max_height, True)


def OP_RETURN_get_try_heights(est_height, max_height, also_back):
	forward_height=est_height
	back_height=min(forward_height-1, max_height)
	
	heights=[]
	mempool=False
	try_height=0
	
	while True:
		if also_back and ((try_height%3)==2): # step back every 3 tries
			heights.append(back_height)
			back_height-=1

		else:
			if forward_height>max_height:
				if not mempool:
					heights.append(0) # indicates to try mempool
					mempool=True
				
				elif not also_back:
					break # nothing more to do here
			
			else:
				heights.append(forward_height)
			
			forward_height+=1
	
		if len(heights)>=OP_RETURN_MAX_BLOCKS:
			break
			
		try_height+=1
	
	return heights


def OP_RETURN_match_ref_txid(ref, txid):
	parts=OP_RETURN_get_ref_parts(ref)
	if not parts:
		return None

	txid_offset=int(parts[1]/65536)
	txid_binary=OP_RETURN_hex_to_bin(txid)

	txid_part=txid_binary[2*txid_offset:2*txid_offset+2]
	txid_match=bytearray([parts[1]%256, int((parts[1]%65536)/256)])

	return txid_part==txid_match # exact binary comparison


# Unpacking and packing bitcoin blocks and transactions	

def OP_RETURN_unpack_block(binary):
	buffer=OP_RETURN_buffer(binary)
	block={}
	
	block['version']=buffer.shift_unpack(4, '<L')
	block['hashPrevBlock']=OP_RETURN_bin_to_hex(buffer.shift(32)[::-1])
	block['hashMerkleRoot']=OP_RETURN_bin_to_hex(buffer.shift(32)[::-1])
	block['time']=buffer.shift_unpack(4, '<L')
	block['bits']=buffer.shift_unpack(4, '<L')
	block['nonce']=buffer.shift_unpack(4, '<L')
	block['tx_count']=buffer.shift_varint()
	
	block['txs']={}
	
	old_ptr=buffer.used()
	
	while buffer.remaining():
		transaction=OP_RETURN_unpack_txn_buffer(buffer)
		new_ptr=buffer.used()
		size=new_ptr-old_ptr
		
		raw_txn_binary=binary[old_ptr:old_ptr+size]
		txid=OP_RETURN_bin_to_hex(hashlib.sha256(hashlib.sha256(raw_txn_binary).digest()).digest()[::-1])
		
		old_ptr=new_ptr
	
		transaction['size']=size
		block['txs'][txid]=transaction
	
	return block


def OP_RETURN_unpack_txn(binary):
	return OP_RETURN_unpack_txn_buffer(OP_RETURN_buffer(binary))


def OP_RETURN_unpack_txn_buffer(buffer):
	# see: https://en.bitcoin.it/wiki/Transactions
	
	txn={
		'vin': [],
		'vout': [],
	}
	
	txn['version']=buffer.shift_unpack(4, '<L') # small-endian 32-bits
	
	inputs=buffer.shift_varint()
	if inputs>100000: # sanity check
		return None
	
	for _ in range(inputs):
		input={}
		
		input['txid']=OP_RETURN_bin_to_hex(buffer.shift(32)[::-1])
		input['vout']=buffer.shift_unpack(4, '<L')
		length=buffer.shift_varint()
		input['scriptSig']=OP_RETURN_bin_to_hex(buffer.shift(length))
		input['sequence']=buffer.shift_unpack(4, '<L')
		
		txn['vin'].append(input)
		
	outputs=buffer.shift_varint()
	if outputs>100000: # sanity check
		return None
		
	for _ in range(outputs):
		output={}
		
		output['value']=float(buffer.shift_uint64())/100000000
		length=buffer.shift_varint()
		output['scriptPubKey']=OP_RETURN_bin_to_hex(buffer.shift(length))
		
		txn['vout'].append(output)
	
	txn['locktime']=buffer.shift_unpack(4, '<L')
	
	return txn


def OP_RETURN_find_spent_txid(txns, spent_txid, spent_vout):
	for txid, txn_unpacked in txns.items():
		for input in txn_unpacked['vin']:
			if (input['txid']==spent_txid) and (input['vout']==spent_vout):
				return txid
				
	return None


def OP_RETURN_find_txn_data(txn_unpacked):
	for index, output in enumerate(txn_unpacked['vout']):
		op_return=OP_RETURN_get_script_data(OP_RETURN_hex_to_bin(output['scriptPubKey']))
		
		if op_return:
			return {
				'index': index,
				'op_return': op_return,
			}
	
	return None
	

def OP_RETURN_get_script_data(scriptPubKeyBinary):
	op_return=None
	
	if scriptPubKeyBinary[0:1]==b'\x6a':
		first_ord=ord(scriptPubKeyBinary[1:2])
		
		if first_ord<=75:
			op_return=scriptPubKeyBinary[2:2+first_ord]
		elif first_ord==0x4c:
			op_return=scriptPubKeyBinary[3:3+ord(scriptPubKeyBinary[2:3])]
		elif first_ord==0x4d:
			op_return=scriptPubKeyBinary[4:4+ord(scriptPubKeyBinary[2:3])+256*ord(scriptPubKeyBinary[3:4])]
	
	return op_return	


def OP_RETURN_pack_txn(txn):
	binary=b''
	
	binary+=struct.pack('<L', txn['version'])
	
	binary+=OP_RETURN_pack_varint(len(txn['vin']))
	
	for input in txn['vin']:
		binary+=OP_RETURN_hex_to_bin(input['txid'])[::-1]
		binary+=struct.pack('<L', input['vout'])
		binary+=OP_RETURN_pack_varint(int(len(input['scriptSig'])/2)) # divide by 2 because it is currently in hex
		binary+=OP_RETURN_hex_to_bin(input['scriptSig'])
		binary+=struct.pack('<L', input['sequence'])
	
	binary+=OP_RETURN_pack_varint(len(txn['vout']))
	
	for output in txn['vout']:
		binary+=OP_RETURN_pack_uint64(int(round(output['value']*100000000)))
		binary+=OP_RETURN_pack_varint(int(len(output['scriptPubKey'])/2)) # divide by 2 because it is currently in hex
		binary+=OP_RETURN_hex_to_bin(output['scriptPubKey'])
	
	binary+=struct.pack('<L', txn['locktime'])
	
	return binary


def OP_RETURN_pack_varint(integer):
	if integer>0xFFFFFFFF:
		packed="\xFF"+OP_RETURN_pack_uint64(integer)
	elif integer>0xFFFF:
		packed="\xFE"+struct.pack('<L', integer)
	elif integer>0xFC:
		packed="\xFD".struct.pack('<H', integer)
	else:
		packed=struct.pack('B', integer)
	
	return packed


def OP_RETURN_pack_uint64(integer):
	upper=int(integer/4294967296)
	lower=integer-upper*4294967296
	
	return struct.pack('<L', lower)+struct.pack('<L', upper)


# Helper class for unpacking bitcoin binary data

class OP_RETURN_buffer():

	def __init__(self, data, ptr=0):
		self.data=data
		self.len=len(data)
		self.ptr=ptr
	 
	def shift(self, chars):
		prefix=self.data[self.ptr:self.ptr+chars]
		self.ptr+=chars

		return prefix
	 
	def shift_unpack(self, chars, format):
		unpack=struct.unpack(format, self.shift(chars))

		return unpack[0]

	def shift_varint(self):
		value=self.shift_unpack(1, 'B')

		if value==0xFF:
			value=self.shift_uint64()
		elif value==0xFE:
			value=self.shift_unpack(4, '<L')
		elif value==0xFD:
			value=self.shift_unpack(2, '<H')
	
		return value

	def shift_uint64(self):
		return self.shift_unpack(4, '<L')+4294967296*self.shift_unpack(4, '<L')
	
	def used(self):
		return min(self.ptr, self.len)

	def remaining(self):
		return max(self.len-self.ptr, 0)


# Converting binary <-> hexadecimal

def OP_RETURN_hex_to_bin(hex):
	try:
		raw=binascii.a2b_hex(hex)
	except Exception as err:
		print("failed to convert hex to binary: {0}".format(err))
		return None
		
	return raw
	

def OP_RETURN_bin_to_hex(string):
	return binascii.b2a_hex(string).decode('utf-8')
