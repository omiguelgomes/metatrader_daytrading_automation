from metaapi_cloud_sdk import MetaApi
import asyncio
import nest_asyncio
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import os

class Graph:
    async def create(connection, time):
        self = Graph()
        self.positions = self.get_positions()
        self.magicLine = None
        self.operation = None
        self.candleCrossedLine = False
        self.candleEnded = False
        self.connection = connection
        self.newCandle = asyncio.run(self.get_candle(self.connection.account, time))
        self.currCandle = asyncio.run(self.get_candle(self.connection.account, time))
        return self

    def set_candle_ended(self, candleEnded):
        self.candleEnded = candleEnded

    #Alter this later to parse all current positions when starting up
    def get_positions(self):
        return []

    def candle_ended(self):
        
        if self.magicLine != None:
            low_3 = round(self.currCandle.iloc[0]['low'], 3)
            high_3 = round(self.currCandle.iloc[0]['high'], 3)
            magic_3 = round(self.magicLine, 3)

            #Precision is only 3 decimal places
            if low_3 <= magic_3 <= high_3:
                self.candleCrossedLine = True

        self.candleEnded = True

    async def get_new_candle(self, time):
        self.newCandle = asyncio.run(self.get_candle(self.connection.account, time))

    async def get_candle(self, account, time):
        candle =  asyncio.run(account.get_historical_candles(
            symbol=os.getenv("SYMBOL"),
            timeframe=str(os.getenv("TIMEFRAME")),
            start_time=time,
            limit=1))

        candle_frame = pd.DataFrame(candle)
        candle_frame['time'] = pd.to_datetime(candle_frame['time'], unit='s')
        return candle_frame