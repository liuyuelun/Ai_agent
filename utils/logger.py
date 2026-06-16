import logging
import sys

_format = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_format)

logger = logging.getLogger("automation")
logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False  # 避免和 pytest 日志重复
