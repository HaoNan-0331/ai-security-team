# 修改记录

## 2026-03-19 (v2.1)

### 删除
- `agents/monitoring/threat-intel/` - 整个威胁情报Agent目录（职责整合到alert-judgment，使用ip-reputation skill）

### 修改
- `agents/README.md` - 更新团队结构为10个Agent，监控分析组从4个减少到3个，新增v2.1版本说明
- `README.md` - 更新为10个Agent，移除threat-intel条目，更新行为基线归属为威胁情报归属说明
- `agents/monitoring/alert-judgment/prompt.md` - 新增ip-reputation skill用于IP信誉查询
- `agents/monitoring/log-analysis/prompt.md` - 移除对threat-intel的协作关系和边界描述
- `agents/assessment/risk-compliance/prompt.md` - 移除对threat-intel的输入引用
- `agents/assessment/vuln-assessment/prompt.md` - 移除对threat-intel的协作关系
- `knowledge/README.md` - 更新Agent推荐查询路径，将threat-intel改为alert-judgment
- `team-framework/agents/log-analysis.json` - 移除对threat-intel的协作配置
- `agents/supervisor/src/detector.py` - 移除threat-intel的能力定义

### 优化效果
- Agent数量：11 → 10（减少9%）
- 情报查询能力：从独立Agent变为Skill调用，响应更快

---

## 2026-03-18 (v2.1)

### 新增
- `knowledge/products/` - 产品知识目录（防火墙、网络设备等）
- `knowledge/technologies/` - 技术知识目录（网络技术、安全技术）
- `knowledge/compliance/` - 合规知识目录（等保2.0、ISO27001）
- `knowledge/templates/` - 配置模板目录
- `knowledge/products/firewalls/ASG防火墙/README.md` - ASG防火墙知识索引
- `knowledge/compliance/等保2.0/README.md` - 等保2.0三级要求

### 修改
- `knowledge/README.md` - 重写知识库说明，新增目录结构、使用指南、各Agent推荐查询路径
- `agents/orchestrator/prompt.md` - 新增知识库使用章节
- `agents/monitoring/log-analysis/prompt.md` - 新增知识库使用章节
- `agents/monitoring/alert-judgment/prompt.md` - 新增知识库使用章节
- `agents/monitoring/threat-intel/prompt.md` - 新增知识库使用章节
- `agents/monitoring/asset-mgmt/prompt.md` - 新增知识库使用章节
- `agents/defense/threat-response/prompt.md` - 新增知识库使用章节
- `agents/defense/forensic/prompt.md` - 新增知识库使用章节
- `agents/defense/policy-exec/prompt.md` - 新增知识库使用章节
- `agents/assessment/vuln-assessment/prompt.md` - 新增知识库使用章节
- `agents/assessment/risk-compliance/prompt.md` - 新增知识库使用章节
- `agents/operations/network-ops/prompt.md` - 新增知识库使用章节
- `agents/operations/server-ops/prompt.md` - 新增知识库使用章节

### 优化
- 所有Agent现在支持优先查询本地知识库获取专业知识
- 知识库目录结构参照 `E:/knowlegdge_base/ai_knowlegdge/security_knowlegdge/product_knowlegdge/` 架构

---

## 2026-03-17 (v2.0)

### 删除
- `agents/defense/incident-response/` - 整个事件响应Agent目录（职责整合到orchestrator）
- `agents/assessment/pentest/` - 整个渗透测试Agent目录（职责整合到vuln-assessment）
- `agents/assessment/risk-assessment/` - 整个风险评估Agent目录（与compliance合并）
- `agents/assessment/compliance/` - 整个合规检查Agent目录（与risk-assessment合并）
- `agents/operations/patch-mgmt/` - 整个补丁管理Agent目录（职责整合到server-ops）
- `configs/patch-mgmt/` - 补丁管理配置目录

### 新增
- `agents/assessment/risk-compliance/prompt.md` - 新建风险与合规Agent，整合风险评估和合规检查职责

### 修改
- `agents/README.md` - 更新团队结构为11个Agent，新增v2.0版本说明
- `agents/orchestrator/prompt.md` - 新增应急响应流程（PDCERF）、事件分级、团队列表更新为11个Agent
- `agents/defense/threat-response/prompt.md` - 更新协作关系，从orchestrator接收指令
- `agents/assessment/vuln-assessment/prompt.md` - 扩展渗透测试能力，新增工作模式、风险等级确认要求
- `agents/operations/server-ops/prompt.md` - 新增补丁管理职责、更新协作关系
- `README.md` - 更新为11个Agent，更新团队结构、Agent列表、工作流程示例
- `team-framework/agents/orchestrator.json` - description更新为11个Agent

### 优化效果
- Agent数量：15 → 11（减少27%）
- 职责边界：清晰明确
- 启动开销：降低
- 协调链路：缩短

---

## 2026-02-26

### 新增
- `agents/orchestrator/orchestrator.md` - 新增变更管理职责，包括变更申请受理、风险评估、审批协调、实施调度、记录审计
- `agents/orchestrator/prompt.md` - 新增变更管理相关职责说明、变更分类、风险等级矩阵
- `agents/orchestrator/orchestrator.md` - 新增变更管理流程说明
- `agents/orchestrator/orchestrator.md` - 新增变更风险评估框架、风险维度、风险等级矩阵、变更状态定义

### 修改
- `agents/README.md:239-262` - 运维管理组从5个agent调整为4个，移除change-manager
- `agents/README.md:278-290` - 删除变更管理Agent章节
- `agents/README.md:284-295` - 更新协作矩阵，运维变更场景从"变更管理→网络运维"改为"AI协调器→运维Agent"
- `agents/README.md:340-345` - 更新团队版本为v1.4，Agent数量从16更新为15，最后更新日期改为2026年2月26日
- `agents/README.md:347-368` - 新增v1.4版本更新说明，记录变更内容
- `agents/orchestrator/orchestrator.md:26-33` - 核心职责新增变更管理
- `agents/orchestrator/orchestrator.md:15-23` - 专业领域新增变更管理全流程协调
- `agents/orchestrator/orchestrator.md:54-62` - 输出新增变更风险评估报告、变更审批请求、变更实施指令、变更状态报告
- `agents/orchestrator/orchestrator.md:127-130` - 管理的Agent列表移除变更管理Agent
- `agents/orchestrator/orchestrator.md:239-269` - 新增变更管理流程章节
- `agents/orchestrator/orchestrator.md:259-275` - 新增变更风险评估框架章节
- `agents/orchestrator/prompt.md:48` - 管理的Agent数量从16更新为15
- `agents/orchestrator/prompt.md:68-71` - 运维管理组移除变更管理Agent
- `agents/orchestrator/prompt.md:114-170` - 核心职责新增变更管理协调，包括变更申请受理、风险评估、审批协调、实施调度、回滚管理、记录审计
- `agents/orchestrator/prompt.md:122-126` - 新增变更分类表格
- `agents/orchestrator/prompt.md:128-131` - 新增变更流程
- `agents/orchestrator/prompt.md:133-142` - 新增风险等级矩阵
- `agents/operations/network-ops/prompt.md:134-136` - 协作关系移除变更管理Agent，改为从AI协调器接收变更指令
- `agents/operations/server-ops/prompt.md:284-293` - 主要协作Agent移除change-manager，新增上报AI协调器的详细说明
- `agents/operations/patch-mgmt/prompt.md:38-41` - 协作关系新增上报AI协调器（补丁部署结果、资产更新通知）
- `agents/monitoring/asset-mgmt/prompt.md:54-67` - 运维agents职责从(network-ops、server-ops、endpoint-ops)更新为(network-ops、server-ops、patch-mgmt)
- `agents/monitoring/asset-mgmt/prompt.md:59-67` - 核心原则更新变更流程，新增AI协调器进行变更风险评估和审批协调的步骤
- `agents/monitoring/asset-mgmt/prompt.md:76-79` - 输入资产变更通知来源新增AI协调器

### 删除
- `agents/operations/change-manager/` - 整个变更管理Agent目录及其所有内容

### 修复
- **变更管理职责重叠问题** - 原change-manager职责与Orchestrator重叠严重，删除后将变更管理职责整合到Orchestrator
- **协作链条过长问题** - 原流程Orchestrator→change-manager→运维Agent存在多层转发，简化为Orchestrator→运维Agent
- **审批流程传声筒问题** - 原change-manager在审批环节只能传话无决策权，删除后由Orchestrator直接协调人类审批
