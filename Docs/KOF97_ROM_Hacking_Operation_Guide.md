# 拳皇97（KOF 97）ROM 逆向魔改实操与参数配置手册

本手册详细记录了《拳皇97》（基于风云再起版 `kof97pls`）逆向魔改工程的**工具链使用方法**、**核心参数修改指南**、**68000 汇编与调色板定制实操**以及**自动化验证流程**。

---

## 目录
1. [项目结构与安全隔离架构](#1-项目结构与安全隔离架构)
2. [环境准备与快速上手](#2-环境准备与快速上手)
3. [核心命令行工具使用指南 (`rom_tool.py` / `crom_tool.py`)](#3-核心命令行工具使用指南)
4. [核心参数修改与实操指南](#4-核心参数修改与实操指南)
   - [4.1 P-ROM 战斗防御参数定制（免破防、免眩晕、伤害减半/倍率/无敌）](#41-p-rom-战斗防御参数定制)
   - [4.2 P2-ROM 角色调色板与皮肤配色修改（八神庵黑金配色实操）](#42-p2-rom-角色调色板与皮肤配色修改)
   - [4.3 C-ROM 角色与特效图像瓦片重绘与回写导入](#43-c-rom-角色与特效图像瓦片重绘与回写导入)
5. [WinKawaks 沙盒联调与自动化验证](#5-winkawaks-沙盒联调与自动化验证)
6. [常见问题排查与工程红线约束](#6-常见问题排查与工程红线约束)

---

## 1. 项目结构与安全隔离架构

```text
Fighter97/
├── Docs/                  # 架构设计、逆向分析与实操文档
├── PlanDocs/              # 方案讨论与收口交接区（双角色协作）
├── CRDocs/                # 实施与审查代码交接区（双角色协作）
├── tools/                 # 核心自动化工具链
│   ├── rom_tool.py        # P-ROM/S-ROM 处理、调色板注入、打包与模拟器自动化联调
│   └── crom_tool.py       # C-ROM 4bpp 图像瓦片四象限解构、全量解交错与 PNG 导出/导入
├── build/                 # 中间构建产物（严禁直接提交大二进制）
│   ├── unpacked/          # 解包后的 68000 大端格式二进制（p1_be.bin, p2_be.bin, s1.bin）
│   └── crom_unpacked/     # C-ROM 解交错流 (.spr) 与重构 ROM
├── output/roms/           # 最终打包生成的交付物
│   └── kof97pls.zip       # 定制魔改版 ROM（WinKawaks 优先加载）
└── sandbox/               # 隔离运行沙盒
    ├── WinKawaks.ini      # 双路径加载配置（RomPath1=output, RomPath2=原生资产）
    ├── launch_sandbox.bat # 沙盒启动脚本
    └── capture/           # 自动化实机运行截图存盘目录
```

> [!IMPORTANT]
> **原生目录安全隔离红线**：
> 原生游戏目录 `C:\Program Files (x86)\KOF97\roms` 保持 100% 绝对只读。所有解包、Patch 和重打包均在工作区内完成，WinKawaks 通过配置：
> - `RomPath1=..\output\roms`（优先加载修改后的 `232-p1p.bin`、`232-p2p.bin`）
> - `RomPath2=C:\Program Files (x86)\KOF97\roms`（只读共享 40MB 原版 C-ROM、12MB V-ROM 音频及 BIOS）
> 既避免重复复制数十兆大文件，又杜绝了破坏原生资产的风险。

---

## 2. 环境准备与快速上手

### 2.1 依赖环境
- **Python**: 3.8+（64 位或 32 位均可）
- **依赖库**:
  ```bash
  pip install pillow
  ```
  *(注：`ctypes`, `struct`, `binascii`, `hashlib`, `zipfile` 均为 Python 标准库)*

### 2.2 全局自检（验证工具链健康度）
在项目根目录下执行：
```bash
python tools/rom_tool.py self-test
```
若全部显示 `[PASS]`，则说明：
1. Motorola 68000 字大端字节交换（`bswap16`）双向无损；
2. Neo-Geo `LSPC2-A2` 16-bit 调色板非线性 RGB 编解码双向无损；
3. Neo-Geo MVS 16x16 4bpp 四象限瓦片编解码与实机硬件数据 100% bit-exact。

---

## 3. 核心命令行工具使用指南

[`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py) 提供了统一的 CLI 接口，常用命令如下：

| 任务分类 | 子命令 | 说明 |
| :--- | :--- | :--- |
| **基础流水线** | `unpack` | 从原生 `kof97.ZIP` 解包 `P1`, `P2`, `S1` 并转为 68K 大端序存入 `build/unpacked/` |
| | `pack` | 将 `build/unpacked/` 中的二进制转回磁盘字序并打包为 `output/roms/kof97pls.zip` |
| | `build-baseline` | 一键从原生 ROM 构建官方原版风云再起包 |
| **防御与功能补丁** | `build-defense` | 应用免破防、免眩晕与受创减半补丁并打包 |
| | `verify-defense` | 启动沙盒模拟器，自动选人进入对战并动态断言 HP/防御槽/眩晕槽 |
| **调色板换肤** | `build-palette` | 应用八神庵专属黑金调色板与金发立绘并打包 |
| | `verify-palette` | 启动沙盒自动进入角色选择（光标移至八神庵）、确认首发、截屏与战斗断言 |
| **C-ROM 图像瓦片** | `crom-deinterleave`| 解交错 40MB 全量 6 颗 C-ROM 为 `.spr` 二进制瓦片流 |
| | `crom-interleave` | 将 `.spr` 瓦片流重新交错复原为 6 颗标准 C-ROM 二进制文件 |
| | `crom-export-tile` | 导出指定编号的 16x16 单瓦片为 PNG 图片 |
| | `crom-export-sheet`| 将连续多个瓦片导出为拼合的瓦片图集（Tile Sheet）PNG |
| | `crom-import-tile` | 将编辑后的 16x16 PNG 瓦片回写导入至指定 C-ROM 二进制 |

---

## 4. 核心参数修改与实操指南

### 4.1 P-ROM 战斗防御参数定制

全部战斗逻辑位于 `build/unpacked/p1_be.bin`（Motorola 68000 大端 1MB 逻辑空间）。

#### 4.1.1 免破防（Guard Crush Immunity）
* **逻辑地址**：`0x01397E`
* **原版指令**：`SUB.W D0, $013E(A4)`（机器码：`91 6C 01 3E`）
  * 说明：`A4` 是角色结构体指针，`$013E(A4)` 是当前破防槽计数（满值 `0x0067` = 103 点）。原版在格挡受击时扣减 `D0` 点。
* **修改方案**：
  * **完全免破防**：替换为 4 字节空操作 `NOP; NOP`（机器码：`4E 71 4E 71`）。
  * **恢复原版扣除**：恢复为 `91 6C 01 3E`。

#### 4.1.2 免眩晕（Dizzy/Stun Immunity）
* **逻辑地址**：`0x0139A4`
* **原版指令**：`SUB.W D0, $0146(A4)`（机器码：`91 6C 01 46`）
  * 说明：`$0146(A4)` 是角色眩晕槽计数（满值 `0x0067` = 103 点）。原版在连续被击中时扣减 `D0` 点。
* **修改方案**：
  * **完全免眩晕**：替换为 4 字节空操作 `NOP; NOP`（机器码：`4E 71 4E 71`）。
  * **恢复原版扣除**：恢复为 `91 6C 01 46`。

#### 4.1.3 受创减半 / 自定义伤害倍率 / 无敌模式
* **切入跳板**：`0x01394A`
  * 原版指令：`ADD.W D0, $013A(A4)`（机器码：`D1 6C 01 3A`，将掉血量累加至红血/虚血动画槽）
  * 替换指令：`JSR ($0300).W`（机器码：`4E B8 03 00`，短绝对寻址跳转到安全空洞）
* **安全注入区（Code Cave）**：`0x000300`
  * 原版在 `0x000194..0x000800`（1,644 字节）全为 `0xFF`，属于未使用的安全注入区。

不同伤害模式在 `0x000300` 处的机器码编写方式：

| 模式 | 汇编逻辑 | 机器码 (Hex) | 效果说明 |
| :--- | :--- | :--- | :--- |
| **受创减半（当前默认）** | `LSR.W #1, D0`<br>`ADD.W D0, $013A(A4)`<br>`RTS` | `E248D16C013A4E75` | 逻辑右移 1 位，掉血量除以 2（等效双倍生命） |
| **受创减为 1/4** | `LSR.W #2, D0`<br>`ADD.W D0, $013A(A4)`<br>`RTS` | `E448D16C013A4E75` | 逻辑右移 2 位，掉血量除以 4（等效四倍生命） |
| **受创减为 1/8** | `LSR.W #3, D0`<br>`ADD.W D0, $013A(A4)`<br>`RTS` | `E648D16C013A4E75` | 逻辑右移 3 位，掉血量除以 8 |
| **受创翻倍 (地狱模式)** | `LSL.W #1, D0`<br>`ADD.W D0, $013A(A4)`<br>`RTS` | `E348D16C013A4E75` | 逻辑左移 1 位，受到伤害乘以 2 |
| **完全无敌 (0 伤害)** | `CLR.W D0`<br>`ADD.W D0, $013A(A4)`<br>`RTS` | `4240D16C013A4E75` | 将掉血量清零，受击不扣实血亦不产生红血 |

> [!TIP]
> **代码生效步骤**：
> 修改 `tools/rom_tool.py` 中 `build_defense_patch()` 对应的十六进制字符串，然后执行：
> ```bash
> python tools/rom_tool.py build-defense
> ```
> 工具会自动重新打包并刷新 `output/roms/kof97pls.zip`。

---

### 4.2 P2-ROM 角色调色板与皮肤配色修改

#### 4.2.1 Neo-Geo `LSPC2-A2` 16-bit 调色板颜色格式
Neo-Geo 彩色寄存器采用非线性排列的 16 位字存储一个颜色（5-bit RGB + 暗色位）：

```text
 15  14  13  12  11  10   9   8   7   6   5   4   3   2   1   0
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
| D | R0| G0| B0| R4| R3| R2| R1| G4| G3| G2| G1| B4| B3| B2| B1|
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
```
* **Bit 15 (`D`)**：Dark 位，通常为 `0`；
* **Bit 14 (`R0`)**、**Bit 13 (`G0`)**、**Bit 12 (`B0`)**：红/绿/蓝通道最低有效位（LSB）；
* **Bits 11..8 (`R4..R1`)**：红色高 4 位；
* **Bits 7..4 (`G4..G1`)**：绿色高 4 位；
* **Bits 3..0 (`B4..B1`)**：蓝色高 4 位。

#### 4.2.2 调色板换算辅助代码
在 Python 中可直接调用 `tools/rom_tool.py` 内部函数：
```python
from tools.rom_tool import encode_lspc2, decode_lspc2

# 将 8-bit RGB (#FFDE3A) 换算为 5-bit RGB 并编码为 16-bit 字:
# R=255 -> 31, G=222 -> 27, B=58 -> 7
color_word = encode_lspc2(31, 27, 7, dark=0)
print(f"Hex: 0x{color_word:04X}")  # 输出 0x7FD3

# 反向解码 16-bit 字为 5-bit RGB:
r5, g5, b5, dark = decode_lspc2(0x7FD3)
print(f"R={r5}, G={g5}, B={b5}, Dark={dark}")  # (31, 27, 7, 0)
```

#### 4.2.3 八神庵（`CharID=0x1B`）主调色板结构分解
八神庵 A 键主调色板位于 `build/unpacked/p2_be.bin` 物理偏移 **`0x2DF7F0`**（占用 32 字节 / 16 个字）：

| 序号 | 偏移 | 原版数据 | 当前“黑金”配置 | 颜色名称 | 5-bit RGB | 对应身体部位 |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **#00** | `+0x00` | `0x07C0` | `0x07C0` | 控制头 | - | **调色板 ID（不可改动）** |
| **#01** | `+0x02` | `0x4FFB` | `0x4FFB` | 肤色高光 | `(31, 30, 22)` | 面部/手部高光 |
| **#02** | `+0x04` | `0x0FC8` | `0x0FC8` | 肤色主色 | `(30, 24, 16)` | 面部/胸膛主肤色 |
| **#03** | `+0x06` | `0x5E95` | `0x5E95` | 肤色阴影 | `(29, 18, 11)` | 面部阴影 |
| **#04** | `+0x08` | `0x1B52` | `0x1B52` | 肤色深阴影 | `(22, 10, 5)` | 肌肉轮廓深阴影 |
| **#05** | `+0x0A` | `0x1FFF` | `0x0333` | 衬衣高光 | `(6, 6, 6)` | 内衬黑灰过渡 |
| **#06** | `+0x0C` | `0x6BBC` | `0x7111` | 衬衣主色 | `(3, 3, 3)` | 内部深灰衬衣 |
| **#07** | `+0x0E` | `0x2778` | `0x7000` | 衬衣阴影 | `(1, 1, 1)` | 内部纯黑衬衣底色 |
| **#08** | `+0x10` | `0x6D32` | `0x7FD3` | 黄金高光 | `(31, 27, 7)` | **璀璨亮金头发/金裤高光** |
| **#09** | `+0x12` | `0x6A21` | `0x7DA1` | 黄金主色 | `(27, 21, 3)` | **纯正黄金头发/金裤主色** |
| **#10** | `+0x14` | `0x7710` | `0x1A70` | 黄金阴影 | `(20, 14, 1)` | **青铜暗金头发/金裤阴影** |
| **#11** | `+0x16` | `0x4400` | `0x0640` | 黄金深底 | `(12, 8, 0)` | **深沉暗铜头发/金裤轮廓** |
| **#12** | `+0x18` | `0x7334` | `0x1222` | 风衣反光 | `(4, 4, 5)` | **暗夜黑风衣折角反光** |
| **#13** | `+0x1A` | `0x7223` | `0x1111` | 风衣主色 | `(2, 2, 3)` | **黑曜石风衣大身主色** |
| **#14** | `+0x1C` | `0x7112` | `0x6001` | 风衣阴影 | `(1, 1, 2)` | **风衣褶皱极深阴影** |
| **#15** | `+0x1E` | `0x1000` | `0x0000` | 风衣勾边 | `(0, 0, 0)` | **风衣外部纯黑勾边** |

#### 4.2.4 选人与立绘头像板同步修改
选人界面与顶部血条 HUD 使用了独立的头像调色板：
- `0x2DF990`（PalID `0x07CD`，大立绘头像板）：Words #08, #10, #11, #15 对应发色；
- `0x2DF9B0`（PalID `0x07CE`，中立绘头像板）：Words #07, #08, #09 对应发色；
- `0x2DF9D0`（PalID `0x07CF`，HUD 小头像板）：Words #06, #07, #08, #14 对应发色。

在 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py) 中的 `build_palette_patch()` 函数中直接替换对应的字，然后执行：
```bash
python tools/rom_tool.py build-palette
```
即可将新配色写入并刷新 ROM。

---

### 4.3 C-ROM 角色与特效图像瓦片重绘与回写导入

#### 4.3.1 导出指定瓦片为 PNG
若需查看或重绘某个 16x16 瓦片（例如导出 `c1_c2` 对中的第 10 号瓦片）：
```bash
python tools/rom_tool.py crom-export-tile --pair c1_c2 --tile 10 --output sandbox/capture/my_tile.png
```
支持的 `--pair` 包括：
- `c1_c2`: 对应 `KOF97_C1.ROM` + `KOF97_C2.ROM` (131,072 个瓦片)
- `c3_c4`: 对应 `KOF97_C3.ROM` + `KOF97_C4.ROM` (131,072 个瓦片)
- `c5_c6`: 对应 `KOF97_C5.ROM` + `KOF97_C6.ROM` (65,536 个瓦片)

#### 4.3.2 批量导出瓦片图集（Tile Sheet）
将连续多个瓦片拼合渲染为一张大图方便快速检索角色帧：
```bash
python tools/rom_tool.py crom-export-sheet --pair c1_c2 --start 0 --count 256 --cols 16 --output sandbox/capture/sheet_256.png
```
这将在 `sandbox/capture/` 生成一张 256x256 像素（16x16 列）的连续瓦片排布图。

#### 4.3.3 修改并回写瓦片（导入至 ROM）
1. 在 Photoshop、Aseprite 或 GIMP 中编辑导出的 16x16 PNG 图片（确保保存为索引色，最多 16 种颜色）；
2. 使用 `crom-import-tile` 命令回写至解包后的 C-ROM 二进制文件：
   ```bash
   python tools/rom_tool.py crom-import-tile --image sandbox/capture/my_tile_edited.png --odd-rom build/crom_unpacked/rebuilt/KOF97_C1.ROM --even-rom build/crom_unpacked/rebuilt/KOF97_C2.ROM --tile 10
   ```
3. 工具会自动完成四象限拆分与位平面编码，无损写回。

---

## 5. WinKawaks 沙盒联调与自动化验证

本工程深度封装了 Windows API（通过 `ctypes`），支持**无须人手干预的端到端自动化模拟器对战与截图断言**：

### 5.1 自动化验证命令
- **全流程调色板实机测试**：
  ```bash
  python tools/rom_tool.py verify-palette
  ```
  *自动完成*：启动沙盒 Kawaks $\rightarrow$ 跳过片头 $\rightarrow$ 进入选人 $\rightarrow$ 精确摇杆定位至八神庵（`Right x 3, Down x 3`） $\rightarrow$ 截取选人金发立绘 $\rightarrow$ A 键选择八神庵并设为首发 $\rightarrow$ 进入 Round 1 战斗姿态 $\rightarrow$ 截取战斗画面并提取 Work RAM 断言血量/防御槽状态。

- **全流程防御特性实机测试**：
  ```bash
  python tools/rom_tool.py verify-defense
  ```
  *自动完成*：启动沙盒 $\rightarrow$ 进入对战 $\rightarrow$ 驱动 1P/2P 连续攻击与格挡 $\rightarrow$ 读取 `0x00712688` 处 Work RAM $\rightarrow$ 断言掉血减半、破防槽恒定 103、眩晕槽恒定 103。

### 5.2 手动沙盒运行与调试
双击工作区根目录下的批处理脚本即可手动启动沙盒：
```cmd
sandbox\launch_sandbox.bat
```
在 WinKawaks 界面中选择 `File -> Load Game`，载入 `kof97pls`（拳皇97 风云再起），即可体验实时魔改成果。

---

## 6. 常见问题排查与工程红线约束

### 6.1 常见问题与避坑指南 (FAQ)

1. **模拟器报红屏或黑屏非法指令崩溃**：
   - **原因**：68000 指令未偶数对齐，或生成的 ROM 缺少 `bswap16` 字节翻转。
   - **解决**：确保所有修改在 `build/unpacked/p1_be.bin`（大端序）中进行，并通过 `tools/rom_tool.py pack` 统一打包。

2. **调色板颜色发紫、过暗或破皮**：
   - **原因**：Bit 15 暗色位（Dark bit）被误置为 1，或者 RGB 分量未按 `LSPC2-A2` 硬件位拆分为高 4 位与第 0 位。
   - **解决**：使用 `tools/rom_tool.py` 内置的 `encode_lspc2(r5, g5, b5, dark=0)` 自动换算，避免手动拼凑机器码。

3. **修改伤害倍率后角色不倒地或血条动画撕裂**：
   - **原因**：68000 算术右移（`ASR`）对负数会保留符号位，导致血量计算溢出；或者未同步累加 `$013A(A4)` 红血计数器。
   - **解决**：在 Code Cave 中必须使用逻辑右移 `LSR.W`，且必须包含 `ADD.W D0, $013A(A4)`。

---

### 6.2 总结与技术支持

所有工具链源码 100% 自包含于工作区内，无需外部繁杂编译器。任何二次魔改需求均可通过修改 `tools/rom_tool.py` 中的相应十六进制常量表，并运行 `build-defense` 或 `build-palette` 命令快速构建生效。
