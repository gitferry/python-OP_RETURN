import json, datetime
from tabnanny import check
from time import sleep
from blockcypher import get_transaction_details
from blockcypher import get_block_overview
import statistics

def main():
    measurement_file = "measurements.json"
    fastConfirm=[]
    fastSixDeep=[]
    fastTwentyDeep=[]
    slowConfirm=[]
    slowSixDeep=[]
    slowTwentyDeep=[]
    with open(measurement_file, "r+") as meaFile:
        data = json.load(meaFile)
        checkpoints=data['checkpoints']
        for i in range(len(checkpoints)):
            fastfee=checkpoints[i]['fastfee']
            fastConfirm.append(fastfee['confirm_duration'])
            fastSixDeep.append(fastfee['six_deep_duration'])
            fastTwentyDeep.append(fastfee['twenty_deep_duration'])

            slowfee=checkpoints[i]['slowfee']
            slowConfirm.append(slowfee['confirm_duration'])
            slowSixDeep.append(slowfee['six_deep_duration'])
            slowTwentyDeep.append(slowfee['twenty_deep_duration'])
        meaFile.close()
    
    print("High fee:")
    print("Mean of confirmation time: % s " % (statistics.mean(fastConfirm))) 
    print("Standard Deviation of confirmation time: % s "% (statistics.stdev(fastConfirm)))
    print("Mean of 6 deap time: % s " % (statistics.mean(fastSixDeep))) 
    print("Standard Deviation of 6 deep time: % s "% (statistics.stdev(fastSixDeep)))
    print("Mean of 20 deap time: % s " % (statistics.mean(fastTwentyDeep))) 
    print("Standard Deviation of 20 deep time: % s "% (statistics.stdev(fastTwentyDeep)))

    print("Low fee:")
    print("Mean of confirmation time: % s " % (statistics.mean(slowConfirm))) 
    print("Standard Deviation of confirmation time: % s "% (statistics.stdev(slowConfirm)))
    print("Mean of 6 deap time: % s " % (statistics.mean(slowSixDeep))) 
    print("Standard Deviation of 6 deep time: % s "% (statistics.stdev(slowSixDeep)))
    print("Mean of 20 deap time: % s " % (statistics.mean(slowTwentyDeep))) 
    print("Standard Deviation of 20 deep time: % s "% (statistics.stdev(slowTwentyDeep)))

if __name__ == "__main__":
	main()