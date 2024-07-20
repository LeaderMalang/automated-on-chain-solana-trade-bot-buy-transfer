import asyncio
import datetime
import time
from solana.rpc.types import TokenAccountOpts
from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey
from solana.rpc.commitment import Confirmed, Finalized, Commitment
from solana.rpc.api import RPCException
from solana.rpc.api import Client
from solders.compute_budget import set_compute_unit_price,set_compute_unit_limit
from solana.rpc.types import TxOpts
from spl.token.instructions import CloseAccountParams, close_account
from create_close_account import fetch_pool_keys, get_token_account, make_swap_instruction ,sell_get_token_account
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import transfer_checked, TransferCheckedParams
from spl.token.client import Token
from solana.transaction import Transaction
from spl.token.constants import WRAPPED_SOL_MINT

from dotenv import dotenv_values
config = dotenv_values(".env")
RPC_HTTPS_URL = (config["RPC_HTTPS_URL"])




solana_client = Client(RPC_HTTPS_URL) #Enter your API KEY

LAMPORTS_PER_SOL = 1000000000
MAX_RETRIES = 3
RETRY_DELAY = 3


def getTimestamp():
    while True:
        timeStampData = datetime.datetime.now()
        currentTimeStamp = "[" + timeStampData.strftime("%H:%M:%S.%f")[:-3] + "]"
        return currentTimeStamp


async def get_transaction_with_timeout(client, txid, commitment=Confirmed, timeout=10):
    # Wrap the synchronous get_transaction call in a coroutine
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, client.get_transaction, txid, "json")



async def transfer_normal(solana_client, TOKEN_TO_SWAP_SELL, payer,dest_wallet):
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            # token_symbol, SOl_Symbol = getSymbol(TOKEN_TO_SWAP_SELL)
            mint = Pubkey.from_string(TOKEN_TO_SWAP_SELL)
            dest_wallet_account=Pubkey.from_string(dest_wallet)
            sol= WRAPPED_SOL_MINT
            TOKEN_PROGRAM_ID = solana_client.get_account_info_json_parsed(mint).value.owner
            pool_keys = fetch_pool_keys(str(mint))
            accountProgramId = solana_client.get_account_info_json_parsed(mint)
            programid_of_token = accountProgramId.value.owner
            accounts = solana_client.get_token_accounts_by_owner_json_parsed(payer.pubkey(), TokenAccountOpts(
                program_id=programid_of_token)).value
            amount_in=0
            for account in accounts:
                mint_in_acc = account.account.data.parsed['info']['mint']
                if mint_in_acc == str(mint):
                    amount_in = int(account.account.data.parsed['info']['tokenAmount']['amount'])
                    print("Your Token Balance is: ", amount_in)
                    break

            swap_token_account = sell_get_token_account(solana_client, payer.pubkey(), mint)
            WSOL_token_account, WSOL_token_account_Instructions = get_token_account(solana_client, payer.pubkey(), sol)
            print(amount_in)
            if amount_in==0:
                print("Mint Token Account Balance is 0 , So can make sell trasaction.")
                return False

            print("3. Create Transfer Instructions...")
            spl_client = Token(conn=solana_client, pubkey=mint, program_id=swap_token_account, payer=payer)

            dest_account_info=solana_client.get_account_info(dest_wallet_account)
            # Fetch or create destination token account
            try:
                dest_token_account = spl_client.get_accounts_by_owner(owner=dest_wallet_account, commitment=None, encoding='base64').value[0].pubkey
            except:
                dest_token_account = spl_client.create_associated_token_account(owner=dest_wallet_account, skip_confirmation=False, recent_blockhash=None)

            tx = Transaction()
            tx.add(transfer_checked(
                    TransferCheckedParams(
                program_id=TOKEN_PROGRAM_ID,
                source=swap_token_account,
                mint=mint,
                dest=dest_token_account,
                owner=payer.pubkey(),
                amount=amount_in,
                decimals=6,
                signers=[]
                    )
                )
            )
            
            transaction=solana_client.send_transaction(
                tx, payer, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed))
                    
            if transaction:

                print(f"Transaction Signature: https://solscan.io/tx/{transaction.value}")
                # Await transaction confirmation with a timeout
                await asyncio.wait_for(
                    get_transaction_with_timeout(solana_client, transaction.value, commitment="confirmed", timeout=10),
                    timeout=15
                )
                print("Transaction Confirmed")
                return True
        except asyncio.TimeoutError:
            print("Transaction confirmation timed out. Retrying...")
            retry_count += 1
            time.sleep(RETRY_DELAY)
        except RPCException as e:
            print(f"RPC Error: [{e.args[0].message}]... Retrying...")
            retry_count += 1
            time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"Unhandled exception: {e}. Retrying...")
            # retry_count= MAX_RETRIES
            retry_count+= 1
            time.sleep(RETRY_DELAY)

            # return False
    print("Failed to confirm transaction after maximum retries.")
    return False

# async def main():

#     token_toBuy="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
#     payer = Keypair.from_base58_string(config['PrivateKey'])
#     print(payer.pubkey())
#     # print(payer.prikey())
#     await sell_normal(solana_client, token_toBuy, payer)

# asyncio.run(main())