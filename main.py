import pandas as pd
from dotenv import load_dotenv
import os
import asyncio
import nest_asyncio
from metaapi_cloud_sdk import MetaApi
from datetime import datetime
import time as t
import update as updater
from connection import Connection
from marketHours import MarketHours
from graph import Graph
load_dotenv()
nest_asyncio.apply()

async def main_loop(connection):

    graph = asyncio.run(Graph.create(connection))
    marketHours = MarketHours.create()
    
    #For debugging purposes, to allow starting on the date we want
    init_time = datetime.now()
    if os.getenv("DEBUG") == "True":
        candle_time = datetime.strptime(os.getenv("START_TIME"), "%Y-%m-%d %H:%M:%S")
    else:
        candle_time = datetime.now()

    #check new times, and stop the bot for that time
    while True:
        if marketHours.is_open_hour():
            time = datetime.now()-(init_time-candle_time)

            asyncio.run(graph.get_new_candle(time))

            #Candle ended, make transaction
            if graph.newCandle.iloc[0]['brokerTime'] != graph.prevCandle.iloc[0]['brokerTime']:
                graph.candle_ended()
            else:
                graph.set_candle_ended(False)

            asyncio.run(updater.update(graph, connection, time))
            print(str(datetime.now()) + " - Current operation is: " + str(graph.operation))
            
        t.sleep(int(os.getenv("REFRESH")))

async def main():
    #Login
    connection = asyncio.run(Connection.create())

    print("Login done")

    await connection.connection.subscribe_to_market_data('EURUSD')

    print("Account connected")
    asyncio.run(main_loop(connection))


if __name__ == '__main__':
    asyncio.run(main())