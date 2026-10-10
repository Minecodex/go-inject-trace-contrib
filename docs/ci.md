# PR 与 CI 合并规则

本仓库默认主分支为 `master`。日常开发从最新主分支创建功能分支，将功能分支推送到组织仓库，再通过 PR 合并。

```sh
git fetch origin
git switch -c feature/your-change origin/master
git push -u origin feature/your-change
```

主分支由仓库规则集保护：必须通过 PR，必须通过 `CI` 检查，合并前必须同步最新主分支，禁止强制推送和删除。规则没有管理员绕过名单；目前不额外要求他人批准，PR 上的审查讨论必须解决。

`CI` 是固定名称的汇总检查。它在所有 PR 上运行，任一必需任务失败、取消或意外跳过都会失败，避免工作流名称或矩阵版本变化导致保护规则失效。检查来源限定为 GitHub Actions。

## 自动检查范围

每个 PR 检查当前 Go 版本的根模块 vet、race 与规则包编译，并通过实际 go-inject 与固定提交的官方 Agent 比较 HTTP、gRPC 和跨 goroutine 的遥测行为。OTel 冒烟使用 Go 1.27，SkyWalking 冒烟使用其场景声明支持的 Go 1.26；运行 A/B 两边，不接受仅编译或只运行其中一边。

每次 v* 版本标签执行 release.yml：Go 1.25.8/1.26.8/1.27.1 在六种原生平台进行基础包检查，Windows arm64 按工具链能力不运行 race；Linux 执行全部 22 个 OTel 和 33 个 SkyWalking 场景的完整声明矩阵，按四个非空分片分别收集结果。SkyWalking 官方 Agent 对照在 Linux Docker 内完成，符合现有上游工具边界；不将其记为 Windows/macOS 官方 Agent Runtime 验收。完整验收的失败、取消或意外跳过均导致 CI 失败。手动 full 或 PR 的 ci:release 标签可在发行前运行同一门槛。没有定时任务。

工作流也支持主分支 push 和手动运行。手动运行使用 Actions 页面的 Run workflow，选择待检查的分支；功能分支首次引入新工作流时，先创建 PR 触发检查。

`test/` 下有独立 Go 模块，根模块的 `go test ./...` 不包含它们；因此遥测 job 单独调用既有 Docker A/B 入口，启动真实依赖、构建和运行两侧程序并执行归一化比较与官方 Collector 验证。k3s 场景包含在完整 OTel 矩阵中；任何缺少场景或空分片都失败。通过范围以该提交的实际基础/冒烟/完整矩阵输出区分。

CI 失败会阻止合并。修复失败后在同一个功能分支继续提交，重新运行检查；不要通过删除必需检查或设置管理员绕过来把失败当作通过。

首次实际 A/B 检查发现资源初始化缺少稳定的 telemetry.sdk 属性，现由同一资源初始化路径为三种信号加入 SDK detector。健康探针本来就属于比较器排除的波动输入，纯探针 trace 也不再留下空树；业务 span 和稳定 SDK 属性的差异继续失败，并有独立回归测试。容器构建关闭隐式 VCS 探测，源码 provenance 由固定 checkout 提交记录，不放宽 Git 的所有权检查。

每个遥测任务保存两侧实际 OTLP 与完整归一化 JSON，避免控制台截断遮住差异。手动 Telemetry diagnostics 可按已声明场景与 Go 版本复现问题，使用相同固定上游与双侧比较；其结果不作为必需 CI 或完整发布矩阵的替代证据。

A/B 工作区固定 fixture 声明的模块版本，防止官方工具添加依赖时只升级 A 侧 SDK，导致比较不同库版本。GenAI 移植补齐真实请求 URL 的 server.address/server.port；OpenAI 的 span 与指标均携带端点，Anthropic 按固定上游只在 span 中携带，保留 SDK 原有身份和语义差异检查。

构建容器通过 init 管理脱离编译器代理的子进程，并保留显式 shell 生命周期与失败前的 daemon/进程/内存诊断。指标按同一 resource/scope/instrument 的稳定合同合并导出批次，完整保留属性点与 bucket 边界；不同采样批次不产生假差异，缺少属性点或业务指标仍失败。

发布制品同时记录 go version -m。官方工具可能提高 require 的 MVS 标签，实际代码仍由 replace 固定；仅在两侧有效 replacement 完全一致时，对齐候选的逻辑 require 标签，以覆盖从 BuildInfo 计算的 SDK User-Agent。不会更改实际 SDK 版本，也不会删除 User-Agent 属性比较；有效模块不同直接失败，并上传对齐记录。

Kubernetes 场景使用与 client-go 对齐的固定 K3s 和有效依赖版本，将实际客户端使用的 k3s-server DNS 别名加入服务证书 SAN，保持完整证书校验。必须成功导入实际 Pod 镜像，并收到创建、指定标签更新与删除事件才进入健康状态。Informer 启动有明确预算；清理先关闭 stop channel 再调用等待退出的 Shutdown，避免事件完成后仍永久阻塞；异常初始化不能以空遥测或健康返回代替验收。

双侧独立集群采用相同 Node 名称和固定 watch 预算，保留这些属性及完整 URL 比较。Pod UID 由各自真实 API 分配，程序输出独立的身份收据；比较器只映射与该收据精确相同的 k8s.pod.uid。缺少 UID、归属错误或试图映射 SDK 等稳定属性仍会失败，原始 OTLP、身份收据与归一化数据分别保存。批处理插桩补齐 codes 导入，错误状态继续与固定上游一致。

SkyWalking 的普通运行时指标采集器在注册前读取 `SW_AGENT_PLUGIN_EXCLUDES`，使用上游逗号分隔、完整名称匹配的规则。排除 runtimemetrics 时不注册运行时指标或采集钩子；默认及其他插件名称仍注册完整指标。自观测场景继续要求原有九项指标合同，不通过过滤额外指标放宽验证。

HTTP 插桩使用 SDK 原有 NanoTime/DurationOfInterceptor API 记录进入和退出处理的实际开销，业务请求本身的耗时不计入该直方图。自观测验收必须收到真实样本，不能只建立空指标结构。

GORM 矩阵逐项使用声明的 excepted-file，版本验收文件来自同一固定上游提交；同一个版本的 A/B 使用相同合同。缺失或越界文件直接失败，不退回默认合同。官方 Collector 的错误正文也保存为失败诊断，区分插桩问题与版本合同选择问题。

PostgreSQL dialector 与 database/sql 的连接信息使用已注入的导出元数据字段传递，避免跨包断言不存在的私有 getter/setter 导致丢失嵌套 SQL span。保留原始 db.statement 和单独的参数标签，不改写 SQL 以适配验收文件。

Docker CMD 健康检查保留声明的参数边界，避免将 bash -c 的脚本拆开后让外层 sh 解释 /dev/tcp，误报 Mongo 等依赖不健康。健康失败包含实际探针输出和服务日志，不把超时当作可忽略的场景。

Elasticsearch v8 使用完整 /v8 模块路径，并固定每个声明单元的实际框架版本，避免非法 major path 或聚合 SDK 依赖把较低版本单元升级成同一个版本。

依赖容器挂载场景声明的上游配置文件，文件必须位于当前场景内；Elasticsearch/RocketMQ 使用固定上游配置，配置只读。Elasticsearch 单节点验收为小数据行为测试，使用明确的 512 MiB JVM 预算并等待真实集群健康，不依赖新镜像的默认安全/集群配置。

RocketMQ 测试消息使用显式、按同步/异步/单向发送区分的业务 ID，避免框架自动生成的进程/时间 ID 使两侧本来相同的消息链路不可比。真实 broker 仍分别启动，消息 ID、broker offset ID、标签及生产者/消费者关联继续精确比较。

SkyWalking 比较器读取实际 meters/logs 明细，验证指标名称、标签、类型、bucket 边界，以及日志内容、级别和 trace 关联；不会把服务包装层当成空的指标/日志。采样数值保留给官方 Collector 合同验证，框架本身的结构差异仍阻止通过。

固定 Apache Mock Collector 不实现动态配置、Profile 和 Pprof 的三个后台查询 RPC。隔离测试网络中的控制网关为这些明确的查询返回合法的空 Commands，表示没有配置更新或分析任务；其余请求、响应、元数据及错误按原始 protobuf 字节转发给真正的 Collector。两侧使用同一网关，原始遥测与日志比较不删减，避免 Collector 缺失接口产生的 Agent 后台错误混入业务日志。此网关属于测试设施，不代表完整 OAP 控制平面验收。

SkyWalking 两侧使用 SDK 原有的精确路径忽略配置排除 fixture 启动探针；只加入声明的 health 路径和 GET 操作名，保留 fixture 原有忽略项。health 与业务入口相同时不排除。Kratos 冷启动的临时 500 探针次数不再随两侧就绪时机改变比较结果；业务 span、状态、标签、指标和日志仍由原比较器和官方合同验证。

Kratos 入口在 AfterStart 中等待真实 gRPC 连接进入 Ready 后才监听外部端口；就绪等待有 30 秒预算，失败直接终止。不会在连接仍处于 Idle/Connecting 时开放业务入口，也不靠健康探针尝试次数判断 A/B 差异。
