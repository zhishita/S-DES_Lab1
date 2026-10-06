# S-DES 密码实验台

信息安全导论 · 作业 1。教学班 **992987-001**，小组 **YyH**，成员 **杨凌至、于沂加、黄相茹**。

用 Python 独立实现课程指定的 S-DES，用本地浏览器 GUI 展示每一步的位变化。主密钥为 10 位，分组为 8 位；采用作业文档修改后的 SBox2。运行界面只需要 Python 3.10+ 和现代浏览器，全部数据在本机处理。

## 启动

下载仓库后，在项目根目录运行：

```sh
python -m sdes.webapp --open
```

浏览器地址为 `http://127.0.0.1:8765`，按 Ctrl+C 结束服务。端口占用时可加 `--port 8768`。界面有分组实验、字符串实验、密钥搜索、碰撞探索四个模块；测试报告覆盖作业的全部五关。

## 已完成的验证

| 关卡 | 实现和实测结果 | 证据 |
| --- | --- | --- |
| 1 · 基本测试 | GUI 支持分组加解密、输入校验、K1/K2 和逐轮跟踪；262,144 个组合全部正确还原 | [测试报告](docs/test-report.md)、[原始结果](results/experiment_results.json) |
| 2 · 交叉测试 | 独立 JavaScript 位串实现与 Python 全空间摘要一致；另一组公开的 200 条 CSV 向量全部兼容 | [交叉测试说明](docs/test-report.md#第二关交叉测试)、[来源说明](docs/sources.md) |
| 3 · 扩展功能 | ASCII 每字节加解密，提供 HEX、二进制、转义字节串；另支持 UTF-8 中文 | [用户指南](docs/user-guide.md)、[字符串实测](docs/test-report.md#第三关字符串) |
| 4 · 暴力破解 | 完整遍历 1024 个密钥，保留所有候选，记录 UTC 时间戳与高精度耗时 | [计时动图](results/bruteforce.gif)、[原始进度](results/bruteforce_timeline.json) |
| 5 · 封闭测试 | 所有 256 个固定明文都有密钥碰撞，最大桶含 12 个密钥；无全局等价密钥 | [完整 256 行统计](results/collision_summary.csv)、[分析与证明](docs/test-report.md#第五关封闭测试) |

![完整密钥搜索的实测进度慢速回放](results/bruteforce.gif)

动图使用真实计算采样，**动画播放时间不是破解耗时**。实际耗时和 UTC 起止时间标在画面上；计算期间未插入人为延时。性能数字仅代表本次机器与运行环境。

## 文档与复现

- [用户指南](docs/user-guide.md)：运行与四个模块的操作示例。
- [开发手册](docs/developer-guide.md)：算法参数、函数、HTTP API、目录与扩展方法。
- [五关测试报告](docs/test-report.md)：本次实测结果、候选密钥与碰撞证明。
- [要求与来源](docs/sources.md)：作业规则、外部向量来源、独立编写说明。
- [单元测试记录](results/unit_tests.txt)：校验异常、ASCII 全字符、过程跟踪、密钥搜索等测试。

```sh
# 普通单元测试，仅需 Python
python -m unittest discover -s tests -v

# 重新生成五关原始结果：额外需要 Node.js 18+
python -m tests.run_experiments

# 可选：重新生成计时动图，额外需要 Pillow
python -m pip install -r requirements-media.txt
python tools/make_animation.py
```

另一组公开的静态测试向量只用于结果互验，未复制其算法源码、界面或文档。项目内独立 JavaScript 实现用于跨语言全空间核对；公开向量互验不等同于与对方现场联调。细节见来源说明。

S-DES 的密钥空间只有 1024，适合教学实验，不用于实际敏感信息保护。
