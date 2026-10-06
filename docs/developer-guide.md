# 开发手册

## 组织与数据流

`sdes/core.py` 提供纯函数内核；`sdes/experiments.py` 提供字符串、破解和碰撞统计；`sdes/webapp.py` 提供本地 HTTP 接口；`web` 是原生 HTML/CSS/JavaScript GUI。浏览器请求输入 → Python 校验 → 算法执行 → JSON 结果 → 文本方式安全展示。

`tests/test_sdes.py` 为普通测试，`tests/reference.js` 是独立位串核验实现，`tests/run_experiments.py` 生成五关原始记录，`tools/make_animation.py` 将真实采样制作成带计时的慢速回放。

## 课程算法参数

所有置换表按最高位到最低位编号，起始编号为 1。

| 转换 | 参数 |
| --- | --- |
| P10 | 3, 5, 2, 7, 4, 10, 1, 9, 8, 6 |
| P8 | 6, 3, 7, 4, 8, 5, 10, 9 |
| IP | 2, 6, 3, 1, 4, 8, 5, 7 |
| IP⁻¹ | 4, 1, 3, 5, 7, 2, 8, 6 |
| EP | 4, 1, 2, 3, 2, 3, 4, 1 |
| P4 | 2, 4, 3, 1 |

SBox1 各行为 `(1,0,3,2)`、`(3,2,1,0)`、`(0,2,1,3)`、`(3,1,0,2)`；SBox2 各行为 `(0,1,2,3)`、`(2,3,1,0)`、`(3,0,1,2)`、`(2,1,0,3)`。外侧两位决定行，内侧两位决定列。作业明确指出第二个 S 盒以文档为准。

密钥经 P10 后拆成两个 5 位半部，分别左移 1 位生成 K1；在该状态再分别左移 2 位生成 K2，即累计左移 3 位。加密流程为 `IP → f(K1) → SW → f(K2) → IP⁻¹`；解密交换两个子密钥的使用顺序。轮函数将右半部扩展、与子密钥异或、经两个 S 盒和 P4 得到 4 位值，与左半部异或，右半部保持。第二轮后不再进行 SW。

## Python 接口

| 函数 | 输入 | 返回 / 说明 |
| --- | --- | --- |
| `parse_bits(value, width, label)` | 严格二进制字符串、宽度、错误标签 | 整数；不匹配则 ValueError |
| `subkeys(key)` | 0～1023 整数 | `(K1,K2)`，每个 0～255 |
| `encrypt_block(block,key)` | 0～255 分组、0～1023 密钥 | 0～255 密文 |
| `decrypt_block(block,key)` | 同上 | 0～255 明文 |
| `trace_block(block,key,decrypt=False)` | 同上、解密标志 | 字典：K1/K2、IP、两轮 EP/XOR/S1/S2/P4/output、SW、最终输出 |
| `encode_text(text,key,encoding='ascii')` | 字符串、密钥、ascii 或 utf-8 | HEX、分组二进制、转义字节串、字节数 |
| `decode_text(cipher_hex,key,encoding='ascii')` | HEX、密钥、编码 | 还原文本、明文 HEX、字节数 |
| `crack_keys(pairs,progress=None)` | 非空 `(明文,密文)` 整数列表；可选回调 | 全部候选、checked=1024、UTC 起止、elapsed_ms、16 个采样事件 |
| `collision_report(plain)` | 一个明文整数 | 不同密文数、碰撞桶数、最大桶、单候选桶、全部碰撞明细 |

整数接口拒绝 bool、负数、浮点和越界值；编码与 HEX 错误通过 ValueError 或 UnicodeError 报告。内核使用两张 256 项置换表和一张 256×16 轮函数表，并缓存最多 1024 个子密钥对。跟踪接口直接按各步骤计算，可与优化路径核验。

## HTTP API

`POST /api`，请求为 UTF-8 JSON；成功返回 200 与 JSON，输入错误返回 400 与 `{"error":"…"}`。最多 65536 字节；仅供本地 GUI。GET 只提供 `/`、`/app.js`、`/style.css`，不会公开源代码、目录或任意本地文件。不同源的浏览器请求返回 403。

| action | 其他字段 | 输出 |
| --- | --- | --- |
| encrypt / decrypt | block:8 位字符串，key:10 位字符串 | trace_block 结果 |
| encode / decode | text:文本或 HEX，key:10 位，encoding:ascii/utf-8 | 编码或解码结果 |
| crack | pairs:多行字符串，每行 `明文 密文`，最多 256 行 | crack_keys 结果 |
| collisions | block:8 位明文 | collision_report 结果 |

示例请求：`{"action":"encrypt","block":"10010111","key":"1010000010"}`。前端使用 `textContent` 与 DOM 元素创建展示输入和结果，避免将用户文本解释为 HTML。运算期间按钮禁用，失败后恢复。

## 测量和扩展

破解在清空子密钥缓存后开始计时，计入生成子密钥、完整候选检查、进度记录与回调开销；模块导入时常量表创建不在该计时内。UTC 用于起止时间显示，持续时间用单调高精度 `perf_counter_ns`，避免系统时钟调整影响耗时。

全空间比较按“key 从 0～1023，plain 从 0～255”顺序连接每个密文字节，再计算 SHA-256。Python 与独立 JavaScript 必须生成完全相同的序列；两者同时各自检查解密回环。

课程没有要求强制使用 TCP 或多线程，这两项未加入；优先完整算法、交互、来源明确的验证和可复现实验。若扩展通信协议，应保持 ASCII 每字节映射，不改变本课程转换表。若修改 S 盒或移位规则，需要重跑全空间测试并重新生成报告，不能沿用旧结果。
