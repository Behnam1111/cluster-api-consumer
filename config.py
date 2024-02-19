import os
from typing import List

from dotenv import load_dotenv


load_dotenv()


class Config:
    def get_hosts(self) -> List[str]:
        hosts_str = os.getenv("HOSTS_PATH", "localhost:8000")
        return hosts_str.split(",")
