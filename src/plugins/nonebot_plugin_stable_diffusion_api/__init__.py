import threading
from argparse import Namespace
from base64 import b64decode
from random import randint

import nonebot
from colorama import Fore
from nonebot import logger
from nonebot.adapters.onebot.v12 import MessageEvent, Bot, MessageSegment, ActionFailed
from nonebot.exception import ParserExit
from nonebot.params import CommandArg, RegexDict, ShellCommandArgs
from nonebot.plugin.on import on_command, on_regex, on_shell_command
from nonebot.rule import ArgumentParser

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

command_parser = ArgumentParser()
command_parser.add_argument("seed", default=-1)
command_parser.add_argument("scale", default=-1)
command_parser.add_argument("steps", default=-1)
command_parser.add_argument("size", default="")
command_parser.add_argument("prompt", default="")
command_parser.add_argument("negative", default="")

drawer = on_shell_command("AI画图", aliases={"Ai画图", "生成色图", "ai画图"}, parser=command_parser)
logger.info("ai画图启动")

try:
    post_url = config.stable_url
    logger.info(f"post_url: {post_url}")
except AttributeError:
    post_url = ""
    logger.warning("could not fetch stable diffusion url, check your config")


@drawer.handle()
async def _(args: ParserExit = ShellCommandArgs()):
    logger.warning(f"wrong args: {args}")
    await drawer.finish(args.message)

@drawer.handle()
async def drawer_task(event: MessageEvent, bot: Bot, args: ShellCommandArgs()):
    id_ = event.get_user_id()
    logger.info(f"start task for id {id_}")

    del user_task_dict[id_]

    seed = args.seed
    scale = args.scale
    steps = args.steps
    size = args.size
    prompt = args.prompt
    uc = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
    if not args.negative == "":
        uc = args.negative

    if seed is None or seed == -1:
        seed = randint(0, pow(2, 32))
    if scale is None or scale == -1:
        scale = 12
    if steps is None or steps == -1:
        steps = 28
    if size is None or size == "":
        size = "512x768"

    try:
        size = size.split("x")
    except AttributeError:
        size = [512, 512]
    size = [int(size[0]), int(size[1])]
    if size[0] > 1024 or size[1] > 1024:
        drawer.finish("图片尺寸过大，请重新输入！", at_sender=True)

    if prompt is None or prompt == "":
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
