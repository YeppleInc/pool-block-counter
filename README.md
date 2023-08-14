# pool-block-counter
A Python script that can be placed on a Cardano Block Producer node to extract block data (scheduled/minted/missed/etc) and writes updates to a file  and/or submits them to an API endpoint.

# Installation
Clone the repo to your git directory:
git clone https://github.com/YeppleInc/pool-block-counter

Give permissions for the file block_count.sh to run:
chmod 755 block_count.sh

Edit block_count.sh and ensure the path is correct (you may need to change the username from 'admin' to whatever user you are logged in as).

Create a crontab job to run this script every 2 minutes:
crontab -e
*/2 * * * * /home/admin/git/pool-block-counter/block_count.sh 

Edit block_count.py:
Replace the pool ticker and pool ID (lines 149-150) with your pools information.
That's it! The script will now run every 2 minutes and write the epoch block count information as a json file to the /data/ directory. See sample below.

[Optional] If you would like to send the json information to an API endpoint, then:
1) Replace line 138, "use_api = False" with "use_api = True"
2) Create a file called ".env" in the same directory and define the API endpoint URL and secret key. For example:
#.env
url=https://client-api.yepple.io/v1/apps/stakepools/epoch/set
secret=[secret_key]

# Sample Output
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
data example
