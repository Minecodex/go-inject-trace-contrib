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
