# 思维模型小红书制作

将已经定稿的思维模型文章制作成小红书正文、系列标题和七张分享图的 Codex Skill。支持单篇和批量制作，每个模型编号独立审核、制图、验收并打包。

七张「049 可证伪性」图片随包提供，作为逐页对应的构图母版。新图保留母版的版式与视觉语言，内容换成本次文章，不沿用旧主题的文字、案例和数字。

<p>
  <img src="assets/masters/049-p01.jpg" width="260" alt="049 母版第1页：封面">
  <img src="assets/masters/049-p06.jpg" width="260" alt="049 母版第6页：行动方法">
</p>

## 使用方式

先提供一篇或多篇完整终稿文件，支持 PDF、Word、Markdown 和 TXT，再明确要求开始。例如：

```text
思维模型070已经定稿，开始小红书制作。
```

```text
使用 $thinking-model-xiaohongshu：这几篇都已定稿，开始小红书制作。
```

上传文件与启动制作可以在同一条消息中完成，也可以分两次提交。**仅上传文件、说“已定稿”或输入编号，不会启动制作。**

启动后自动完成正文与标题、七页文案、审核修订、七图生成、检查和打包，不需要逐页确认。也可以明确限定为只写正文、只审稿或只制作图片。每篇最终交付一个独立 ZIP，多篇按编号分别提供下载链接。

默认使用本次提供的终稿，不自动从公众号取稿，也不自动上传或发布到小红书。

## 交付内容

完整制作包包含：

- `title.txt`、`titles.txt`：推荐标题和默认5个候选标题。
- `body.txt`：可复制的小红书正文，含 emoji 和文末话题。
- `seven-pages-final.md`：七页定稿文案。
- `images/`：七张独立图片，默认目标为1080×1440、3:4，实际尺寸需检查。
- `review-notes.md`、`manifest.json`、`generation-records.json`：审核、文件与版本清单、生成及验收记录。

单独要求某个环节时，只交付对应内容。缺页或未完成检查的成果不会标为完整制作包。

## 运行条件

完整流程需要：

- 支持本地文件读写、图片查看和相应稿件读取能力的 Codex 环境。
- Python 3.9及以上；图片检查另需 Pillow，可在所用 Python 环境中运行 `python3 -m pip install Pillow` 安装。
- 可读取的 `humanizer-zh` Skill，用于正文优化；本仓库不包含该依赖。
- 可用的内置 `imagegen` 技能与工具，且生成时支持传入参考图。仅有文本对话能力无法完成七图生成。

依赖按制作阶段检查。缺少能力时记录未完成环节，不冒称完成，也不自动切换到付费 API。

## 安装

使用 Git 安装到 Codex 的技能目录。以下命令发现同名目录时会停止，不覆盖已有版本：

```sh
xhs_skill_dir="${CODEX_HOME:-$HOME/.codex}/skills/thinking-model-xiaohongshu"
if [ -e "$xhs_skill_dir" ]; then
  echo "目录已存在，请先检查已有版本：$xhs_skill_dir"
else
  mkdir -p "$(dirname "$xhs_skill_dir")"
  git clone https://github.com/sushengs-creator/thinking-model-xiaohongshu.git "$xhs_skill_dir"
fi
```

也可以在 [GitHub 仓库](https://github.com/sushengs-creator/thinking-model-xiaohongshu) 点击 **Code → Download ZIP**，解压后将仓库根目录命名为 `thinking-model-xiaohongshu`，放入 `${CODEX_HOME:-$HOME/.codex}/skills/` 对应的实际目录。已有同名目录时先检查，勿直接覆盖。

安装后的 `thinking-model-xiaohongshu/` 应直接包含 `SKILL.md`、`assets/`、`references/`、`scripts/` 和 `agents/`，不要再多套一层文件夹。

## 定制署名

新图默认保留「鬼子不言」作者戳。其他使用者请在启动时明确指定自己的署名，例如：

```text
思维模型070已经定稿，开始小红书制作。新图作者戳使用“小林 / 制作 / 2026”。
```

该要求用于本次生成的新图；包内七张049母版保留原样。未指定署名时，仍使用默认作者戳，年份按本次制作日期填写。

## 文件说明与许可

执行入口见 [SKILL.md](SKILL.md)，详细文案、视觉和交付规范位于 `references/`，检查脚本位于 `scripts/`。历史提示词用于追溯，不覆盖当前规则或使用者的明确要求。

许可见 [LICENSE](LICENSE)。
