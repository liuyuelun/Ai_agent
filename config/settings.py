# 全局配置
# 所有配置项都可通过环境变量覆盖，方便 CI/CD 切换环境

import os

BASE_URL = os.getenv("BASE_URL", "https://dummyjson.com")
TIMEOUT = int(os.getenv("TIMEOUT", "30"))  # 请求超时（秒）
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
