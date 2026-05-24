# Scanner 输出契约

## 必需文件

```text
.harness/
  project-inventory.json
  command-catalog.yaml
  scanner-report.md
```

## project-inventory.json

捕获确定性的仓库清单信息：

- 仓库元数据
- 技术栈信号
- 目录结构
- 构建文件
- 配置文件
- 文档资产
- 测试资产
- CI 与 Docker 资产
- 文件计数

## command-catalog.yaml

捕获命令候选：

- build（构建）
- test（测试）
- run（运行）
- frontend（前端）
- docker（容器）

每条命令应包含：

- name（名称）
- command（命令内容）
- working directory（工作目录）
- source file（来源文件）
- confidence（置信度）
- verified flag（已验证标记）

## scanner-report.md

供人工审阅和演示的可读摘要报告。
