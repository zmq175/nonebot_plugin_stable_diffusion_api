import nonebot
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""
    stable_url = ""
    stable_auth = ""

global_config = nonebot.get_driver().config
config = Config(**global_config.dict())
