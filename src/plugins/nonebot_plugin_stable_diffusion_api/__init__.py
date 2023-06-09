import hashlib
import json
import random
import threading
from argparse import Namespace
from base64 import b64decode
from random import randint

import nonebot
from colorama import Fore
from nonebot import logger
from nonebot.adapters.onebot.v11 import MessageEvent, Bot, MessageSegment, ActionFailed, Event
from nonebot.adapters.telegram import MessageSegment as TelegramMessageSegment
from nonebot.adapters.telegram import Bot as TelegramBot
from nonebot.adapters.telegram import Event as TelegramEvent
from nonebot.adapters.telegram.exception import ActionFailed as TelegramActionFailed
from nonebot.adapters.telegram.message import File
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
import deepl

global_config = nonebot.get_driver().config
config = Config.parse_obj(global_config)

taskQueue = TaskQueue()
user_task_dict = {}

command_parser = ArgumentParser()
command_parser.add_argument("--seed", default=-1, required=False)
command_parser.add_argument("--scale", default=-1, required=False)
command_parser.add_argument("--steps", default=-1, required=False)
command_parser.add_argument("--size", default="", required=False)
command_parser.add_argument("--prompt", default="", required=False)
command_parser.add_argument("--negative", default="", required=False)
command_parser.add_argument("--sampler", default="", required=False)
command_parser.add_argument("--hires", action="store_true")

with open("/home/ec2-user/nonoko/nonebot_plugin_stable_diffusion_api/src/plugins/nonebot_plugin_stable_diffusion_api"
          "/tags.json", "r") as f:
    tag_sets_list = json.load(f)

with open("/home/ec2-user/nonoko/nonebot_plugin_stable_diffusion_api/src/plugins/nonebot_plugin_stable_diffusion_api"
          "/lora.json", "r") as f:
    lora_list = json.load(f)

tag_sets = set(tag_sets_list)

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
    await drawer.finish(f"{args.message}, 目前支持的Lora模型列表如下：\n <lora:ArknightsChen5concept_10:1>"
                        f" <lora:ArknightsNian_20:1> "
                        f"<lora:AzumaSeren_v10:1> "
                        f"<lora:Bremerton (Kung Fu Cruiser) "
                        f"(Azur Lane):1>"
                        f" <lora:GawrGuraFlatisJustice:1> "
                        f"<lora:Lucy (Cyberpunk Edgerunners):1>"
                        f" <lora:Raiden Shogun:1> "
                        f"<lora:Rem_RE Zero:1> "
                        f"<lora:Shengren:1> "
                        f"<lora:YDLunaCos:1> "
                        f"<lora:YaeMikoRealisticGenshin:1> "
                        f"<lora:Yuefu:1> "
                        f"<lora:Yuta:1> "
                        f"<lora:aliceNikke_v30:1>"
                        f" <lora:arknightsTexas20the.uDnD:1> <lora:banbanbai:1> <lora:corruption_v1:1> "
                        f"<lora:godChineseGirl:1> <lora:hmsCheshireAzurLane_delta:1> <lora:iuV35.uv1P:1> "
                        f"<lora:kanameMadoka_delta:1> <lora:minatoaqua_trSafe:1> <lora:necoStyleLora_v10:1> "
                        f"<lora:punishingGreyRaven_v10:1> <lora:shutenDoujiFateGO_shuten:1> "
                        f"<lora:stLouisLuxuriousWheels_v1:1> <lora:yaemikoTest.Yof9:1>")


def translate_to_english(text):
    """
    检测输入字符串是否有中文，如果有中文则调用Deepl翻译API将其翻译为英语，返回字符串
    :param text: 输入字符串
    :return: 翻译后的英文字符串
    """
    # 判断字符串是否包含中文字符
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            # 包含中文，调用Deepl翻译API进行翻译
            api_key = 'd4462d35-a54d-0caa-ff7d-097b3812fc92:fx'  # 请替换成你的Deepl API密钥
            translator = deepl.Translator(api_key)
            result = translator.translate_text(text, target_lang="EN-GB")
            return result.text

    # 不包含中文，直接返回原字符串
    return text


@drawer.handle()
async def telegram_task(event: TelegramEvent, bot: TelegramBot, args: Namespace = ShellCommandArgs()):
    logger.info(f"args: {args}")
    id_ = event.get_user_id()
    logger.info(f"start task for id {id_}")

    seed = args.seed
    scale = args.scale
    steps = args.steps
    size = args.size
    prompt = args.prompt
    uc = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
    sampler = args.sampler
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
    if sampler is None or sampler == "":
        sampler = "DPM++ 2M Karras"

    try:
        size = size.split("x")
    except AttributeError:
        size = [512, 512]
    size = [int(size[0]), int(size[1])]
    if size[0] > 2048 or size[1] > 2048:
        drawer.finish("图片尺寸过大，请重新输入！")
        return

    if prompt is None or prompt == "":
        max_num_tags = min(len(tag_sets), 30)  # 设置允许的最大随机数为50，或者tag_sets的长度，以防止出现超出范围的随机数
        num_tags = random.randint(1, max_num_tags)  # 生成一个1到max_num_tags之间的随机数，作为抽取的tag数量
        selected_tags = random.sample(tag_sets, num_tags)  # 从tag_sets中随机抽取num_tags个tag
        prompt = ", ".join(selected_tags)  # 将选中的tag拼接成英文逗号分隔的字符串
        num_loras = random.randint(0, 2)
        selected_lora = random.sample(lora_list, num_loras)
        final_lora = []
        for lora in selected_lora:
            final_lora.append(lora + str(round(random.uniform(0.1, 0.9), 1)) + ">")
        lora_str = ", ".join(final_lora)
        prompt = prompt + ", " + lora_str
        await drawer.send(f"因为您没有指定prompt, prompt随机指定为{prompt}")

    prompt = translate_to_english(prompt)

    await drawer.send("正在生成图片，请稍等...")
    logger.info(
        Fore.LIGHTYELLOW_EX +
        f"\n开始生成{event.get_user_id}的图片："
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
        seed=seed,
        sampler=sampler,
        config=config,
        hires=args.hires
    )

    if data[0] is False:
        logger.error(Fore.LIGHTRED_EX + f"后端请求失败：{data[1]}")
        await drawer.finish("生成失败！")

    image = b64decode(data[1])
    msg = File.photo(image)
    try:
        (await drawer.send(msg))
    except TelegramActionFailed:
        logger.warning(Fore.LIGHTYELLOW_EX + f"可能被风控，请稍后再试！")


@drawer.handle()
async def drawer_task(event: MessageEvent, bot: Bot, args: Namespace = ShellCommandArgs()):
    logger.info(f"args: {args}")
    id_ = event.get_user_id()
    logger.info(f"start task for id {id_}")

    if id_.strip() == "3388108457" or "3388108457" in id_:
        await drawer.finish("江西人也好意思用机器人？？？", at_sender=True)
        return
    else:
        logger.info(f"user_id:{id_}")

    seed = args.seed
    scale = args.scale
    steps = args.steps
    size = args.size
    prompt = args.prompt
    uc = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
    sampler = args.sampler
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
    if sampler is None or sampler == "":
        sampler = "DPM++ 2M Karras"

    try:
        size = size.split("x")
    except AttributeError:
        size = [512, 512]
    size = [int(size[0]), int(size[1])]
    if size[0] > 2048 or size[1] > 2048:
        drawer.finish("图片尺寸过大，请重新输入！", at_sender=True)
        return

    if prompt is None or prompt == "":
        max_num_tags = min(len(tag_sets), 30)  # 设置允许的最大随机数为50，或者tag_sets的长度，以防止出现超出范围的随机数
        num_tags = random.randint(1, max_num_tags)  # 生成一个1到max_num_tags之间的随机数，作为抽取的tag数量
        selected_tags = random.sample(tag_sets, num_tags)  # 从tag_sets中随机抽取num_tags个tag
        prompt = ", ".join(selected_tags)  # 将选中的tag拼接成英文逗号分隔的字符串
        num_loras = random.randint(0, 2)
        selected_lora = random.sample(lora_list, num_loras)
        final_lora = []
        for lora in selected_lora:
            final_lora.append(lora + str(round(random.uniform(0.1, 0.9), 1)) + ">")
        lora_str = ", ".join(final_lora)
        prompt = prompt + ", " + lora_str
        await drawer.send(f"因为您没有指定prompt, prompt随机指定为{prompt}", at_sender=True)

    prompt = translate_to_english(prompt)

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
        seed=seed,
        sampler=sampler,
        config=config,
        hires=args.hires
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
