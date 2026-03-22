import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://syslog_user:Syslog2025@127.0.0.1:5432/syslog'

async def check():
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            await session.execute(text('SELECT 1'))
        print('Connection successful!')
        return True
    except Exception as e:
        print(f'Connection failed: {e}')
        return False

asyncio.run(check())
