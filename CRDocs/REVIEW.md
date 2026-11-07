# 审查结论与问题清单 (CRDocs — TASK-ROM-004 Round 4)

- **Task ID**：`TASK-ROM-004`
- **Target**：调色板皮肤魔改（八神庵专属黑金配色与 Neo-Geo LSPC2-A2 编解码器实现，实机自动化验证）
- **Reviewer**：Argon
- **Review Round**：Round 4
- **Decision**：**APPROVED**（`P0: 0`, `P1: 0`, `P2: 0`；前序 `[CR-003-P2-01]` 已圆满关闭 `RESOLVED`）

---

## 审查结论

经独立核查 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py)、[`output/roms/kof97pls.zip`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/output/roms/kof97pls.zip) 全量二进制 Diff、Motorola 68000 / Neo-Geo LSPC2-A2 硬件调色板编码规范、原生目录只读隔离性及自动化实机截图（[`kof97pls050.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls050.png)、[`kof97pls051.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls051.png)、[`kof97pls052.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls052.png)），**`TASK-ROM-004`（阶段四：调色板皮肤魔改）100% 满足 `DIR-001`、[`Rules.md`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/.claude/Rules.md) 与 [`Plan.md`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/Plan.md) 验收标准，予以正式通过（`APPROVED`）**。

---

## 独立核验清单与实测结果

### 1. 宿主目录只读安全与纯英文规范（100% 达标）
- **原生文件只读隔离**：独立复核 `C:\Program Files (x86)\KOF97\roms` 原始资产：
  - `kof97.ZIP`（29,286,731 B，MD5 `87e8718af8b5d452e6d32697c051c994`，mtime 维持 `946656000.0`）
  - `kof97pls.zip`（1,438,722 B，MD5 `6f152d3ec8d2d5cb252a203e97603677`，mtime 维持 `1075863528.0`）
  - `neogeo.zip`（57,734 B，MD5 `6ab3817a33c5b75bb745ca1f9efb55d1`，mtime 维持 `1036030632.0`）
  确认宿主目录零写入、零篡改。
- **纯 ASCII 规范**：独立扫描代码库核心工具与脚本：
  - `tools/rom_tool.py`（59,922 字节，非 ASCII 字符数：`0`）
  - `sandbox/launch_sandbox.bat`（700 字节，非 ASCII 字符数：`0`）
  100% 遵守纯 ASCII 英文规范，杜绝 Windows 控制台编码隐患。

### 2. Neo-Geo LSPC2-A2 16-bit 调色板编解码器独立核算（100% 精确）
- **硬件位布局核验**：
  SNK Neo-Geo MVS / AES 视频硬件（LSPC2-A2）采用 16-bit 非线性 RGB 位排布：
  - Bit 15：`Dark bit`（暗位）
  - Bit 14：`R0`（红色分量 LSB）
  - Bit 13：`G0`（绿色分量 LSB）
  - Bit 12：`B0`（蓝色分量 LSB）
  - Bits 11..8：`R4..R1`（红色高 4 位）
  - Bits 7..4：`G4..G1`（绿色高 4 位）
  - Bits 3..0：`B4..B1`（蓝色高 4 位）
- 核查 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L73-L105) 中的 `encode_lspc2()` 与 `decode_lspc2()`，位掩码与移位逻辑完全吻合硬件设计规范。
- 独立执行 `python tools/rom_tool.py self-test`，覆盖基线样字双向往返无损编解码校验，测试 100% 通过。

### 3. P2-ROM 全量二进制 Diff 独立复核（精准 72 字节）
独立比对 `build/unpacked/p2_be.bin` 与原版 `KOF97_P2.ROM`（经 `bswap16` 转换后的大端逻辑空间）：
全量 4,194,304 字节中，**仅精确修改 72 字节**，其余 4,194,232 字节零漂移，且修改范围严格限制在调色板数据区内：

1. **八神庵 A 键主调色板（`0x2DF7F0..0x2DF80F`，修改 21 字节）**：
   - `Word #00`（`+0x00`）：`0x07C0`（PalID 控制头严格原值保持）；
   - `Word #01..#04`（`+0x02..+0x08`）：`0x4FFB`, `0x0FC8`, `0x5E95`, `0x1B52`（肤色高光、主肤色、阴影与深阴影严格原值保持，肤色自然）；
   - `Word #05..#07`（`+0x0A..+0x0E`）：由原版亮白灰（`0x1FFF`, `0x6BBC`, `0x2778`）精准替换为黑夜衬衣：
     - `Word #05`: `0x0333`（RGB 5-bit: `6, 6, 6`，高光黑炭）；
     - `Word #06`: `0x7111`（RGB 5-bit: `3, 3, 3`，暗灰过渡）；
     - `Word #07`: `0x7000`（RGB 5-bit: `1, 1, 1`，深黑阴影）；
   - `Word #08..#11`（`+0x10..+0x16`）：由原版酒红头发/裤装（`0x6D32`, `0x6A21`, `0x7710`, `0x4400`）替换为金属纯黄金渐变：
     - `Word #08`: `0x7FD3`（RGB 5-bit: `31, 27, 7`，耀眼亮金高光）；
     - `Word #09`: `0x7DA1`（RGB 5-bit: `27, 21, 3`，黄金主色）；
     - `Word #10`: `0x1A70`（RGB 5-bit: `20, 14, 1`，暗金阴影）；
     - `Word #11`: `0x0640`（RGB 5-bit: `12, 8, 0`，青铜沉底）；
   - `Word #12..#15`（`+0x18..+0x1E`）：由原版紫灰蓝（`0x7334`, `0x7223`, `0x7112`, `0x1000`）替换为黑金风衣：
     - `Word #12`: `0x1222`（RGB 5-bit: `4, 4, 5`，深灰反光）；
     - `Word #13`: `0x1111`（RGB 5-bit: `2, 2, 3`，暗夜黑主色）；
     - `Word #14`: `0x6001`（RGB 5-bit: `1, 1, 2`，风衣暗部）；
     - `Word #15`: `0x0000`（RGB 5-bit: `0, 0, 0`，纯黑勾边）。
2. **选人/立绘头像板同步金发化（`0x2DF990..0x2DF9EF`，修改 22 字节）**：
   - `0x2DF990`（PalID `0x07CD`）：Words #08, #10, #11, #15 替换为黄金梯级；
   - `0x2DF9B0`（PalID `0x07CE`）：Words #07, #08, #09 替换为黄金梯级；
   - `0x2DF9D0`（PalID `0x07CF`）：Words #06, #07, #08, #14 替换为黄金梯级；
   精准确保选人界面的巨大半身立绘与顶部 HUD 小头像金发一致性。
3. **历史偏移兼容写入（`0x2DC9F0..0x2DCA0F`，修改 29 字节）**：
   - 保持 `Word #00: 0x0650` 控制头，同步覆写为一致黑金配色，防止历史脚本调用产生色彩突变。

### 4. P1 防御 Patch 无损继承核验（100% 保持）
- 独立复核 `build/unpacked/p1_be.bin` 与原版比较：
  - 维持且仅维持 `TASK-ROM-003` 批准的 **4 处精确改动（共 20 字节）**：
    1. `0x000300..0x000308`: `E2 48 D1 6C 01 3A 4E 75`（Code Cave 受创减半跳板）
    2. `0x01394A..0x01394E`: `4E B8 03 00`（`JSR ($0300).W`）
    3. `0x01397E..0x013982`: `4E 71 4E 71`（免疫破防）
    4. `0x0139A4..0x0139A8`: `4E 71 4E 71`（免疫眩晕）
  - 大端校验和 `0x21465F0A`，经 `bswap16` 打包后磁盘 CRC32 为 `0xFF227541`，零回退。
- `s1.bin`（131,072 B）零差异，CRC32 为 `0x8514ECF5`。

### 5. 打包交付物与实机视觉截图独立复核（100% 达标）
- 检验 `output/roms/kof97pls.zip` 内容：
  - `232-p1p.bin`（1,048,576 B，磁盘 CRC32 `0xFF227541`）
  - `232-p2p.bin`（4,194,304 B，磁盘 CRC32 `0xAF5CC95E`）
  - `232-s1p.bin`（131,072 B，磁盘 CRC32 `0x8514ECF5`）
- 检验截获实机图像数据：
  1. [`sandbox/capture/kof97pls050.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls050.png)：Member Select 界面光标聚焦八神庵，左下巨幅半身像金发璀璨，发丝质感与黑衣对比分明；
  2. [`sandbox/capture/kof97pls051.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls051.png)：Order Select 界面八神庵作为首发 1P，金发金裤与黑长风衣比例协调；
  3. [`sandbox/capture/kof97pls052.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls052.png)：Round 1 实机格斗对决态，金发刘海、金色绑带裤、深邃墨黑风衣在战斗中完美呈现，无破皮拉花或色块错位；顶部血槽、破防槽（103）与眩晕槽（103）完好无损。

---

## 问题清单 (P0 / P1 / P2)

本轮无新增 `P0`、`P1`、`P2` 问题。

### 历史问题关闭情况
- **`[CR-003-P2-01]` 阶段四（`TASK-ROM-004`）八神庵真实角色 ID（`0x1B`）与 A 键调色板物理偏移校准（`0x2DF7F0`）**：
  - **状态**：**`RESOLVED`**
  - **结论**：Antigravity 完整采纳了 Argon 反汇编查表结论，在 `p2_be.bin` 真实偏移 `0x2DF7F0`（PalID `0x07C0`）及头像板 `0x2DF990..0x2DF9EF`（PalID `0x07CD..0x07CF`）成功落地黑金配色，实机对战与立绘均实现金发黑衣展现。该项圆满闭环关闭。
