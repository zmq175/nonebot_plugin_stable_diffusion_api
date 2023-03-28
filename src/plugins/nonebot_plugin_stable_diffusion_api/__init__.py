from asyncio import Queue, create_task, get_event_loop
from base64 import b64decode
from random import randint

import nonebot
from colorama import Fore
from nonebot import logger
from nonebot.adapters.onebot.v12 import GroupMessageEvent, Bot, MessageSegment, ActionFailed
from nonebot.params import CommandArg, RegexDict
from nonebot.plugin.on import on_command

from .config import Config
from .worker import get_data

from nonebot import require
require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

global_config = nonebot.get_driver().config
config = Config.parse_obj(global_config)

taskQueue = Queue()
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
async def drawer_handle(event: GroupMessageEvent, bot: Bot, regex: dict = RegexDict()):
    logger.info("start handle drawer")
    id_ = event.get_user_id()

    # 检查当前用户是否已有未完成任务
    if id_ in user_task_dict:
        drawer.finish("你有任务正在排队，请耐心等待！", at_sender=True)
        return

    # 创建一个任务并添加到队列中
    task = create_task(drawer_task(event, bot, regex))
    user_task_dict[id_] = task
    if not taskQueue.empty():
        name = (await bot.get_stranger_info(user_id=int(id_)))["nickname"]
        await drawer.send(f"您的前面还有{taskQueue.qsize()}个任务，已提交任务，请耐心等待！", at_sender=True)
    await taskQueue.put(task)


async def drawer_task(event: GroupMessageEvent, bot: Bot, regex: dict = RegexDict()):
    id_ = event.get_user_id()
    logger.info(f"start task for id {id_}")

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


@scheduler.scheduled_job("cron", second="*/1", id="draw job")
async def handle_queue():
    while True:
        # 从队列中取出任务
        logger.info("尝试获取任务")
        task = await taskQueue.get()
        logger.info(f"运行任务")
        # 运行任务
        await task
        # 任务运行完成后，将其从user_task_dict中删除
        id_ = task._coro.cr_frame.f_locals['event'].get_user_id()
        del user_task_dict[id_]
        # 通知下一个任务可以开始了
        taskQueue.task_done()

