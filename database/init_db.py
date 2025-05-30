from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings
from typing_extensions import AsyncIterable

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterable[AsyncSession]:
    db = async_session()
    try:
        yield db
    except Exception as e:
        print(f'ERROR {e=}')
        await db.rollback()
    else:
        await db.commit()
    finally:
        await db.close()