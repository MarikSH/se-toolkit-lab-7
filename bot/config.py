import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env.bot.secret"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

@dataclass
class LmsConfig:
    base_url: str
    api_key: str

    @classmethod
    def from_env(cls) -> "LmsConfig":
        return cls(
            base_url=os.environ.get("LMS_API_URL", "http://localhost:42002"),
            api_key=os.environ.get("LMS_API_KEY", "my-secret-api-key"),
        )

lms_config = LmsConfig.from_env()
