import json
from io import BytesIO
from re import findall

from PIL.Image import Image
from fake_useragent import UserAgent
from httpx import AsyncClient, ConnectTimeout
from .config import Config
from nonebot import logger


async def asyncDownloadFile(url, proxies=None, headers=None):
    if headers is None:
        headers = {"User-Agent": UserAgent().random}
    async with AsyncClient(headers=headers, proxies=proxies, timeout=None) as client:
        try:
            file = await client.get(url)
        except Exception as error:
            return False, error
        else:
            return True, file.content


def set_size(image):
    # 人类的本质就是复读机，这里应该可以用个什么算法，但是我太懒了
    img = Image.open(BytesIO(image))
    width, height = img.size

    if width == 512 or width < 512:
        width = 512
    elif width == 640:
        pass
    elif width == 768:
        pass
    elif width == 1024 or width > 1024:
        width = 1024
    elif 512 < width < 640:
        width1 = width - 512
        width2 = abs(width - 640)
        if width1 > width2:
            width = 640
        else:
            width = 512
    elif 640 < width < 768:
        width1 = width - 640
        width2 = abs(width - 768)
        if width1 > width2:
            width = 768
        else:
            width = 640
    elif 768 < width < 1024:
        width1 = width - 768
        width2 = abs(width - 1024)
        if width1 > width2:
            width = 1024
        else:
            width = 768

    if height <= 768:
        # 高为768的图片生成效果最好，高为512则很容易生异形
        height = 768
    elif height == 1024 or height > 1024:
        height = 1024
    elif 768 < height < 1024:
        height1 = height - 768
        height2 = abs(height - 1024)
        if height1 > height2:
            height = 1024
        else:
            height = 768

    return width, height


async def get_data(post_url, config, prompt, timeout,
                   img=None, mode=None, strength=None,
                   noise=None, size=None, uc=None,
                   scale=None, steps=None, seed=None, sampler=None, hires=None):
    data = {
        "width": size[0],
        "height": size[1],
        "batch_size": 1,
        "prompt": prompt,
        "sampler_name": sampler,
        "cfg-scale": scale,
        "seed": seed,
        "steps": steps,
        "negative_prompt": uc,
        "enable_hr": hires,
        "restore_faces": True,
        "hr_upscaler": "Latent"
    }

    headers = {
        "User-Agent": UserAgent().random
    }

    if config.stable_auth is not None:
        headers["Authorization"] = config.stable_auth
        logger.info("使用鉴权设置")

    async with AsyncClient(headers=headers, timeout=timeout) as client:
        try:
            logger.info(f"request api: {post_url}, payload:{data}")
            resp = await client.post(url=post_url, json=data)
        except ConnectTimeout:
            return False, "时间超过限制！"
        except Exception as error:
            return False, error
        info = resp.text

        # 获取错误
        if "images" not in info:
            return False, info

        # 获取返回的图片base64
        base64_img = json.loads(info)['images'][0]
        return True, base64_img
