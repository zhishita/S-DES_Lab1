# 作业要求与来源

## 作业依据

主依据：[作业1：S-DES算法实现](https://shimo.im/docs/m5kvdlMaKvcENy3X)，读取日期 2026-10-06。要求 8 位分组、10 位密钥、指定转换盒、GUI、交叉测试、ASCII 扩展、已知对暴力破解及计时视频/动图、固定明文密钥碰撞分析。代码需有意义命名、适量注释和模块化；仓库提供源码、五关测试结果、用户指南和开发接口文档。文档允许使用 Codex 等 LLM；本项目使用 Codex 辅助独立编写与验证。

提交表：[信息安全导论-作业1提交](https://shimo.im/sheets/5bqndOjwQwhRYVAy/MODOC)。提交内容：教学班 `992987-001`、小组 `YyH`、杨凌至、于沂加、黄相茹、GitHub 仓库链接、通关情况。截止时间 **2026-10-08 23:00，中国标准时间**。人员信息由用户提供；未虚构小组分工或合作过程。

原始文档写“二人一组”；本次成员列表按用户提供的三人信息记录。实现语言未限定唯一方案，本项目使用 Python 标准库服务和浏览器 GUI。TCP 通信、多线程为可选拓展。

## 外部验证数据

读取提交表中的仓库 [Qisheng-Zhang/Information_Security_Lab1](https://github.com/Qisheng-Zhang/Information_Security_Lab1) 的 README，核对其公开样例与测试形式。只复用其已发布的测试数据，不复用实现代码或文档表述。

公开 CSV 来源：[对方.csv](https://github.com/Qisheng-Zhang/Information_Security_Lab1/blob/main/%E5%AF%B9%E6%96%B9.csv)，源 Git blob SHA 为 `4b81dfb48fdd8b2a3a6293284506581fb2d11de7`，本项目保存于 `tests/peer_vectors.csv`，共 200 行。检验方式是本项目加密输出等于公开密文，并且本项目对公开密文解密后等于公开明文。

CSV 名称不能证明其最初生成者，因此本项目将其准确描述为“该组仓库公开的静态测试向量”。未声称联系该组、现场联调或运行该组源码。数据文件 SHA-256 保存在 `results/experiment_results.json`，便于检查内容是否变化。

另浏览了 [AppleKing1225/S-DES-Assignment](https://github.com/AppleKing1225/S-DES-Assignment) 的仓库元信息与简短 README，没有从该仓库复用数据或代码。以上第三方内容只用作参考资料与结果验证。

## 原创范围

Python 算法内核、纯函数接口、HTTP 服务、GUI 布局与前端逻辑、JavaScript 位串核验器、全空间统计、计时记录及动图生成器均在本次任务中独立编写。S-DES 数学流程和转换表来自作业指定标准；算法常量相同是标准兼容的必要条件。
