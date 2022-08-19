import json, datetime
from time import sleep
from blockcypher import get_transaction_details
from blockcypher import get_block_overview

def main():
    txid_file = "mainnet_checkpoints.json"
    measurement_file = "measurements.json"
    with open(txid_file, "r+") as txidFile:
        txid_json = json.load(txidFile)
        checkpoints=txid_json['checkpoints']
        n = 17
        for i in range(n):
            fastfee=checkpoints[i]['fastfee']
            fasttx1=fastfee['tx1']
            fasttx1_confirm_duration, fasttx1_six_deep_duration, fasttx1_twenty_deep_duration = get_measurement(fasttx1)
            fasttx2=fastfee['tx2']
            fasttx2_confirm_duration, fasttx2_six_deep_duration, fasttx2_twenty_deep_duration = get_measurement(fasttx2)
            fastfee['confirm_duration'] = fasttx1_confirm_duration if fasttx1_confirm_duration > fasttx2_confirm_duration else fasttx2_confirm_duration
            fastfee['six_deep_duration'] = fasttx1_six_deep_duration if fasttx1_six_deep_duration > fasttx2_six_deep_duration else fasttx2_six_deep_duration
            fastfee['twenty_deep_duration'] = fasttx1_twenty_deep_duration if fasttx1_twenty_deep_duration > fasttx2_twenty_deep_duration else fasttx2_twenty_deep_duration
            print("fast checkpoint:", i+1)
            print(fastfee['confirm_duration'])
            print(fastfee['six_deep_duration'])
            print(fastfee['twenty_deep_duration'])

            slowfee=checkpoints[i]['slowfee']
            slowtx1=slowfee['tx1']
            slowtx1_confirm_duration, slowtx1_six_deep_duration, slowtx1_twenty_deep_duration = get_measurement(slowtx1)
            slowtx2=slowfee['tx2']
            slowtx2_confirm_duration, slowtx2_six_deep_duration, slowtx2_twenty_deep_duration = get_measurement(slowtx2)
            slowfee['confirm_duration'] = slowtx1_confirm_duration if slowtx1_confirm_duration > slowtx2_confirm_duration else slowtx2_confirm_duration
            slowfee['six_deep_duration'] = slowtx1_six_deep_duration if slowtx1_six_deep_duration > slowtx2_six_deep_duration else slowtx2_six_deep_duration
            slowfee['twenty_deep_duration'] = slowtx1_twenty_deep_duration if slowtx1_twenty_deep_duration > slowtx2_twenty_deep_duration else slowtx2_twenty_deep_duration
            print("slow checkpoint:", i+1)
            print(slowfee['confirm_duration'])
            print(slowfee['six_deep_duration'])
            print(slowfee['twenty_deep_duration'])

        with open(measurement_file, "w+") as meaFile:
            json.dump(txid_json, meaFile, indent=4)
            meaFile.close()
        txidFile.close()
    
def get_measurement(txid):
    tx_detail=get_transaction_details(txid)
    block_height=int(tx_detail['block_height'])
    confirm_duration=tx_detail['confirmed'].minute
    six_deep_block=get_block_overview(str(block_height+6))
    twenty_deep_block=get_block_overview(str(block_height+20))
    six_deep_duration=six_deep_block['received_time']-tx_detail['confirmed']
    twenty_deep_duration=twenty_deep_block['received_time']-tx_detail['confirmed']

    return confirm_duration, six_deep_duration.total_seconds() / 60, twenty_deep_duration.total_seconds() / 60


if __name__ == "__main__":
	main()