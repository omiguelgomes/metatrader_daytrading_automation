import warnings
import os
import pandas as pd
import transaction as transactioner
import asyncio
import nest_asyncio
from datetime import datetime

def update_cci(period, data):
    #For some reason, I believe pine uses close instead of typical price
    # data['TP'] = (data['high'] + data['low'] + data['close'])/3
    data['TP'] = data['close']
    data['SMA'] = data['TP'].rolling(period).mean()
    
    #.mad() will be deprecated
    warnings.simplefilter("ignore", FutureWarning)
    data['MAD'] = data['TP'].rolling(period).apply(lambda x: pd.Series(x).mad())
    
    data['CCI'] = (data['TP'] - data['SMA'])/(0.015*data['MAD'])
    return data['CCI'][period-1]

def update_atr(candle_frame):
    data = candle_frame.copy()
    
    high = data['high']
    low = data['low']
    close = data['close']
    data['tr0'] = abs(high - low)
    data['tr1'] = abs(high - close.shift())
    data['tr2'] = abs(low - close.shift())
    tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
    atr = tr.ewm(alpha=1/int(os.getenv("AP")), adjust=False).mean()
    return atr

def update_vars(candle, atr):
    coeff = int(os.getenv("COEFF"))
    upT = candle.iloc[0]['low'] - atr.iloc[0]*coeff
    downT = candle.iloc[0]['high'] + atr.iloc[0]*coeff

    return upT, downT

def update_magicLine(cci, upT, downT, graph):
    
    #initialize magicLine
    if graph.magicLine is None:
        graph.magicLine = upT if cci >= 0 else downT
    
    if cci >= 0:
        if upT < graph.magicLine:
            newMagicLine = graph.magicLine
        else:
            newMagicLine = upT
    else:
        if downT > graph.magicLine:
            newMagicLine = graph.magicLine
        else:
            newMagicLine = downT
    
    graph.magicLine = newMagicLine
    return

#only uses graph color, doesn't use script alert
async def update_operation(graph, cci, connection):
    #check if the chart is trending, before updating
    if cci >= 0:
        newOperation = "Buy"
    else:
        newOperation = "Sell"

    #Signal changed, make transaction
    if graph.operation != newOperation and graph.operation is not None:
        if newOperation == "Buy":
            asyncio.run(transactioner.buy(connection, graph.positions))
        elif newOperation == "Sell":
            asyncio.run(transactioner.sell(connection, graph.positions))
            graph.positions = []
    
    #First buy of the run
    elif graph.operation is None and newOperation == "Buy":
        asyncio.run(transactioner.buy(connection, graph.positions))

    #Already bought, but 2 consecutive buy signals appeard
    elif newOperation == "Buy" and graph.operation == "Buy":
        asyncio.run(transactioner.buy(connection, graph.positions))

    #if prevCandle touched magic line, make purchase
    elif graph.candleCrossedLine:
        asyncio.run(transactioner.buy(connection, graph.positions))

    graph.operation = newOperation

async def update(graph, connection, time):

    atr = update_atr(graph.newCandle)
    upT, downT = update_vars(graph.newCandle, atr)

    #historic data, from last <period> days, to get cci
    data =  asyncio.run(connection.account.get_historical_candles(symbol=os.getenv("SYMBOL"), timeframe='5m',
                                               start_time=time, limit=int(os.getenv("PERIOD"))))

    data_frame = pd.DataFrame(data)
    data_frame['time'] = pd.to_datetime(data_frame['time'], unit='s')
    
    cci = update_cci(int(os.getenv("PERIOD")), data_frame)

    update_magicLine(cci, upT, downT, graph)

    if graph.newCandle.iloc[0]['low'] <= graph.magicLine <= graph.newCandle.iloc[0]['high']:
        graph.candleCrossedLine = True

    if(graph.candleEnded):
        asyncio.run(update_operation(graph, cci, connection))

    return