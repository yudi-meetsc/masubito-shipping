from typing import Optional, Dict
from pydantic import BaseModel


class JobStatus(BaseModel):
    step: str = "pending"
    pct: int = 0
    message: str = "準備中..."
    download_url: Optional[str] = None
    error: Optional[str] = None


jobs: Dict[str, JobStatus] = {}
