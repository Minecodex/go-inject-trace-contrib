# PR 与 CI 合并规则

默认主分支为 `master`。要求 PR、GitHub Actions 固定 CI、同步最新主分支和解决审查讨论；失败、取消、意外跳过都不能通过。禁止强推、删除或管理员绕过。

| 阶段 | 实际范围 |
| --- | --- |
| PR / master push | 当前 Go 的 vet/race/规则包编译与实际官方 OTel/SkyWalking 双侧 HTTP/gRPC/goroutine 遥测冒烟 |
| v* / 手动 full | 三个冻结 Go 版本、六种原生平台（Windows arm64 无 race）、22 个 OTel 与 35 个 SkyWalking 声明场景 |
| diagnostics | 固定上游、相同依赖版本及真实双侧运行的专项定位，不替代完整矩阵 |

发布只由版本标签或手动候选触发；ci:release 标签不再随每次 PR 提交执行全部场景。缺少声明场景、空分片、失败、取消或意外跳过都阻止完整通过。没有定时任务、专用 Runner、额外 Secret 或受保护 Environment。

SkyWalking 新增 Logrus 与 Zap 原生日志插桩：沿用固定官方的日志类型、追踪开关、Reporter 开关、标签、上下文与原始框架输出；日志桥接在 tracer 启动后绑定预先创建的框架 logger。RocketMQ/Dubbo 的框架日志继续保留并参与对照，不过滤缺失信号。Pulsar 的 shell 健康命令使用有效 CMD-SHELL 声明，保持真实服务健康前提。

官方 SkyWalking Agent 仍固定 `b52ef5762fab16d85704a7d35b8968165d351b85`；OTel 官方工具仍固定 `70b4fe80ffb5032e6cdb79f543da5069ee4133b5`。归一化、官方 Collector 合同、原始两侧遥测与源码身份均保留。Linux Docker 对照不宣称 Windows/macOS 的官方 Agent Runtime 验收；原生基本包检查与完整遥测范围分别报告。

Dubbo 使用冻结的 Triple 生成器。两侧相同的生成后步骤把单值 metadata 表示为标量附件，以兼容 v3.0.1 的 GetAttachment；多值附件和线上实际 header 保留，官方 Agent 源码不改动，全部四个 Dubbo 版本仍验证原始跨进程引用。框架日志仅归一化 Dubbo URL 的进程号、时间戳及 MetadataService 随机监听端口，业务 RPC 地址、方法、框架版本、日志内容和关联状态仍参与对照。

日志示例同时保留固定上游原始 excepted.yml 与显式 excepted-gateway.yml。后者仅不再要求原 Mock Collector 不支持的三项后台查询错误，因为既有控制网关返回合法空 Commands；两条业务日志的内容、级别、模块标签和真实关联仍完全验证，实际遥测与 A/B 日志不删减。
