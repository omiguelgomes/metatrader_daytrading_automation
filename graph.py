from metaapi_cloud_sdk import MetaApi
import asyncio
import nest_asyncio
import datetime
import pandas as pd
from dotenv import load_dotenv
import os

class Graph:
    async def create(connection):
        self = Graph()
        self.positions = self.get_positions()
        self.magicLine = None
        self.operation = None
        self.candleCrossedLine = False
        self.candleEnded = False
        self.connection = connection
        self.newCandle = asyncio.run(self.get_candle(self.connection.account))
        self.prevCandle = asyncio.run(self.get_candle(self.connection.account))
        return self

    def set_candle_ended(self, candleEnded):
        self.candleEnded = candleEnded

    #Alter this later to parse all current positions when starting up
    def get_positions(self):
        return []

    def candle_ended(self):
        self.prevCandle = self.newCandle
        self.candleEnded = True

    async def get_new_candle(self):
        self.newCandle = asyncio.run(self.get_candle(self.connection))

    async def get_candle(self, account):
        candle =  asyncio.run(account.get_historical_candles(
            symbol=os.getenv("SYMBOL"),
            timeframe='5m',
            start_time=datetime.datetime.now(),
            limit=1))

        candle_frame = pd.DataFrame(candle)
        candle_frame['time'] = pd.to_datetime(candle_frame['time'], unit='s')
        return candle_frame