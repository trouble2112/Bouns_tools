# 2026上半年奖金计算工具 V1.0

## 项目结构

```
bonus_calculator/
├── README.md                    # 项目说明
├── docs/
│   ├── EXCEL_TEMPLATE_DESIGN.md # Excel模板详细设计文档
│   └── CONFIRM_LIST.md          # 待业务确认问题清单
└── src/
    ├── __init__.py              # 包初始化
    ├── config.py                # 配置参数定义
    ├── models.py                # 数据模型定义
    ├── validators.py            # 数据校验模块
    ├── bonus_engine.py          # 核心计算引擎
    ├── excel_exporter.py        # Excel导出模块
    └── examples.py              # 使用示例
```

## 整体方案摘要

### 1. 解决方案架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        奖金计算工具                                   │
├─────────────────────────────────────────────────────────────────────┤
│  输入层                                                              │
│  ├── 全局参数表（时间系数、回款门槛、叠加模式等）                        │
│  ├── 人员基础信息表（姓名、岗位、区域、组织单元）                        │
│  └── 产值数据表（1-6月产值、目标、回款率、完成情况）                     │
├─────────────────────────────────────────────────────────────────────┤
│  计算层                                                              │
│  ├── 过程激励计算（产值 × 比例 × 时间系数）                            │
│  ├── 完成奖计算（含90%/100%叠加逻辑）                                  │
│  ├── 区域/全国奖计算                                                  │
│  └── 补贴 + CEO奖汇总                                                │
├─────────────────────────────────────────────────────────────────────┤
│  输出层                                                              │
│  ├── 各岗位奖金明细表                                                 │
│  └── 汇总报表（分岗位、分区域、总计）                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. 核心设计原则

1. **参数化设计**：所有可能有歧义或可能变化的规则都做成可配置参数
2. **数据校验前置**：输入时即校验，避免计算时出错
3. **计算透明化**：每个奖金项单独展示，可追溯计算过程
4. **待确认标记**：对规则歧义点明确标记，便于业务确认后调整

### 3. 岗位奖金结构速查

| 岗位 | 代码 | 过程激励 | 完成奖 | 区域奖 | 全国奖 | 固定补贴 | CEO奖 |
|------|------|---------|--------|--------|--------|---------|-------|
| 常委 | CP | - | - | 30K×2档 | 40K×2档 | 60K | ✓ |
| 总经理 | DM | 0.4% | 0.4%(cap 40K)×2档 | 40K | - | - | ✓ |
| 副总经理 | VP | 0.4% | 1.5%×2档 | - | - | - | ✓ |
| 部门经理 | MGR | 1.0% | 1.5%×2档 | - | - | - | ✓ |
| 销售-用户部 | SALES_USER | 2.0% | 1.5%×2档 | - | - | - | ✓ |
| 销售-新购 | SALES_NEW | 3.0% | 1.5%×2档 | - | - | 4.8K | ✓ |
| 销售-高校 | SALES_EDU | 3.0% | 1.5%×2档 | - | - | 4.8K | ✓ |

---

## 快速开始

### 安装依赖

```bash
pip install openpyxl  # Excel导出功能需要
```

### Python引擎使用

```python
from config import Role, GlobalConfig
from models import PersonData
from bonus_engine import calculate_bonus

# 创建人员数据
person = PersonData(
    name="张三",
    role=Role.DM,
    region="华北",
    org_unit="北京分公司",
    month_revenue={1: 500000, 2: 600000, 3: 700000, 4: 800000, 5: 750000, 6: 650000},
    company_total_revenue=4000000,
    annual_target=3800000,
    collection_rate=0.92,
    region_completed_90=True
)

# 计算奖金
detail, validation = calculate_bonus(person)
print(f"奖金合计: ¥{detail.grand_total:,.0f}")
```

### 自定义配置

```python
from config import GlobalConfig, CompletionBonusMode

custom_config = GlobalConfig(
    dm_completion_bonus_mode=CompletionBonusMode.STACK,  # DM改为叠加
    threshold_90=0.80,  # 降低90%门槛
    include_payout_timing=True  # 显示50/50拆分
)

from bonus_engine import BonusCalculator
calculator = BonusCalculator(global_config=custom_config)
```

### 导出Excel

```python
from excel_exporter import create_excel_template, export_to_excel

create_excel_template("bonus_template.xlsx")
results = calculator.calculate_batch(persons)
export_to_excel(results, "bonus_results.xlsx")
```

---

## 待确认问题（详见 docs/CONFIRM_LIST.md）

| 序号 | 问题 | 默认处理 | 优先级 |
|------|------|---------|--------|
| 1 | 90%/100%完成奖叠加模式 | DM=exclusive, 其他=stack | ⚠️ 高 |
| 2 | 回款率门槛值 | 85%/90% | ⚠️ 高 |
| 3 | 50/50发放是否拆分显示 | 只算总额 | 中 |
| 4 | 个人分配比例来源 | 手工输入 | 中 |
| 5 | DM完成奖cap适用范围 | 单档cap 40000 | ⚠️ 高 |

---

## 数据校验规则

| 字段 | 校验规则 | 错误级别 |
|------|---------|---------|
| 回款率 | 0 ≤ 值 ≤ 1 | 错误 |
| 产值 | ≥ 0 | 错误 |
| 分配比例 | 0 ≤ 值 ≤ 1 | 错误 |
| 同组织分配合计 | ≤ 1 | 警告 |
| 完成率 | 0 ≤ 值 ≤ 2 | 警告(>2时) |

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-01-28 | 初始版本 |
