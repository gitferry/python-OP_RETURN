# send-OP_RETURN.py
# 
# CLI wrapper for OP_RETURN.py to send bitcoin with OP_RETURN metadata
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


import sys, string, os, json, configparser, random
from typing import Dict
from OP_RETURN import *
from datetime import datetime, timezone, date
from json import JSONEncoder

NETWORK = 'test'
testnet=False

def main():
	configParser = configparser.RawConfigParser()  
	configFilePath = r'config.txt'
	configParser.read(configFilePath)

	send_address = configParser[NETWORK]['send_address']
	send_amount = configParser[NETWORK]['send_amount']
	op1_bytes = str.encode('BBNT') + os.urandom(int(configParser[NETWORK]['op1_len']))
	op2_bytes = str.encode('BBNT') + os.urandom(int(configParser[NETWORK]['op2_len']))
	op_return_1 = OP_RETURN_hex_to_bin(op1_bytes.hex())
	op_return_2 = OP_RETURN_hex_to_bin(op2_bytes.hex())
	fastfee = configParser[NETWORK]['fastfee']
	slowfee = configParser[NETWORK]['slowfee']
	interval = configParser[NETWORK]['interval']
	exp_n = configParser[NETWORK]['exp_n']

	filename = newResultFile()

	for i in range(int(exp_n)):
		print("Sending checkpoint " + str(i+1) + " with fastfee:")
		fasttx1=OP_RETURN_send(send_address, float(send_amount), op_return_1, float(fastfee), testnet)
		if 'error' in fasttx1:
			print('Error: '+fasttx1['error'])
			return

		fasttx2=OP_RETURN_send(send_address, float(send_amount), op_return_2, float(fastfee), testnet)
		if 'error' in fasttx2:
			print('Error: '+fasttx2['error'])
			return

		print("Sending checkpoint " + str(i+1) + " with slowfee:")
		slowtx1=OP_RETURN_send(send_address, float(send_amount), op_return_1, float(slowfee), testnet)
		if 'error' in slowtx1:
			print('Error: '+slowtx1['error'])
			return

		slowtx2=OP_RETURN_send(send_address, float(send_amount), op_return_2, float(slowfee), testnet)
		if 'error' in slowtx2:
			print('Error: '+slowtx2['error'])
			return

		printAndRecordRes(filename, i+1, fasttx1, fasttx2, slowtx1, slowtx2)
		print("Countdown to send the next checkpoint:")
		for i in range(int(interval),0,-1):
			print(f"{i}", end="\r", flush=True)
			time.sleep(1)

def newResultFile():
	date_time = datetime.now().strftime("%H:%M:%S")
	filename = "test_result_"+date_time+".json"
	with open(filename, "w+") as resFile:
		res = {
			"checkpoints": [

			],
		}
		json.dump(res, resFile, indent=4)
		resFile.close()
	return filename
	

def printAndRecordRes(filename, index, fasttx1, fasttx2, slowtx1, slowtx2):
	printRes(fasttx1)
	printRes(fasttx2)
	printRes(slowtx1)
	printRes(slowtx2)

	with open(filename, "r+") as resFile:
		result = json.load(resFile)
		ts = datetime.now()
		ts = ts.replace(tzinfo=timezone.utc)
		new_ckpt = {
			'time': ts,
			'fastfee': {
				'tx1': fasttx1,
				'tx2': fasttx2,
			},
			'slowfee': {
				'tx1': slowtx1,
				'tx2': slowtx2,
			}
		}
		result['checkpoints'].append(new_ckpt)
		resFile.seek(0)
		json.dump(result, resFile, indent=4, cls=DateTimeEncoder)
		resFile.close()

def printRes(res):
	timestamp = datetime.now().strftime("%H:%M:%S")
	print('TxID: '+res+'\nSent Time: '+ timestamp + '\nSuccess!')

def get_random_string(length):
    # choose from all lowercase letter
	letters = string.ascii_lowercase
	result_str = ''.join(random.choice(letters) for i in range(length))
	return result_str

# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()

if __name__ == "__main__":
	main()
