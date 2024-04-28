import asyncpg
from create_bot import os

class Psql:

    def __init__(self, pool):
        self.pool = pool


    @classmethod
    async def connect_postgres(self):
        pool = await asyncpg.create_pool(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            database='postgres'
        )
        return self(pool)


    @classmethod
    async def connect(self):
        pool = await asyncpg.create_pool(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            database=os.getenv('POSTGRES_DATABASE')
        )
        return self(pool)


    async def close_pool(self):
        await self.pool.close()


    async def create_db(self, db_name):
        query = f"""CREATE DATABASE {db_name};"""
        try:
            return await self.pool.execute(query)
        except Exception as e:
            print(e)
            return False


    async def create_users_table(self):
        query = """
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                tg_id BIGINT NOT NULL UNIQUE,
                coin1 VARCHAR(255),
                coin2 VARCHAR(255),
                min1 INT NOT NULL,
                max1 INT NOT NULL,
                min2 INT NOT NULL,
                max2 INT NOT NULL
            );
        """
        await self.pool.execute(query)


    async def create_user(self, tg_id, coin1, coin2, min1, max1, min2, max2) -> bool:
        query = """
            INSERT INTO users (
                tg_id, coin1, coin2, min1, max1, min2, max2) 
                VALUES ($1, $2, $3, $4, $5, $6, $7) 
                ON CONFLICT (tg_id) DO NOTHING;
        """
        try:
            await self.pool.execute(query, tg_id, coin1, coin2, \
                min1, max1, min2, max2)
            return True
        except Exception as e:
            print(e)
            return False
    
    
    async def get_user_data(self, tg_id) -> list:
        query = """
            SELECT * FROM users WHERE tg_id=$1;
        """
        try:
            return await self.pool.fetch(query, tg_id)
        except Exception as e:
            print(e)
            return False


    async def add_coin(self, tg_id, coin_target, coin_name):
        query = f"""UPDATE users SET {coin_target} = $2 WHERE tg_id = $1"""
        try:
            await self.pool.execute(query, tg_id, coin_name)
            return True
        except Exception as e:
            print(e)
            return False


    async def add_value(self, tg_id, value_target, value):
        query = f"""UPDATE users SET {value_target} = $2 WHERE tg_id = $1"""
        try:
            await self.pool.execute(query, tg_id, value)
            return True
        except Exception as e:
            print(e)
            return False


    async def get_all_users_data(self) -> list:
        query = """
            SELECT * FROM users;
        """
        try:
            return await self.pool.fetch(query)
        except Exception as e:
            print(e)
            return False