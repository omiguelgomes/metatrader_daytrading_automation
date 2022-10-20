import pandas as pd
from dotenv import load_dotenv
import os
import time
import asyncio
import nest_asyncio
from metaapi_cloud_sdk import MetaApi
import datetime
import update as updater
import transaction as transactioner
from connection import Connection
from marketHours import MarketHours
from graph import Graph
load_dotenv()
nest_asyncio.apply()

async def main_loop(connection):

    graph = asyncio.run(Graph.create(connection))
    marketHours = MarketHours.create()

    #check new times, and stop the bot for that time
    while True:
        if marketHours.is_open_hour():
            graph.get_new_candle()
            print(graph.newCandle)

            #Candle ended, make transaction
            if graph.newCandle.iloc[0]['brokerTime'] != graph.prevCandle.iloc[0]['brokerTime']:
                graph.candle_ended()
            else:
                graph.set_candle_ended(False)

            asyncio.run(updater.update(graph, connection))
            print(str(datetime.datetime.now()) + " - Current operation is: " + str(graph.operation))
            
        time.sleep(int(os.getenv("REFRESH")))

async def main():
    #Login
    connection = asyncio.run(Connection.create())

    print("Login done")

    await connection.connection.subscribe_to_market_data('EURUSD')

    print("Account connected")
    asyncio.run(main_loop(connection))


if __name__ == '__main__':
    asyncio.run(main())