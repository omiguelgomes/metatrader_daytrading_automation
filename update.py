import warnings
import os
import pandas as pd
import transaction as transactioner
import asyncio
import nest_asyncio
import datetime

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

def update_magicLine(cci, upT, downT, magicLine):
    
    #initialize magicLine
    if magicLine is None:
        magicLine = upT if cci >= 0 else downT
    
    if cci >= 0:
        if upT < magicLine:
            newMagicLine = magicLine
        else:
            newMagicLine = upT
    else:
        if downT > magicLine:
            newMagicLine = magicLine
        else:
            newMagicLine = downT
    
    return newMagicLine

#only uses graph color, doesn't use script alert
async def update_operation(operation, cci, connection, connectionRPC, positions, candleCrossedLine):
    #check if the chart is trending, before updating
    if cci >= 0:
        newOperation = "Buy"
    else:
        newOperation = "Sell"

    #Signal changed, make transaction
    if operation != newOperation and operation is not None:
        if newOperation == "Buy":
            print(str(datetime.datetime.now()) + " - Will perform a purchase")
            asyncio.run(transactioner.buy(connection, connectionRPC, positions))
        elif newOperation == "Sell":
            print(str(datetime.datetime.now()) + " - Will sell everything")
            asyncio.run(transactioner.sell(connection, connectionRPC, positions))
            positions = []
    
    #First buy of the run
    elif operation is None and newOperation == "Buy":
        print(str(datetime.datetime.now()) + " - Will perform a purchase")
        asyncio.run(transactioner.buy(connection, connectionRPC, positions))

    #Already bought, but 2 consecutive buy signals appeard
    elif newOperation == "Buy" and operation == "Buy":
        print(str(datetime.datetime.now()) + " - Will perform a purchase")
        asyncio.run(transactioner.buy(connection, connectionRPC, positions))

    #if prevCandle touched magic line, make purchase
    elif candleCrossedLine:
        print(str(datetime.datetime.now()) + " - Will perform a purchase")
        asyncio.run(transactioner.buy(connection, connectionRPC, positions))

    return newOperation

async def update(candle, magicLine, operation, account, connection, connectionRPC, positions, candleEnded, candleCrossedLine):

    atr = update_atr(candle)

    upT, downT = update_vars(candle, atr)

    #historic data, from last <period> days, to get cci
    data =  asyncio.run(account.get_historical_candles(symbol=os.getenv("SYMBOL"), timeframe='5m',
                                               start_time=datetime.datetime.now(), limit=int(os.getenv("PERIOD"))))

    data_frame = pd.DataFrame(data)
    data_frame['time'] = pd.to_datetime(data_frame['time'], unit='s')
    
    cci = update_cci(int(os.getenv("PERIOD")), data_frame)

    newMagicLine = update_magicLine(cci, upT, downT, magicLine)

    if candle.iloc[0]['low'] <= newMagicLine <= candle.iloc[0]['high']:
        candleCrossedLine = True

    if(candleEnded):
        operation = asyncio.run(update_operation(operation, cci, connection, connectionRPC, positions, candleCrossedLine))


    return newMagicLine, operation, candleCrossedLine