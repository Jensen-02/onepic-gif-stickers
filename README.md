# 一图成套 · GIF 表情包工坊

**给 Codex 一张主图、一个主题，做出一套能单独发送的 GIF 表情包。**

OnePic GIF Stickers 是为 Codex 设计的 Skill。它使用 Codex 内置图片生成能力设计角色和连续姿势，再用本地工具完成字幕、GIF 编码与检查。你描述用途，Codex 负责文案、表情、动作和道具。

> 用这张图做一套不想上班的表情包。

默认继续制作到独立动图，不在角色样张或静态合集处结束。项目名称为 `onepic-gif-stickers`，技能调用名保留为 **`$theme-gif-stickers`**。

## 试作示例

| 嗨喵 | 开饭啦 | 晚安喵 |
| :---: | :---: | :---: |
| <img src="docs/examples/cat-hello.gif" width="200" alt="猫咪打招呼动图"> | <img src="docs/examples/cat-dinner.gif" width="200" alt="猫咪开饭动图"> | <img src="docs/examples/cat-goodnight.gif" width="200" alt="猫咪晚安动图"> |

▲ 已生成的小猫试作 GIF，可直接观察动作与循环。样例展示不代表所有角色、风格和动作都已通过完整实测。

## 能做什么

- **从主题设计整套表达**：日常聊天、上班摸鱼、吃喝玩乐等，默认 12 张，可指定数量。
- **文案和动作一起设计**：“收到”可以点头回应，“不想上班”可以推开鼠标；不靠换字幕重复同一张脸。
- **轻动作优先**：支持挥手、扶眼镜、抱靠垫、推杯子等，也可以明确要求大动作。
- **角色一致，表情各不相同**：保留脸型、发型、眼镜、宠物花色，按每条含义变化神态与姿势。
- **37 种画风参考**：Q版、手绘涂鸦、气球扭塑、发条铁皮、赛博朋克等。主图决定角色是谁，风格样图只提供画法。
- **支持局部修改**：关掉文字、只改一张、追加几张，不要求重做整套。

## 安装到 Codex

把下面这句话发给 Codex：

```text
请从 https://github.com/Jensen-02/onepic-gif-stickers 安装
skills/theme-gif-stickers 这个技能到我的 Codex 用户技能目录。
如果已经安装，请先比较差异，再同步更新，不要创建重复技能。
```

也可从 [Releases](https://github.com/Jensen-02/onepic-gif-stickers/releases) 下载技能 ZIP，解压后将整个 `theme-gif-stickers` 文件夹放入 `$CODEX_HOME/skills/`；未设置 `CODEX_HOME` 时使用用户目录下的 `.codex/skills/`。

安装后在新聊天里选择 `$theme-gif-stickers` 并上传主图。若没有显示，先刷新或重新打开 Codex。

### 需要的环境

| 项目 | 用途 |
| --- | --- |
| 可使用内置图片生成工具的 Codex | 读取参考图，生成角色和动作姿势；无需为本技能另配图片 API |
| Python 3.10+、Pillow 13.x | 字幕、GIF 合成、文件检查；由 Codex 按环境检查和准备 |
| 本机可用的中文字体 | 有字版字幕；项目不捆绑商业字体 |

如果当前 Codex 会话未开放图片生成或额度不足，Skill 无法自行开通。可选补帧工具仅在确有需要且环境可用时使用；本项目不内置补帧模型，也不默认安装大型模型或切换付费视频服务。

## 怎么用

上传图片，再发一句话：

```text
$theme-gif-stickers 根据这张照片，把我做成Q版，做8张日常聊天表情包。
```

```text
$theme-gif-stickers 用我家猫这张图，做6张吃喝玩乐的表情包，不要字。
```

```text
$theme-gif-stickers 用这张角色图，做一套不想上班的表情包，轻动作。
```

需要调整时直接说：

```text
第3张改成把咖啡杯推远，其他不变。
再补4张周末主题，沿用这个形象和画风。
先给我看文案，确认后再生成。
```

不必提供帧数、补帧参数或循环秒数。默认 512×512 白底、顶部 2–6 字短句；关闭文字后重新利用画面空间。构图以半身或大头小身体为主。

## 制作和交付

**主图＋主题 → 文案与动作设计 → 连续姿势 → GIF 合成 → 快速检查 → 独立 GIF＋动态预览＋ZIP**

默认检查文件可用性、数量、字幕、角色动作和循环。发现跳变、重影或接触错误时，才展开问题片段做逐帧排查。检查本身不调用图片生成；确认存在视觉问题后才局部重生成，默认每条最多两轮修复。

合成器输出的 `candidates.zip` 是候选包。Codex 完成相应检查后再整理交付包；未能观看正常播放时应标注待动态验收，不冒称完整通过。

## 画风参考

| Q版 | 手绘涂鸦 | 气球扭塑 | 发条铁皮 |
| :---: | :---: | :---: | :---: |
| <img src="skills/theme-gif-stickers/assets/styles/S02-chibi.png" width="160" alt="Q版参考"> | <img src="skills/theme-gif-stickers/assets/styles/S10-doodle.png" width="160" alt="手绘参考"> | <img src="skills/theme-gif-stickers/assets/styles/S27-balloon-sculpture.png" width="160" alt="气球参考"> | <img src="skills/theme-gif-stickers/assets/styles/S29-tin-clockwork.png" width="160" alt="铁皮参考"> |

▲ 这些是静态画风样图，不是要替换成的固定人物。可指定编号或名称，例如“用 S10 手绘涂鸦风格”。

[浏览全部 37 种画风](docs/styles.md) · [角色与风格参考的分工](skills/theme-gif-stickers/references/style-library.md)

## 当前状态

当前为 **0.3.0 预览版**：具备 Codex 工作流、37 张风格参考、本地合成器和自动测试。已有真实角色试作，跨新会话的一图一句话完整回归、不同动作的正常播放验收仍需持续实测。

默认目标是运动连续，而不是承诺每次生成零缺陷。增加帧数不会自动解决身份漂移或错误动作。具体生成时间和额度消耗取决于数量、动作复杂度以及是否需要修复，项目不提供未经测量的固定耗时承诺。

## 开发与验证

```bash
git clone https://github.com/Jensen-02/onepic-gif-stickers.git
cd onepic-gif-stickers
python -m pip install -r skills/theme-gif-stickers/requirements.txt
python -m unittest discover -s skills/theme-gif-stickers/tests -v
```

测试需要本机存在字体；无默认字体时设置 `TEST_FONT` 指向可用 TTF/TTC。自动测试检查编码与文件行为，不替代动画视觉验收。

已有独立姿势帧时可调用合成器：

```bash
python skills/theme-gif-stickers/scripts/compose_pack.py --manifest /path/to/render.json --output /path/to/new-output
```

需要详细逐帧图片时加 `--review-frames`。一张普通照片不是这个脚本的直接动画输入，角色动作由 Codex 内置图片生成工具制作。

[渲染清单格式](skills/theme-gif-stickers/references/job-format.md) · [验收方式](skills/theme-gif-stickers/references/quality.md) · [贡献指南](CONTRIBUTING.md) · [更新记录](CHANGELOG.md)

## 许可与作者

[MIT License](LICENSE)。代码、文档及本仓库提供的样例按该许可分发；第三方运行依赖各自遵循其许可证。许可不授予样图人物的姓名、肖像或商标使用权；请使用自己有权使用的角色素材。

由 **椰子的AI小岛** 维护。欢迎通过 [Issues](https://github.com/Jensen-02/onepic-gif-stickers/issues) 提交可复现的问题或试用反馈；不要上传密钥、私人照片或未经允许公开的聊天记录。
