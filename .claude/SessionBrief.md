# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标与最新状态
1. **TASK-STUDIO-021：启动性能、随机配色与独立游戏启动器（2026-11-15）**
   - PyInstaller 从 --onefile 切换为 --onedir，产物位于 dist/KOF97ModStudio/。桌面 EXE 约 6.47 MB，目录依赖合计约 56.4 MB；根目录旧单文件版已从 Git 基线恢复，作为回退副本。launch_mod_studio.bat 优先启动 onedir 版。
   - 冻结态路径解析已修正：从 EXE 目录向上查找同时含 src/ 和 sandbox/WinKawaks.exe 的工作区根，避免把 dist/KOF97ModStudio 当作项目根。
   - “全部随机”现在为 36 位角色同时随机分配精选服装主题及特效主题；VFX 随机池排除 classic 与 sync_skin，配置由后端自动保存，需打包 ROM 后在游戏里生效。
   - KOF97BridgeApi.launch_game_sync() 统一执行缺包时打包、启动沙盒 Kawaks 和内存补丁。Studio 按钮保留后台启动并显示“启动中”；KOF97GameLauncher.exe 通过复用 onedir 主程序文件生成，放在 dist/KOF97ModStudio/，以当前配置独立启动游戏，异常通过 Windows 消息框报告。
   - 本轮 onedir 构建成功；尚未实测独立启动器的实际 ROM 启动结果及完整冷启动耗时。用户要求本轮保存记忆、提交、push；提交仅包含本轮源文件与记忆/交接文档，不纳入既有 ROM 验证产生的配置、INI、截图和临时文件。
2. **冻结基线（严禁回退）**
   - 68000 补丁地址与大端 bswap16 处理、P1 0x0F0000 受击特效 Code Cave、P2 公共色板保护均维持既有已审基线。
   - 全员 36 名角色 20 款皮肤 OKLCH 染色算法及参数保持不变；技能 VFX 着色器与 25 个 RPC 契约保持兼容。
   - 原始 C:\Program Files (x86)\KOF97\roms 只读；ROM 解包与改写均在工作区副本中完成。

## 模块索引
- src/core/paths.py：源代码、单文件及 onedir 的根目录/配置/前端路径解析。
- src/studio/bridge_api.py：皮肤、特效、ROM 打包、沙盒模拟器启动 API。
- src/studio/kof97_webview_app.py：Studio 入口；按 EXE 文件名分派 KOF97GameLauncher.exe 的无界面启动模式。
- src/studio/web/index.html：Studio 前端及“全部随机”“开始游戏”交互。
- src/build/build_exe.py、BuildStudio.bat、launch_mod_studio.bat：onedir 构建及桌面入口。

## 关键限制与下一步
- 活跃 Python、批处理脚本保持纯英文/ASCII 规范；新增变量和注释仅用英文。
- 构建日志包含若干可选 NumPy/PyInstaller hook 警告，但构建成功；不要把构建成功表述为运行验证。
- **下一步**：检查本轮差异和暂存清单，提交并 push；后续需要实测 KOF97GameLauncher.exe 启动、错误提示和 ROM 加载。
