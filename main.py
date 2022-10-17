import pandas as pd
from dotenv import load_dotenv
import time
import asyncio
import nest_asyncio
from metaapi_cloud_sdk import MetaApi
import os
import datetime
import update as updater
import parser as parser
import transaction as transactioner
load_dotenv()
nest_asyncio.apply()

async def get_candle(account):
    candle =  asyncio.run(account.get_historical_candles(
        symbol=os.getenv("SYMBOL"),
        timeframe='5m',
        start_time=datetime.datetime.now(), 
        limit=1))

    candle_frame = pd.DataFrame(candle)
    candle_frame['time'] = pd.to_datetime(candle_frame['time'], unit='s')
    return candle_frame

def is_open_hour(closing_hours):

    start, end = closing_hours[0]
    now = datetime.datetime.now()

    #dont run in down hours
    if now >= start and now <= end:
        return False
    
    else:
        #when close window ends, delete it from list
        if now > end:
            closing_hours.pop(0)
        
        return True
        

async def main_loop(account, connection, connectionRPC):
    magicLine = None
    operation = None

    closing_hours = parser.parse_closing_hours()

    orders = []

    #check new times, and stop the bot for that time
    while True:
        if is_open_hour(closing_hours):

            candle = asyncio.run(get_candle(account))
            magicLine, operation = asyncio.run(updater.update(candle, magicLine, operation, account, connection, connectionRPC, orders))
            print(str(datetime.datetime.now()) + " - Current operation is: " + str(operation))
            
        time.sleep(int(os.getenv("REFRESH")))

async def main():
    #Login
    token = str(os.getenv("TOKEN"))
    api = MetaApi(token=token)
    account =  await api.metatrader_account_api.get_account(account_id=str(os.getenv("ACCOUNT_ID")))

    print("Login done")

    #connect to servers
    await account.deploy()
    await account.wait_connected()

    connection = account.get_streaming_connection()
    await connection.connect()
    await connection.wait_synchronized({'timeoutInSeconds': 600})
    connectionRPC = account.get_rpc_connection()
    asyncio.run(connectionRPC.connect())
    terminal_state = connection.terminal_state
    await connection.subscribe_to_market_data('EURUSD')

    print("Account connected")
    asyncio.run(main_loop(account, connection, connectionRPC))


if __name__ == '__main__':
    asyncio.run(main())