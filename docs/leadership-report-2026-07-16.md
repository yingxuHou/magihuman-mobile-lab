# MagiHuman Mobile Lab 复现与手机 App 可行性阶段汇报

- 项目名称：MagiHuman Mobile Lab
- 仓库：`magihuman-mobile-lab`
- GitHub：https://github.com/yingxuHou/magihuman-mobile-lab.git
- 报告日期：2026-07-16
- 当前提交：`3378199`
- 当前阶段：GPU handoff 已准备好，真实 GPU 推理数据待补充

## 一句话结论

不建议把 daVinci-MagiHuman 作为端侧模型直接装进手机 App 本地推理。当前更合理的产品方向是“手机 App + 云端 GPU 推理服务”。

但云端方案还不能给出最终产品化结论，因为真实 GPU 推理、生成质量、移动端播放兼容性和单条视频成本尚未实测。下一步建议先租用云 H100 做小额、受预算控制的 P01 smoke test，不建议现阶段直接采购硬件。

## 当前决策状态

| 选项 | 当前判断 | 依据 |
| --- | --- | --- |
| A. 手机端侧本地推理 | 不建议，基本不可行 | 官方栈依赖 CUDA/PyTorch/NCCL/MagiCompiler，完整模型依赖体积约 285.63 GiB，未发现 ONNX/Core ML/TFLite/NCNN/MNN 等移动端导出路径 |
| B. 手机 App + 云端 GPU 推理 | 当前推荐方向，但仍待实测 | 本地已完成 API、worker、任务队列、指标采集、实验矩阵、证据导入和预算门禁；真实 GPU runtime 证据尚未返回 |
| C. 暂停产品化 | 暂不下结论 | 需要先完成 P01 和后续 required suite 实测，再根据速度、质量、成本决定是否继续 |

当前自动化判定状态为：`B_pending_runtime`。

## 已完成工作

### 1. 官方资料和模型依赖核验

已核验官方论文、代码仓库、模型仓库和 Demo 入口，并记录在 README 和 todo 中：

- Paper: https://arxiv.org/abs/2603.21986
- Code: https://github.com/GAIR-NLP/daVinci-MagiHuman
- Model: https://huggingface.co/GAIR/daVinci-MagiHuman
- Demo: https://huggingface.co/spaces/SII-GAIR/daVinci-MagiHuman

已形成的关键判断：

- 官方模型是面向 GPU 的大规模视频生成模型，不是移动端轻量模型。
- 完整 checkpoint 和外部依赖估算约 285.63 GiB。
- P01 base smoke-test 所需依赖也约 114.64 GiB。
- 官方路径使用 PyTorch、CUDA、NCCL、MagiCompiler、Flash Attention 等 GPU 生态组件。
- 在官方仓库静态搜索中，未发现明确的 ONNX、Core ML、TFLite、NCNN、MNN 或 TorchScript 移动端导出路径。

### 2. 本机环境评估

当前本机不具备完整推理复现条件：

| 项目 | 当前情况 |
| --- | --- |
| 操作系统 | Windows 11 |
| GPU | Intel Iris Xe Graphics |
| NVIDIA GPU/CUDA | 未检测到 |
| Docker/Conda 推理环境 | 当前不作为完整推理环境使用 |
| 结论 | 本机适合做代码准备、流程设计和报告同步，不适合跑 daVinci-MagiHuman 真实推理 |

因此，真实推理必须切换到 Linux NVIDIA GPU 主机，优先 H100。

### 3. 复现实验流程已经工程化

虽然还没有真实 GPU 结果，但复现流程已准备到可以交给 GPU 主机执行：

- 已准备 P01 256p / 5 秒 smoke test。
- 已准备 required suite：P01、P03、P04、T01、T02。
- 已准备 GPU preflight，检查 NVIDIA、Docker、Git、Git LFS、Python、Bash、ffprobe、模型目录等。
- 已准备 GPU workflow，一键串联源码准备、模型下载、P01、required suite、验收、证据打包。
- 已准备证据导入流程，GPU 主机返回 `outputs/gpu-evidence-*.tar.gz` 后，本地可安全导入并刷新报告。
- 已准备质量评审、成本评审、移动端视频兼容性检查门槛。
- 当前本地测试全部通过：`195 passed`。

当前 handoff 状态：

| 项目 | 状态 |
| --- | --- |
| GPU execution packet | `ready_for_gpu_handoff` |
| GPU session budget | `budget_ready` |
| Reproduction gap report | `awaiting_gpu_runtime` |
| Review readiness | `runtime_not_ready` |
| Final recommendation | `B_pending_runtime` |

## 当前证据和缺口

### 已经足够支持的结论

端侧部署基本不可行。原因不是单一指标，而是多项证据叠加：

- 模型和依赖体积远超 App 包内分发可接受范围。
- 官方推理路径依赖 NVIDIA/CUDA 生态。
- 官方没有提供移动端导出或端侧推理路线。
- 官方性能指标以 H100 为参考，不是手机硬件。
- 当前本机普通显卡无法提供推理条件。

因此，手机端更适合作为客户端，而不是模型运行环境。

### 仍然缺失的结论证据

云端 GPU 方案是否适合产品化，还缺以下真实数据：

| 缺口 | 需要补充的数据 |
| --- | --- |
| GPU runtime | P01/P03/P04/T01/T02 的真实耗时、峰值显存、CPU 内存 |
| 输出结果 | 每个 case 的实际 MP4 输出 |
| 移动端兼容性 | MP4/H.264/AAC、时长、音视频流、手机播放表现 |
| 质量评审 | 脸部质量、动作自然度、语音可懂度、伪影控制、音画同步 |
| 成本评审 | 单条视频 GPU 成本、排队和等待时间、失败重试成本 |

这些数据回来之前，不应把 `B_pending_runtime` 改成最终 B。

## 预算和硬件建议

### 不建议现在采购硬件

当前不建议直接采购本地 GPU 设备，原因：

- 真实推理还没有跑通，无法确认最低可用 GPU 配置。
- 不清楚 P01、540p、1080p、多语言 TI2V 的实际显存和耗时。
- 不清楚生成质量是否达到产品演示标准。
- 不清楚单条视频成本和等待时间是否可接受。
- 采购 H100/A100/高端 4090/5090 级硬件前，应该先用云 GPU 低成本验证。

### 建议先租云 GPU 做 P01 smoke test

当前已填写一个受控预算方案：

| 项目 | 配置 |
| --- | --- |
| Provider | Thunder Compute |
| GPU | H100 PCIe 80GB |
| 报价来源 | https://www.thundercompute.com/pricing |
| 报价检查日期 | 2026-07-16 |
| GPU 小时价 | 2.19 USD/hour |
| 预算运行时长 | 4 小时 |
| 计费开销倍数 | 1.25 |
| 预估 session 成本 | 10.95 USD |
| session 封顶预算 | 15.00 USD |
| 磁盘预算 | 300 GiB |
| 当前预算状态 | `budget_ready` |

执行前必须重新确认报价，并在云服务商侧设置 4 小时 / 15 USD 级别的消费上限或自动关机。

## 推荐下一步

### 第一步：只跑 P01，不直接跑完整 suite

目标：用最小成本验证官方模型能否在云 H100 上稳定出片。

P01 配置：

- 类型：T2V smoke test
- 分辨率：256p
- 时长：5 秒
- seed：42
- 输出：`outputs/smoke-test/P01.mp4`
- 必须采集：总耗时、峰值显存、CPU 内存、ffprobe 视频信息、移动端播放兼容性

如果 P01 失败，应先定位失败原因，不继续下载 SR 或跑 required suite。

### 第二步：P01 通过后再跑 required suite

P01 通过后，再运行：

- P03：540p / SR 相关路径
- P04：1080p / SR 相关路径
- T01/T02：多语言或 TI2V 相关路径

这一步用于判断云端 GPU 方案是否真的适合 App 产品化。

### 第三步：补质量评审和成本评审

GPU 证据导入后，再填写：

- `docs/quality-review.json`
- `docs/cost-review.json`

只有当 runtime、质量、成本、移动端播放都通过后，才能把结论从 `B_pending_runtime` 更新为最终 B。

如果质量、速度或成本不达标，则应改为 C：当前不适合产品化 App。

## 面向领导的可汇报口径

当前阶段可以这样汇报：

> 我们已经完成 daVinci-MagiHuman 的官方资料核验、模型体积评估、端侧可行性静态分析、云端 GPU 复现实验流程搭建，以及手机 App 后端原型和证据评审机制。现有证据已经足够判断：官方完整模型不适合直接装进手机 App 本地运行。更合理的路线是手机 App 作为客户端，云端 GPU 负责视频生成。
>
> 但云端方案是否值得产品化，还缺真实 GPU 推理数据。我们不建议现在采购硬件，建议先按 15 美元以内预算租用 H100 跑一次 P01 256p smoke test。P01 跑通后，再决定是否继续跑 540p、1080p 和多语言测试，并最终用速度、质量、成本数据决定项目进入云端 App 方案还是暂停产品化。

## 当前风险

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| Hugging Face gated 模型访问失败 | 无法下载完整模型 | GPU preflight 已加入 token/access 检查 |
| P01 不能稳定出片 | 云端方案可能不可行或需要修改官方流程 | 先只跑 P01，失败后定位，不扩大开销 |
| 高分辨率/SR 成本过高 | App 用户等待时间和单条成本不可接受 | P01 通过后分阶段跑 P03/P04，再做成本评审 |
| 输出质量不足 | 即使技术跑通也不能产品化 | 已准备质量评审门槛，需人工审核样片 |
| 视频格式不适配手机 | App 端播放、保存、分享体验受影响 | 已准备 mobile video compatibility gate，必要时增加转码 |

## 结论

当前结论不是“项目已经复现完成”，而是：

1. 端侧本地部署：不建议，基本不可行。
2. 云端 GPU + 手机 App：当前推荐方向，但等待真实 GPU runtime 证据。
3. 硬件采购：暂不建议采购，先租云 H100 做 P01 小额验证。
4. 下一步决策点：P01 是否能在预算内稳定生成可播放视频。

最终 App 产品化结论必须等 P01/P03/P04/T01/T02、质量评审、成本评审和移动端播放证据补齐后再更新。
