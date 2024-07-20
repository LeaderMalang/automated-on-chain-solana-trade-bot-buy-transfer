import sys
import time
import asyncio
from solders.keypair import Keypair
from solana.rpc.api import Client
from buy_swap import buy
from token_transfer import transfer_normal
from dotenv import dotenv_values
config = dotenv_values(".env")


if len(sys.argv) < 3:
    print("Usage: python main.py <CONTRACT_ADDRESS> <PRIVATE_KEY_1> [<PRIVATE_KEY_2> ...]")
    sys.exit(1)

# Get contract address and wallet keys from console arguments
arg_contract_address=sys.argv[1]
arg_wallet_keys=sys.argv[2:]

# print(arg_contract_address,arg_wallet_keys)
# Connect to Solana cluster
solana_client = Client(config["RPC_HTTPS_URL"])

# Define buy amounts and cycles
# Example usage
start = 0.0000001
stop = 0.0000009
num_elements = 2
buy_times=1


def float_range(start, stop, num_elements):
    step = (stop - start) / (num_elements - 1)
    return [start + step * i for i in range(num_elements)]
amounts = float_range(start, stop, num_elements)
dest_wallet='A6ZkTEfwNnLxgJcFaknGvdz2NoKPHRDZC5evN6x5AnJK'
##
async def main():

    token_toBuy=arg_contract_address #Enter token you wish to buy here
    for i in range(buy_times):
        print("buy time",i+1)
        for wallet in arg_wallet_keys:
            payer = Keypair.from_base58_string(wallet)
            # print(payer.pubkey())
            for amount in amounts:

                buy_transaction=await buy(solana_client, token_toBuy, payer, amount) #Enter amount of sol you wish to spend
                print(buy_transaction,"Buy TX with Amount",amount)
                time.sleep(5)
        
        
            transfer_txn=await transfer_normal(solana_client, token_toBuy, payer,dest_wallet)
            print(transfer_txn,"Transfer TX",)
            time.sleep(5)
        

while True:
    
    asyncio.run(main())