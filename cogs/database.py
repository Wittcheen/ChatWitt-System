import interactions
from interactions.models.internal.tasks import IntervalTrigger
import aiomysql

import os
from dotenv import load_dotenv
load_dotenv()

global_pool = None

class Database(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.listen()
    async def on_startup(self):
        self.auto_close_pools.start()

    #region - GET GLOBAL DATABASE POOL
    async def get_global_pool():
        return global_pool
    #endregion

    #region - CREATE DATABASE CONNECTION POOL
    async def create_pool():
        global global_pool
        global_pool = await aiomysql.create_pool(
            host = os.getenv("db_endpoint"),
            port = 3306,
            user = os.getenv("db_username"),
            password = os.getenv("db_password"),
            db = os.getenv("db_name"),
            maxsize = 10,
        )
    #endregion

    #region - CLOSE DATABASE POOL
    async def close_pool():
        global global_pool
        global_pool.close()
        await global_pool.wait_closed()
        global_pool = None
    #endregion

    #region - CREATE ENTRIES TABLE
    async def create_entries_table(message_id: int):
        async with global_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = f"CREATE TABLE g{message_id} ( id BIGINT PRIMARY KEY, user_name TEXT );"
                await cursor.execute(query)
                await conn.commit()
    #endregion

    #region - GET ONE GIVEAWAY BY ID IN DATABASE
    async def get_giveaway_by_id(id: int):
        async with global_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = f"SELECT * FROM giveaways WHERE id = %s"
                await cursor.execute(query, (id))
                row = await cursor.fetchone()
                return row
    #endregion

    #region - GET ALL ACTIVE GIVEAWAYS FROM DATABASE
    async def get_all_giveaways():
        async with global_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = "SELECT * FROM giveaways WHERE active = 1"
                await cursor.execute(query)
                rows = await cursor.fetchall()
                return rows
    #endregion

    #region - GET ALL GIVEAWAY ENTRIES
    async def get_all_entries(message_id: int):
        async with global_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = f"SELECT id FROM g{message_id}"
                await cursor.execute(query)
                rows = await cursor.fetchall()
                column_values = [row["id"] for row in rows]
                return column_values
    #endregion

    #region - INSERT ROW INTO DATABASE
    async def insert_row(table_name: str, data):
        async with global_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                await cursor.execute(query, tuple(data.values()))
                await conn.commit()
    #endregion

    #region - DELETE ROW FROM DATABASE
    async def delete_row(table_name: str, message_id: int):
        async with global_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = f"DELETE FROM {table_name} WHERE id = %s"
                await cursor.execute(query, (message_id))
                await conn.commit()
    #endregion

    #region - UPDATE GIVEAWAY TO INACTIVE
    async def update_giveaway_inactive(message_id: int):
        async with global_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = f"UPDATE giveaways SET active = 0 WHERE id = %s"
                await cursor.execute(query, (message_id))
                await conn.commit()
    #endregion

    #region - UPDATE ENTRIES COUNT
    async def update_entries(message_id: int):
        async with global_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = f"UPDATE giveaways SET entries = (SELECT COUNT(*) FROM g{message_id}) WHERE id = %s;"
                await cursor.execute(query, (message_id))
                await conn.commit()
    #endregion

    #region - GET RANDOM USER FROM DATABASE
    async def random_user(message_id: int, limit: int):
        async with global_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = f"SELECT id FROM g{message_id} ORDER BY RAND() LIMIT {limit}"
                await cursor.execute(query)
                rows = await cursor.fetchall()
                column_values = [row[0] for row in rows]
                return column_values
    #endregion

    #region - DROP ENTRIES TABLE
    async def drop_entries_table(message_id: int):
        async with global_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = f"DROP TABLE g{message_id};"
                await cursor.execute(query)
                await conn.commit()
    #endregion

    @interactions.Task.create(IntervalTrigger(minutes = 1))
    async def auto_close_pools(self):
        global global_pool
        if not global_pool._closed:
            global_pool.close()
            await global_pool.wait_closed()

def setup(client):
    Database(client)
