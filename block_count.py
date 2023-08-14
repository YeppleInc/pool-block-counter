import time
import sqlite3
import subprocess
import csv
import os
import shutil
import os.path
import sys
import json
import requests
from dotenv import load_dotenv

def get_current_epoch():
    ## A function to return the current Cardano epoch number based on Shelly Genesis info.
    ##
    ## Args: None
    ## Returns: Current epoch number as an integer

    shelleyGenesisTimestamp = 1596491091
    shelleyGenesisSlot = 4924800
    shelleyGenesisEpoch = 209
    slotsPerEpoch = 432000

    timestamp = round(time.time())
    slot = (timestamp - shelleyGenesisTimestamp) + shelleyGenesisSlot

    return shelleyGenesisEpoch + ((slot - shelleyGenesisSlot) // slotsPerEpoch)

def comparefiles(file1_path, file2_path):
    ## A function that compares two files to detect if their contents are identical or not.
    ##
    ## Args: Two complete filepaths
    ## Returns: True if the files are identical, False if they are not (or if one does not exist).

    if not os.path.exists(file2_path):
        return False

    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        for line1, line2 in zip(file1, file2):
            if line1 != line2:
                return False
        # Check if one file has more lines than the other
        if file1.readline() or file2.readline():
            return False
    return True

def extract_count(data):
    ## A function that is used to extract the number of count (of blocks) from a given SQL query
    ##
    ## Args: The "select" data from an SQL query
    ## Returns: The associated "count" of blocks from that query

    try:
        return int(str(row[0])[1:-1].split(',')[0])
    except:
        return 0

def createtemp(epoch,file):
    ## A function that creates a temp file which holds block details for a certain epoch (either current or next). 
    ## The file is then later compared to another permanent file to determine whether a block was updated.
    ##
    ## Args: An epoch number (as integer), and a filepath for the temporary file.
    ## Returns: The json data to send to API endpoint. 

    ## Select ideal and performance metric from DB
    rows = cursor.execute(f"SELECT epoch_slots_ideal, max_performance, active_stake FROM epochdata WHERE epoch=?;",(epoch,),).fetchall()

    ## Parse SQL to get ideal and performance metrics
    ideal_perf = str(rows[0])
    ideal_perf = ideal_perf[1:-1]

    ideal = ideal_perf.split(',')[0]
    perf = ideal_perf.split(',')[1].strip()

    active_stake = ideal_perf.split(',')[2].strip()
    active_stake = active_stake[1:-1]

    ## Select block count metrics from DB
    # sqlite3 blocklog.db "SELECT status, COUNT(status) FROM blocklog WHERE epoch=387 GROUP BY status;"
    invalid_cnt = cursor.execute(f"SELECT COUNT(*) FROM blocklog WHERE epoch=? AND status='invalid';",(epoch,),).fetchall()
    missed_cnt  = cursor.execute(f"SELECT COUNT(*) FROM blocklog WHERE epoch=? AND status='missed';",(epoch,),).fetchall()
    ghosted_cnt = cursor.execute(f"SELECT COUNT(*) FROM blocklog WHERE epoch=? AND status='ghosted';",(epoch,),).fetchall()
    stolen_cnt = cursor.execute(f"SELECT COUNT(*) FROM blocklog WHERE epoch=? AND status='stolen';",(epoch,),).fetchall()
    confirmed_cnt = cursor.execute(f"SELECT COUNT(*) FROM blocklog WHERE epoch=? AND status='confirmed';",(epoch,),).fetchall()
    adopted_cnt = cursor.execute(f"SELECT COUNT(*) FROM blocklog WHERE epoch=? AND status='adopted';",(epoch,),).fetchall()
    leader_cnt = cursor.execute(f"SELECT status, COUNT(status) FROM blocklog WHERE epoch=? AND status='leader';",(epoch,),).fetchall()

    invalid_cnt = extract_count(invalid_cnt)
    missed_cnt = extract_count(missed_cnt)
    ghosted_cnt = extract_count(ghosted_cnt)
    stolen_cnt = extract_count(stolen_cnt)
    confirmed_cnt = extract_count(confirmed_cnt)
    adopted_cnt = extract_count(adopted_cnt) + confirmed_cnt

    try:
        leader_cnt = str(leader_cnt[0])
        leader_cnt = leader_cnt[1:-1]
        leader_cnt = int(leader_cnt.split(',')[1])
    except:
        leader_cnt = 0

    leader_cnt = leader_cnt + adopted_cnt + invalid_cnt + missed_cnt + ghosted_cnt + stolen_cnt

    input_data = cursor.execute(f"SELECT * FROM blocklog WHERE epoch=?;",(epoch,),).fetchall()

    data = {
        "epoch": str(epoch),
        "poolID": poolID,
        "blockData": {
            "ticker": ticker,
            "expected": str(leader_cnt),
            "ideal": ideal,
            "performance": perf,
            "activeStake": active_stake,
            "blocks": [
                {
                    "time": item[2].replace('+00:00', 'Z'),
                    "status": item[-1].capitalize()
                }
                for item in input_data
            ]
        }
    }
    json_string = json.dumps(data, indent=4)

    print(json_string)

    with open(file, "w") as file:
        json.dump(data, file, indent=4)

    return data


if __name__ == '__main__':

    ## API Details
    # Change to True if using an API endpoint
    use_api = False
    load_dotenv()
    url = os.getenv('url')
    secret = os.getenv('secret')

    headers = {
        'Content-Type': 'application/json',
        'yepple-access-key': secret
    }

    ## Pool Details
    ticker="YEPPL"
    poolID = "pool1m3h5p82m6v99nda37rmed8vrkqt43e2a8d89k76gw5ets0gdyag"

    ## File path definitions
    db_path = "/opt/cardano/cnode/guild-db/blocklog/blocklog.db"
    filepath = "./data/"
    if not os.path.exists(filepath):
        os.makedirs(filepath)

    ## SQL Connector
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    ## Get Epoch #
    epoch = get_current_epoch()

    currenttmppath = f"{filepath}e{epoch}.tmp"
    currentjsonpath = f"{filepath}e{epoch}.json"
    data = createtemp(epoch,currenttmppath)

    if comparefiles(currenttmppath,currentjsonpath) == True:
        os.remove(currenttmppath)
        print("Current: No changes")
    else:
        if use_api == True:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                os.rename(currenttmppath,currentjsonpath)
                print("Current: Changes written")
            else:
            # API call failed
               print(f"API call failed with status code: {response.status_code}")
               print("Error message:")
               print(response.text)
               os.remove(currenttmppath)
        else:
            os.rename(currenttmppath,currentjsonpath)
            print("Current: Changes written")


    nexttmppath = f"{filepath}e{epoch+1}.tmp"
    nextjsonpath = f"{filepath}e{epoch+1}.json"

    ## Check to see if the future epochs data is available yet. If not, exit.
    try:
        data = createtemp(epoch+1,nexttmppath)
    except:
        exit()

    if comparefiles(nexttmppath,nextjsonpath) == True:
        os.remove(nexttmppath)
        print("Next: No changes")
    else:
        if use_api == True:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                os.rename(nexttmppath,nextjsonpath)
                print("Next: Changes written")
            else:
            # API call failed
               print(f"API call failed with status code: {response.status_code}")
               print("Error message:")
               print(response.text)
               os.remove(currenttmppath)
        else:
            os.rename(nexttmppath,nextjsonpath)
            print("Next: Changes written")

