KOF97 Mod Studio 便携完整包

使用方法
1. 将整个压缩包解压至可写目录。建议使用英文目录，例如 D:\Games\KOF97。
2. 双击 KOF97GameLauncher.exe 启动当前魔改 ROM。
3. 双击 studio.exe 调整皮肤、特效和规则；修改后先点击“打包 ROM”，再开始游戏。
4. 保留整个目录结构，两个 EXE 共用 _internal，不能单独拷贝 EXE。

目录
roms\kof97.ZIP：未修改的原版 ROM，也是 Studio 的还原和生成基线。
roms\neogeo.zip：模拟器所需 BIOS。
output\roms\kof97pls.zip：按随包配置重新生成的魔改 ROM。
sandbox\：模拟器、按键设置及运行数据。
mod_studio_config.json：随包的魔改配置，Studio 会保存后续修改。
build\：ROM 工作缓存，可以删除；下次打包会从包内原版重新生成。
ThirdParty\：随本地模拟器取得的说明文档。
SHA256SUMS.txt：交付时的文件校验清单。游戏运行和配置修改会改变部分文件。
package-check.json：构建时冻结程序的 ROM 重打包和角色预览验证结果。

按键沿用当前项目设置。默认 1P 为 2 投币、1 开始、WASD 移动，
小键盘 1/2/3/5 对应 A/B/C/D。可在模拟器 Game > Redefine keys 中修改。

环境
面向 Windows x64。无需安装 Python；Studio 使用 Microsoft Edge WebView2
及 .NET Framework。若目标系统缺少这些运行时，需要另行安装；本包未内置离线安装器。
一键游戏启动器会调用随包模拟器并应用既有的运行时补丁。

分发说明
本包汇集了本地已有的第三方模拟器、原版 ROM 和 BIOS。
打包不授予这些内容的再分发许可。对外分发前，应确认相应权利或许可。
本包未附带原厂 ROM 或 BIOS 的再分发授权证明。
