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

    if len(closing_hours) == 0: return True

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
    candleCrossedLine = False
    newCandle = asyncio.run(get_candle(account))
    prevCandle = asyncio.run(get_candle(account))
    closing_hours = parser.parse_closing_hours()

    orders = []

    #check new times, and stop the bot for that time
    while True:
        if is_open_hour(closing_hours):
            newCandle = asyncio.run(get_candle(account))

            #Candle ended, make transaction
            if newCandle.iloc[0]['brokerTime'] != prevCandle.iloc[0]['brokerTime']:
                prevCandle = newCandle
                candleEnded = True
            else:
                candleEnded = False

            magicLine, operation, candleCrossedLine = asyncio.run(updater.update(newCandle, magicLine, operation, account, connection, connectionRPC, orders, candleEnded, candleCrossedLine))
            print(str(datetime.datetime.now()) + " - Current operation is: " + str(operation))
            
        time.sleep(int(os.getenv("REFRESH")))

async def main():
    #Login
    token = str(os.getenv("TOKEN"))
    account_id = str(os.getenv("ACCOUNT_ID"))

    token = str(os.getenv("TOKEN"))
    api = MetaApi(token=token)
    account =  await api.metatrader_account_api.get_account(account_id=account_id)

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