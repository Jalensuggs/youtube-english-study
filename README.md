# youtube-english-study

一个支持 [Codex](https://developers.openai.com/codex/skills) 和 [Claude Code](https://claude.com/claude-code) 的 skill：给它一个 YouTube 链接，自动生成单文件的「英语精读本」HTML，双击就能在浏览器里学英语。

## 生成的页面有什么

- 英文字幕重新按完整句子排好，按场景分段，每段有中文导读
- 有用的短语、生词、口语俚语、文化点直接在原文里高亮，旁边是中文意思和用法提示
- 美式音标，点一下朗读（用设备自带的英语语音，可切慢速）
- 每句话带时间戳，点击跳到 YouTube 原视频对应位置听原声
- 三种模式：中英标注 / 遮住中文自测 / 纯英文；浅色、深色主题；手机可读
- 文末短语总表，可以给已掌握的打勾，进度存在浏览器里
- 字幕里的错字、品牌名会被更正并标出来

中文部分只有场景导读和短语释义，没有逐句翻译。

## 安装到 Codex

需要 Python 3.10+ 和 [yt-dlp](https://github.com/yt-dlp/yt-dlp)。生成页面不需要 API key。

```bash
git clone https://github.com/Jalensuggs/youtube-english-study.git
cd youtube-english-study
# 若尚未安装 yt-dlp，建议通过隔离环境安装：
python3 -m venv .venv
.venv/bin/python -m pip install yt-dlp
# macOS/Linux：把 yt-dlp 加入当前终端 PATH
export PATH="$PWD/.venv/bin:$PATH"
# Windows PowerShell 对应：$env:Path = "$PWD\.venv\Scripts;$env:Path"
python3 scripts/install_codex.py
```

默认安装到 `~/.agents/skills/youtube-english-study`，适用于本机的 Codex 任务。
也可仅安装到指定项目（云环境推荐）：

```bash
python3 scripts/install_codex.py --project /path/to/project
```

项目安装路径为 `<project>/.agents/skills/youtube-english-study`。重新打开 Codex 会话后使用。
安装器会完整复制脚本、模板与参考资料；重复执行会校验内容，存在不同文件时拒绝覆盖。
升级时先备份并移走旧安装目录，再重新安装。`yt-dlp` 必须在运行 Codex 的环境 PATH 中。

### 安装到 Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R youtube-english-study ~/.claude/skills/
```

## 使用

在 Codex 中说：

> $youtube-english-study 用这个视频学英语：https://www.youtube.com/watch?v=xxxxxxxxxxx

在 Claude Code 中也可直接说「英文学习 + YouTube 链接」。助手会下载字幕、划分场景、标注短语和音标，
校验后在当前目录生成 `<视频标题>-英语精读本.html`。也可以在指令中指定输出目录。

默认仅保存到本地。需要上传时，请明确说「把生成的页面上传到 owner/repository」。
上传需要 GitHub CLI（`gh`）以及目标仓库写权限；脚本支持 `--repo owner/repository`。
本次安装或上传 skill 代码不代表授权公开以后生成的视频字幕页面。

### Codex 云环境

当前任务已在隔离环境中，直接使用现有 checkout，无需新建 Git worktree。
字幕下载需要允许访问 `youtube.com`、`www.youtube.com`、`youtu.be`，以及 YouTube 返回的
字幕服务地址（可能包括 `*.youtube.com`、`*.googlevideo.com`、`*.ytimg.com`）。
上传另需 `github.com`、`api.github.com`。实际访问受限、视频无英文字幕或触发登录/限流时，
助手会报告具体原因，不能承诺每个视频都可下载。不要关闭 TLS 校验或在聊天中发送 cookie/token。

### 验证

```bash
python3 -m unittest discover -s tests -v
```

测试会安装 skill 到临时项目，检查重复安装及文件保护，并通过已安装的脚本完成
字幕解析、数据校验和 HTML 生成；已安装 Node.js 时也检查生成页面的 JavaScript 语法。
不需要网络或 GitHub 凭据。真实字幕下载需另用一个可访问的视频验证。

视频需要有英文字幕（官方字幕最好，自动字幕也行，但可能有识别错误）。

## 目录

| 路径 | 说明 |
|---|---|
| `youtube-english-study/SKILL.md` | skill 的工作流程 |
| `youtube-english-study/references/annotation-guide.md` | 场景、标注、音标的写作规范 |
| `youtube-english-study/scripts/` | `fetch.py` 取字幕，`check.py` 校验，`build.py` 生成页面，`drop.py` 去掉字幕杂质，`publish.py` 上传 |
| `youtube-english-study/assets/template.html` | 页面模板 |
| `pages/` | 生成的精读本页面 |

## 关于示例页和版权

`pages/` 里的页面是用 YouTube 上的视频生成的，例如 Volka English 的视频 [LTVk3yUb5Mg](https://www.youtube.com/watch?v=LTVk3yUb5Mg)。页面中的英文台词归各视频作者所有，仅作学习与功能演示。原作者或版权方如要求移除，请提 issue，会立即删除。

自己生成的页面请只用于个人学习，不要公开转载别人视频的台词。

## 许可证

代码和 skill 以 MIT 许可证发布，不包含 `pages/` 中的第三方台词。
