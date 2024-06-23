from traceback import format_exc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer
from .config import config
from .logger import get_logger

logger = get_logger()
Base = declarative_base()
db_url = config["system"].get("database", "sqlite+aiosqlite:///:memory:")
logger.debug(f"使用数据库: {db_url}")
engine = create_async_engine(db_url)
del db_url


class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    channel = Column(Integer)
    time = Column(Integer)


async def init_database() -> None:
    async with engine.connect() as conn:
        await conn.run_sync(Message.metadata.create_all)
    logger.info("数据库初始化完成！")


def get_session() -> AsyncSession:
    return AsyncSession(engine)


async def commit_message(id_: int, channel: int, time_: int) -> None:
    async with get_session() as session:
        try:
            session.add(Message(id=id_, channel=channel, time=time_))
        except Exception:
            await session.rollback()
            logger.warning(f"写入数据库失败: {format_exc()}")
        else:
            await session.commit()
