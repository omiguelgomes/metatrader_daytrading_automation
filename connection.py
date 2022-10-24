from metaapi_cloud_sdk import MetaApi
import asyncio
import nest_asyncio
from dotenv import load_dotenv
import os

class Connection:
    async def create():
        self = Connection()
        self.account = asyncio.run(self.get_account())
        self.connection = asyncio.run(self.get_connection())
        self.connectionRPC = asyncio.run(self.get_connectionRPC())
        return self

    async def get_account(self):
        account_id = str(os.getenv("ACCOUNT_ID"))
        token = str(os.getenv("TOKEN"))
        api = MetaApi(token=token)
        account = asyncio.run(api.metatrader_account_api.get_account(account_id=account_id))
        asyncio.run(account.deploy())
        asyncio.run(account.wait_connected())
        print("connected")
        return account

    async def get_connection(self):
        connection = self.account.get_streaming_connection()
        asyncio.run(connection.connect())
        asyncio.run(connection.wait_synchronized({'timeoutInSeconds': 600}))
        return connection

    async def get_connectionRPC(self):
        connectionRPC = self.account.get_rpc_connection()
        asyncio.run(connectionRPC.connect())
        return connectionRPC