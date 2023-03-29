import threading
from base64 import b64decode
from random import randint

import nonebot
from colorama import Fore
from nonebot import logger
from nonebot.adapters.onebot.v12 import MessageEvent, Bot, MessageSegment, ActionFailed
from nonebot.params import CommandArg, RegexDict
from nonebot.plugin.on import on_command
from .config import Config
from .worker import get_data

from nonebot import require
from .taskQueue import TaskQueue

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

global_config = nonebot.get_driver().config
config = Config.parse_obj(global_config)

taskQueue = TaskQueue()
user_task_dict = {}

drawer = on_command("AI画图", priority=5)
logger.info("ai画图启动")

try:
    post_url = config.stable_url
    logger.info(f"post_url: {post_url}")
except AttributeError:
    post_url = ""
    logger.warning("could not fetch stable diffusion url, check your config")


@drawer.handle()
async def drawer_task(event: MessageEvent, bot: Bot, regex: dict = RegexDict()):
    id_ = event.get_user_id()
    logger.info(f"start task for id {id_}")

    del user_task_dict[id_]

    seed = regex["seed"]
    scale = regex["scale"]
    steps = regex["steps"]
    size = regex["size"]
    prompt = regex["prompt"]
    uc = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"

    if seed is None:
        seed = randint(0, pow(2, 32))
    if scale is None:
        scale = 12
    if steps is None:
        steps = 28
    if size is None:
        size = "512x768"

    try:
        size = size.split("x")
    except AttributeError:
        size = [512, 512]
    size = [int(size[0]), int(size[1])]
    if size[0] > 1024 or size[1] > 1024:
        drawer.finish("图片尺寸过大，请重新输入！", at_sender=True)

    if prompt is None:
        drawer.finish("当前不支持无参数输入，请补充prompts", at_sender=True)

    # 获取用户名
    name = (await bot.get_stranger_info(user_id=int(id_)))["nickname"]

    await drawer.send("正在生成图片，请稍等...", at_sender=True)
    logger.info(
        Fore.LIGHTYELLOW_EX +
        f"\n开始生成{name}的图片："
        f"\nscale={scale}"
        f"\nsteps={steps}"
        f"\nsize={size[0]},{size[1]}"
        f"\nseed={seed}"
        f"\nprompt={prompt}"
        f"\nnegative prompt={uc}"
    )

    data = await get_data(
        post_url=post_url + "sdapi/v1/txt2img",
        size=size,
        prompt=prompt,
        timeout=10 * 60 * 1000,
        uc=uc, steps=steps,
        scale=scale,
        seed=seed
    )

    if data[0] is False:
        logger.error(Fore.LIGHTRED_EX + f"后端请求失败：{data[1]}")
        await drawer.finish("生成失败！", at_sender=True)

    image = b64decode(data[1])
    msg = MessageSegment.image(image)
    try:
        msg_id = (await drawer.send(msg, at_sender=True))["message_id"]
    except ActionFailed:
        logger.warning(Fore.LIGHTYELLOW_EX + f"可能被风控，请稍后再试！")
