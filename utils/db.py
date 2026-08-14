import os.path
import time
from traceback import format_exc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, delete
from .config import config
from .cache import get_cache_dir
from .logger import get_logger

logger = get_logger()
Base = declarative_base()


def _resolve_db_url() -> str:
    """database 未配置（或为 null）时默认持久化到缓存目录，避免重启丢失"""
    database = config["system"].get("database")
    if not database:
        path = os.path.join(get_cache_dir(), "onedisc.db")
        return f"sqlite+aiosqlite:///{path}"
    return database


db_url = _resolve_db_url()
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


async def cleanup_expired_messages(ttl: int) -> None:
    """删除 time 早于 now - ttl 的消息记录（缓存过期清理用）"""
    now = int(time.time())
    async with get_session() as session:
        try:
            result = await session.execute(
                delete(Message).where(Message.time < now - ttl)
            )
            await session.commit()
            if result.rowcount:
                logger.info(f"已清理过期消息记录 {result.rowcount} 条")
        except Exception:
            await session.rollback()
            logger.warning(f"清理过期消息记录失败: {format_exc()}")
