# Scanner Skill 冒烟验证结果

## RuoYi-Vue

- project-inventory.json：✅ 已生成（17KB）
- command-catalog.yaml：✅ 已生成
- scanner-report.md：✅ 已生成
- 识别到的技术栈：Java (Maven multi-module) + Node (Vue frontend)
- 识别到的 build/test/frontend 命令：
  - build: `mvn clean package -DskipTests`
  - test: `mvn test`
  - frontend: `npm run build` (ruoyi-ui)
  - run: `npm run dev` (ruoyi-ui)
- 详细发现：
  - 7 个 pom.xml 文件
  - 6 个 Maven modules
  - 1 个 Spring 配置文件
  - 2 个 SQL 资产
  - ruoyi-ui 前端项目：106 个 Vue 文件，4 个 scripts
  - 25 个 Controller，23 个 Service
- 人工校准点：
  - Maven profile 支持（开发/生产配置差异）
  - 前端 build:prod vs build:stage 区分

## eShopOnWeb

- project-inventory.json：✅ 已生成（14KB）
- command-catalog.yaml：✅ 已生成
- scanner-report.md：✅ 已生成
- 识别到的技术栈：.NET (ASP.NET Core)
- 识别到的 build/test 命令：
  - build: `dotnet build`
  - test: `dotnet test`
- 详细发现：
  - 2 个 solution 文件
  - 10 个 csproj 项目
  - 4 个测试项目
  - global.json 存在
  - 2 个 GitHub Actions workflow
  - 2 个 Dockerfile
  - 7 个 Controller
- 人工校准点：
  - Docker compose 文件未检测到（eShopOnWeb 可能不使用 compose）
  - ProjectReference 链路正确

## 结论

- Core schema 稳定：✅ 两种技术栈均输出统一 core schema + stack extensions
- 技术栈扩展字段有用：✅ Java/Node/.NET 各自的结构化信息丰富且准确
- 下一阶段 Task Mapping Skill 需要的字段：
  - command-catalog.yaml 中的 verified 标记
  - codeStructure 中的 controllers/services 分类
  - stackExtensions 中的 buildFiles / testProjects
  - ci 中的 githubActions / dockerfiles
