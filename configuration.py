import os
from os import getenv

import dotenv
from pydantic import BaseModel

dotenv.load_dotenv()


class BaseConfig(BaseModel):
    AUTH_TOKEN: str = getenv("AUTH_TOKEN")
    IMAGE_DIR: str = getenv("IMAGE_DIR")
    DATA_FILE: str = getenv("DATA_FILE")


def from_envvar():
    options = BaseConfig
    loaded_config = options(**os.environ)
    return dict(loaded_config)
