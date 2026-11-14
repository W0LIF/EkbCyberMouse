import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Настройки подключения под наш Docker (порт 5434, пользователь ekb)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://ekb:ekb@127.0.0.1:5434/ekb_connect"
)

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    """Зависимость для FastAPI: выдает асинхронную сессию."""
    async with AsyncSessionLocal() as session:
        yield session