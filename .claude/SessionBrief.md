# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标与最新状态
1. **TASK-STUDIO-022：便携完整包（2026-11-15）**
   - 用户要求模拟器、原版 ROM、魔改 ROM、Studio 与一键游戏 EXE 同包。产物为 dist/KOF97-Portable-20261115.zip。入口 studio.exe 与 KOF97GameLauncher.exe 共用 _internal/，必须整目录解压。
   - src/build/build_portable.py 按白名单装配模拟器、当前按键与配置、原版 roms/kof97.ZIP、roms/neogeo.zip，调用冻结程序生成 output/roms/kof97pls.zip，输出说明、校验清单和报告。没有纳入截图、录音、旧存档、源码或 Git 数据。
   - src/core/paths.py 优先按 portable-package.json 定位包根；ROM 工具统一从包内 roms/ 读取基线，便携包不回退宿主安装目录。开发环境仍兼容原安装路径。模拟器 INI 使用包内相对路径。
   - 冻结程序新增 --check-package，执行真正的 ROM 打包与角色预览并写 JSON；Studio 工具链自检直接调用内置函数，避免冻结环境尝试运行源码脚本。
2. **实测与边界**
   - onedir 重建成功，主 EXE 6,472,082 字节；包内及项目外带空格目录的冻结程序重打包、角色预览通过。
   - 项目外启动器拉起 WinKawaks 1.48，窗口标题 KOF97 Plus；从测试进程既有 ROM 指针读取 P1/P2，与包内 ZIP 的 1 MiB / 4 MiB 数据逐字节一致，两个运行时 NOP 补丁也已确认。
   - 项目外 Studio 可访问性内容确认前端加载、ROM 状态正常、36 名角色及保存的皮肤/VFX 配置恢复；截图连续两次超时，完整画面和对战未验证。
   - ROM/C-ROM 自检、9 项 VFX 回归与 diff 空白检查通过。未在缺少 WebView2/.NET 的干净机器测试，未内置离线运行时安装器。打包未建立第三方模拟器、ROM、BIOS 的再分发授权，未上传或公开发布。

## 冻结基线与约束
- TASK-STUDIO-021 的 onedir、随机皮肤/VFX、同步启动流程保留；根目录旧单文件 EXE 保留为回退，不是本次便携入口。
- 68000 大端 bswap16、P1 0x0F0000 Code Cave、公共色板保护与冻结染色算法未改；原始安装 ROM 只读。
- 活跃 Python/批处理变量与注释纯英文；保留用户既有配置、INI、截图、temp 修改。构建产物被 Git 忽略，本轮未提交或 push。

## 模块索引与下一步
- 路径：src/core/paths.py；构建：src/build/build_exe.py、build_portable.py；入口与自检：src/studio/kof97_webview_app.py、bridge_api.py；说明：Docs/Portable-Readme.txt。
- CRDocs 已记录 TASK-STUDIO-021 / 022，状态 READY_FOR_REVIEW，待 Argon 独立核对；后续补充画面、对战和干净 Windows 验收。PlanDocs 当前 IDLE，无进行中方向讨论。
