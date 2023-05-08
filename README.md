<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot_plugin_stable_diffusion_api

_✨ NoneBot AI画图插件 ✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/zmq175/nonebot_plugin_stable_diffusion_api.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot_plugin_stable_diffusion_api">
    <img src="https://img.shields.io/pypi/v/nonebot_plugin_stable_diffusion_api.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">

</div>

这是一个 nonebot2 版本的AI画图插件

## 📖 介绍

Nonebot2的AI画图插件

## 💿 安装

<details>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot_plugin_stable_diffusion_api

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot_plugin_stable_diffusion_api
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot_plugin_stable_diffusion_api
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot_plugin_stable_diffusion_api
</details>
<details>
<summary>conda</summary>

    conda install nonebot_plugin_stable_diffusion_api
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_stable_diffusion_api"]

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| stable_url | 是 | 无 | 绘图地址 |
| stable_auth | 否 | 无 | 是否需要加header进行认证 |

## 🎉 使用
### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| AI画图 | 群员 | 否 | 群聊/私聊 | 进行画图，-h, --help           show help message and exit --seed SEED --scale SCALE  --steps STEPS  --size SIZE  --prompt PROMPT  --negative NEGATIVE  --sampler SAMPLER  --hires, 目前支持的Lora模型列表如下： <lora:ArknightsChen5concept_10:1> <lora:ArknightsNian_20:1> <lora:AzumaSeren_v10:1> <lora:Bremerton (Kung Fu Cruiser) (Azur Lane):1> <lora:GawrGuraFlatisJustice:1> <lora:Lucy (Cyberpunk Edgerunners):1> <lora:Raiden Shogun:1> <lora:Rem_RE Zero:1> <lora:Shengren:1> <lora:YDLunaCos:1> <lora:YaeMikoRealisticGenshin:1> <lora:Yuefu:1> <lora:Yuta:1> <lora:aliceNikke_v30:1> <lora:arknightsTexas20the.uDnD:1> <lora:banbanbai:1> <lora:corruption_v1:1> <lora:godChineseGirl:1> <lora:hmsCheshireAzurLane_delta:1> <lora:iuV35.uv1P:1> <lora:kanameMadoka_delta:1> <lora:minatoaqua_trSafe:1> <lora:necoStyleLora_v10:1> <lora:punishingGreyRaven_v10:1> <lora:shutenDoujiFateGO_shuten:1> <lora:stLouisLuxuriousWheels_v1:1> <lora:yaemikoTest.Yof9:1> |
### 效果图
如果有效果图的话
