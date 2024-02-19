import os
from typing import List

from dotenv import load_dotenv


def get_hosts() -> List[str]:
    hosts_str = os.getenv("HOSTS")
    if hosts_str is None:
        raise ValueError("HOSTS environment variable not set")
    return hosts_str.split(",")


load_dotenv()


class Config:
    def get_hosts(self) -> List[str]:
        hosts_str = os.getenv("HOSTS", "localhost")
        return hosts_str.split(",")
