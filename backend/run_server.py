"""Запуск uvicorn с прямым логированием в файл."""
import uvicorn
import logging
import os

# Настроим логирование uvicorn
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "uvicorn_direct.log"), mode="w", encoding="utf-8"),
    ]
)

# Запускаем uvicorn напрямую (не через subprocess)
uvicorn.run(
    "api.app.main:app",
    host="0.0.0.0",
    port=8080,
    log_level="debug",
    access_log=True,
)
