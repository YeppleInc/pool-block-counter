# pool-block-counter
A Python script that can be placed on a Cardano Block Producer node to extract block data (scheduled/minted/missed/etc) and writes updates to a file  and/or submits them to an API endpoint.

## Installation
1) Clone the repo to your git directory:
```console
git clone https://github.com/YeppleInc/pool-block-counter
```
2) Give permissions for the file block_count.sh to run:
```console
chmod 755 block_count.sh
```
3) Edit block_count.sh and ensure the path is correct (you may need to change the username from 'admin' to whatever user you are logged in as).

4) Create a crontab job to run this script every 2 minutes:
```console
crontab -e
```
Add:<br>
>*/2 * * * * /home/admin/git/pool-block-counter/block_count.sh 

5) Edit .env file and replace the pool ticker and pool ID with your pools information.

That's it! The script will now run every 2 minutes and write the epoch block count information as a json file to the /data/ directory. See sample below.

### Optional API Config 
If you would like to send the json information to an API endpoint, then:<br>

6) Edit the .env file and include details about your API endpoint URL, as well as secret key and header if required.
   
## Sample Output
```
{
    "epoch": "429",
    "poolID": "pool1m3h5p82m6v99nda37rmed8vrkqt43e2a8d89k76gw5ets0gdyag",
    "blockData": {
        "ticker": "YEPPL",
        "expected": "2",
        "ideal": "1.63",
        "performance": "122.7",
        "activeStake": "1710292372424",
        "blocks": [
            {
                "time": "2023-08-10T16:55:31Z",
                "status": "Leader"
            },
            {
                "time": "2023-08-13T12:04:11Z",
                "status": "Confirmed"
            }
        ]
    }
}
```
