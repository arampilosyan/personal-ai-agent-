from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    database_path: str = os.getenv("DATABASE_PATH", "data/agent.db")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "15"))
    max_document_chars: int = int(os.getenv("MAX_DOCUMENT_CHARS", "50000"))
    agent_max_tool_calls: int = int(os.getenv("AGENT_MAX_TOOL_CALLS", "5"))

    def ensure_data_dir(self) -> None:
        Path(self.database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

settings = Settings()
