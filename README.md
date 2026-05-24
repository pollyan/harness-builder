# Harness Builder

Harness Builder 是一个概念验证（POC）项目，目标是从现有企业级代码库中自动生成项目级 AI Coding Harness 资产。

当前 POC 聚焦于一个最小可验证闭环：

```text
目标仓库 → Scanner → Harness 资产 → Task Mapping → Sensor 验证
```

## POC 范围

首轮 POC 验证两种常见企业技术栈：

- Java / Spring Boot / Maven / Vue：RuoYi-Vue
- .NET / ASP.NET Core / EF Core：eShopOnWeb

Apache Fineract 作为第二阶段复杂业务系统候选，已纳入跟踪。

## 开发方法

本仓库遵循规范优先（Spec-first）的开发流程：

1. 先设计，后实现
2. 先制定实施计划，后编写代码
3. 采用小粒度、TDD 导向的任务拆分
4. 以真实目标仓库为验证对象
5. 扩大范围前必须经过评审

## 当前状态

处于 POC 规划早期阶段，尚无生产级实现。
