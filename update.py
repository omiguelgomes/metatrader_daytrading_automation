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

    if newOperation == "Buy" and graph.operation != "Buy" and graph.candleCrossedLine:
        asyncio.run(transactioner.buy(connection))
    elif newOperation == "Sell" and graph.operation != None:
        asyncio.run(transactioner.sell(connection))
        
    if not graph.candleCrossedLine:
        print("Graph did not cross line")

    graph.operation = newOperation

async def update(graph, connection, time):

    #UPDATE ATTRS AND VARS
    atr = update_atr(graph.currCandle)
    upT, downT = update_vars(graph.currCandle, atr)


    #UPDATE CCI
    data =  asyncio.run(connection.account.get_historical_candles(symbol=os.getenv("SYMBOL"), timeframe=str(os.getenv("TIMEFRAME")),
                                               start_time=time, limit=int(os.getenv("PERIOD"))))
    data_frame = pd.DataFrame(data)
    data_frame['time'] = pd.to_datetime(data_frame['time'], unit='s')
    cci = update_cci(int(os.getenv("PERIOD")), data_frame)


    #MAGICLINE
    update_magicLine(cci, upT, downT, graph)


    #OPERATION
    asyncio.run(update_operation(graph, cci, connection))


    #PRINTS
    print(graph.magicLine)
    print(graph.currCandle.iloc[0])
    print("cci: " + str(cci))
    print(str(time) + " - Current operation is: " + str(graph.operation))


    #RESET CANDLE
    graph.candleCrossedLine = False
    graph.currCandle = graph.newCandle

    return