import os
import asyncio
import nest_asyncio
from datetime import datetime

async def canBuy(connection):
    balance = int(asyncio.run(connection.get_account_information())['balance'])
    total_stake = 0.0
    for position in asyncio.run(connection.get_positions()):
        volume = int(position['volume'])
        current_price = int(position['currentPrice'])
        total_stake += volume*current_price

    return (total_stake/balance) < 0.03

async def buy(connection):
    if asyncio.run(canBuy(connection.connectionRPC)):

        print(str(datetime.now()) + " - Will perform a purchase")

        if str(os.getenv("DEBUG")) == "False":

            asyncio.run(connection.connection.create_market_buy_order(
                symbol=str(os.getenv("SYMBOL")), 
                volume=0.07, 
                stop_loss=0.965,
                stopLossUnits="RELATIVE_PRICE"))

    else:
        print("Cannot buy, there is too much at stake in the account")


async def sell(connection):
    total_volume = 0.0
    print("Will sell: ")

    #sum of all volumes of all positions active of the symbol chosen
    total_volume = sum([position['volume'] for position in await connection.connectionRPC.get_positions() if position['symbol'] == str(os.getenv("SYMBOL"))])
    print(str(total_volume))    

    if total_volume != 0.0 and (os.getenv("DEBUG") == "False"):
        asyncio.run(connection.connection.create_market_sell_order(
            symbol=str(os.getenv("SYMBOL")), 
            volume=total_volume))


#BUYING OPTIONS
# print(await connection.create_stop_limit_buy_order(symbol='GBPUSD', volume=0.07, open_price=1.5,
#     stop_limit_price=1.4, stop_loss=0.9, take_profit=2.0, options={'comment': 'comment',
#     'clientId': 'TE_GBPUSD_7hyINWqAl'}))

# print(await connection.create_limit_buy_order(symbol='GBPUSD', volume=0.07, open_price=1.0, stop_loss=0.9,
#     take_profit=2.0, options={'comment': 'comment', 'clientId': 'TE_GBPUSD_7hyINWqAl'}))

# print(await connection.create_stop_buy_order(symbol='GBPUSD', volume=0.07, open_price=1.5, stop_loss=2.0,
#     take_profit=0.9, options={'comment': 'comment', 'clientId': 'TE_GBPUSD_7hyINWqAl'}))


#SELLING OPTIONS

# print(await connection.create_limit_sell_order(symbol='GBPUSD', volume=0.07, open_price=1.5, stop_loss=2.0,
#     take_profit=0.9, options={'comment': 'comment', 'clientId': 'TE_GBPUSD_7hyINWqAl'}))

# print(await connection.create_stop_sell_order(symbol='GBPUSD', volume=0.07, open_price=1.0, stop_loss=2.0,
#     take_profit=0.9, options={'comment': 'comment', 'clientId': 'TE_GBPUSD_7hyINWqAl'}))

# print(await connection.create_stop_limit_sell_order(symbol='GBPUSD', volume=0.07, open_price=1.0,
#     stop_limit_price=1.1, stop_loss=2.0, take_profit=0.9, options={'comment': 'comment',
#     'clientId': 'TE_GBPUSD_7hyINWqAl'}))


#OTHER OPTIONS, AFTER BUYING
# print(await connection.modify_position(position_id='46870472', stop_loss=2.0, take_profit=0.9))
# print(await connection.close_position_partially(position_id='46870472', volume=0.9))
# print(await connection.close_position(position_id='46870472'))
# print(await connection.close_by(position_id='46870472', opposite_position_id='46870482'))
# print(await connection.close_positions_by_symbol(symbol='EURUSD'))
# print(await connection.modify_order(order_id='46870472', open_price=1.0, stop_loss=2.0, take_profit=0.9))
# print(await connection.cancel_order(order_id='46870472'))