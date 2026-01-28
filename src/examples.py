"""
2026上半年奖金计算引擎 - 使用示例
Example usage of the bonus calculation engine
"""
from config import GlobalConfig, CompletionBonusMode, CompletionRateMode, Role
from models import PersonData
from bonus_engine import BonusCalculator, calculate_bonus
import json


def example_cp():
    """常委奖金计算示例"""
    print("=" * 60)
    print("【示例1】常委 CP 奖金计算")
    print("=" * 60)
    
    person = PersonData(
        name="王总",
        role=Role.CP,
        region="全国",
        org_unit="总部",
        collection_rate=0.95,
        region_completed_90=True,
        region_completed_100=True,
        national_completed_90=True,
        national_completed_100=False,  # 全国未完成100%
        ceo_bonus=50000
    )
    
    detail, validation = calculate_bonus(person)
    
    print(f"\n姓名: {detail.name}")
    print(f"岗位: {detail.role.value}")
    print("-" * 40)
    print(f"固定补贴: ¥{detail.fixed_subsidy:,.0f}")
    print(f"大区90%奖: ¥{detail.region_bonus_90:,.0f}")
    print(f"大区100%奖: ¥{detail.region_bonus_100:,.0f}")
    print(f"全国90%奖: ¥{detail.national_bonus_90:,.0f}")
    print(f"全国100%奖: ¥{detail.national_bonus_100:,.0f}")
    print(f"CEO奖金: ¥{detail.ceo_bonus:,.0f}")
    print("-" * 40)
    print(f"【奖金合计】: ¥{detail.grand_total:,.0f}")
    
    return detail


def example_dm():
    """总经理奖金计算示例"""
    print("\n" + "=" * 60)
    print("【示例2】总经理 DM 奖金计算")
    print("=" * 60)
    
    person = PersonData(
        name="李总",
        role=Role.DM,
        region="华北",
        org_unit="北京分公司",
        month_revenue={
            1: 500000,
            2: 600000,
            3: 700000,
            4: 800000,
            5: 750000,
            6: 650000
        },
        company_total_revenue=4000000,  # 分公司总产值
        annual_target=3800000,           # 年度目标
        collection_rate=0.92,
        region_completed_90=True,
        region_completed_100=False,
        ceo_bonus=20000
    )
    
    detail, validation = calculate_bonus(person)
    
    print(f"\n姓名: {detail.name}")
    print(f"岗位: {detail.role.value}")
    print(f"完成率: {detail.completion_rate*100:.1f}%")
    print(f"回款率: {detail.collection_rate*100:.1f}%")
    print("-" * 40)
    print("【过程激励明细】")
    for month, amount in detail.monthly_incentives.items():
        print(f"  {month}月: ¥{amount:,.0f}")
    print(f"  小计: ¥{detail.incentive_total:,.0f}")
    print("-" * 40)
    print("【完成奖】")
    print(f"  叠加模式: {detail.completion_bonus_mode}")
    print(f"  90%档: ¥{detail.completion_bonus_90:,.0f}")
    print(f"  100%档: ¥{detail.completion_bonus_100:,.0f}")
    print(f"  小计: ¥{detail.completion_bonus_total:,.0f}")
    print("-" * 40)
    print(f"大区完成奖: ¥{detail.region_bonus_total:,.0f}")
    print(f"CEO奖金: ¥{detail.ceo_bonus:,.0f}")
    print("-" * 40)
    print(f"【奖金合计】: ¥{detail.grand_total:,.0f}")
    
    if detail.pending_confirmations:
        print("\n⚠️ 待确认项:")
        for item in detail.pending_confirmations:
            print(f"  - {item}")
    
    return detail


def example_sales():
    """销售人员奖金计算示例"""
    print("\n" + "=" * 60)
    print("【示例3】销售-新购 奖金计算")
    print("=" * 60)
    
    person = PersonData(
        name="张三",
        role=Role.SALES_NEW,
        region="华东",
        org_unit="上海分公司",
        month_revenue={
            1: 80000,
            2: 90000,
            3: 100000,
            4: 110000,
            5: 95000,
            6: 85000
        },
        company_total_revenue=2000000,
        annual_target=550000,
        collection_rate=0.88,
        personal_allocation_ratio=0.3,  # 个人分配30%
        ceo_bonus=5000
    )
    
    detail, validation = calculate_bonus(person)
    
    print(f"\n姓名: {detail.name}")
    print(f"岗位: {detail.role.value}")
    print(f"完成率: {detail.completion_rate*100:.1f}%")
    print(f"回款率: {detail.collection_rate*100:.1f}%")
    print("-" * 40)
    print("【过程激励明细】")
    for month, amount in detail.monthly_incentives.items():
        print(f"  {month}月: ¥{amount:,.0f}")
    print(f"  小计: ¥{detail.incentive_total:,.0f}")
    print("-" * 40)
    print(f"固定补贴: ¥{detail.fixed_subsidy:,.0f}")
    print("-" * 40)
    print("【完成奖】")
    print(f"  叠加模式: {detail.completion_bonus_mode}")
    print(f"  个人分配比例: {detail.personal_allocation_ratio*100:.0f}%")
    print(f"  90%档: ¥{detail.completion_bonus_90:,.0f}")
    print(f"  100%档: ¥{detail.completion_bonus_100:,.0f}")
    print(f"  小计(个人): ¥{detail.completion_bonus_total:,.0f}")
    print("-" * 40)
    print(f"CEO奖金: ¥{detail.ceo_bonus:,.0f}")
    print("-" * 40)
    print(f"【奖金合计】: ¥{detail.grand_total:,.0f}")
    
    if validation.warnings:
        print("\nℹ️ 提示信息:")
        for warning in validation.warnings:
            print(f"  - {warning}")
    
    if detail.pending_confirmations:
        print("\n⚠️ 待确认项:")
        for item in detail.pending_confirmations:
            print(f"  - {item}")
    
    return detail


def example_custom_config():
    """自定义配置示例"""
    print("\n" + "=" * 60)
    print("【示例4】使用自定义配置")
    print("=" * 60)
    
    # 创建自定义配置：DM使用stack模式
    custom_config = GlobalConfig(
        dm_completion_bonus_mode=CompletionBonusMode.STACK,  # 改为叠加
        threshold_90=0.80,  # 降低90%门槛
        include_payout_timing=True  # 显示50/50拆分
    )
    
    calculator = BonusCalculator(global_config=custom_config)
    
    person = PersonData(
        name="赵经理",
        role=Role.DM,
        region="华南",
        org_unit="深圳分公司",
        month_revenue={1: 300000, 2: 350000, 3: 400000, 4: 450000, 5: 420000, 6: 380000},
        company_total_revenue=2300000,
        annual_target=2000000,
        collection_rate=0.95,
        region_completed_90=True,
        region_completed_100=True
    )
    
    detail, validation = calculator.calculate_person(person)
    
    print(f"\n配置说明:")
    print(f"  - DM叠加模式: {custom_config.dm_completion_bonus_mode.value}")
    print(f"  - 90%回款门槛: {custom_config.threshold_90*100:.0f}%")
    print(f"  - 显示发放拆分: {custom_config.include_payout_timing}")
    print("-" * 40)
    print(f"姓名: {detail.name}")
    print(f"完成率: {detail.completion_rate*100:.1f}%")
    print("-" * 40)
    print("【过程激励】")
    print(f"  总额: ¥{detail.incentive_total:,.0f}")
    print(f"  即时发放(50%): ¥{detail.incentive_immediate:,.0f}")
    print(f"  回款后发放(50%): ¥{detail.incentive_after_collection:,.0f}")
    print("-" * 40)
    print("【完成奖】(stack模式)")
    print(f"  90%档: ¥{detail.completion_bonus_90:,.0f}")
    print(f"  100%档: ¥{detail.completion_bonus_100:,.0f}")
    print(f"  叠加小计: ¥{detail.completion_bonus_total:,.0f}")
    print("-" * 40)
    print(f"【奖金合计】: ¥{detail.grand_total:,.0f}")
    
    return detail


def example_validation_errors():
    """数据校验错误示例"""
    print("\n" + "=" * 60)
    print("【示例5】数据校验示例")
    print("=" * 60)
    
    # 故意设置错误数据
    person = PersonData(
        name="测试员",
        role=Role.MGR,
        region="华北",
        org_unit="北京分公司",
        month_revenue={1: 100000, 2: -50000},  # 负数产值
        annual_target=0,  # 目标为0
        collection_rate=1.5,  # 超过100%
        personal_allocation_ratio=1.2  # 超过100%
    )
    
    detail, validation = calculate_bonus(person)
    
    print(f"\n校验结果: {'通过' if validation.is_valid else '失败'}")
    
    if validation.errors:
        print("\n❌ 错误项:")
        for error in validation.errors:
            print(f"  - {error}")
    
    if validation.warnings:
        print("\n⚠️ 警告项:")
        for warning in validation.warnings:
            print(f"  - {warning}")


def example_batch_calculation():
    """批量计算示例"""
    print("\n" + "=" * 60)
    print("【示例6】批量计算示例")
    print("=" * 60)
    
    persons = [
        PersonData(
            name="常委A", role=Role.CP, region="全国", org_unit="总部",
            collection_rate=0.95,
            region_completed_90=True, region_completed_100=True,
            national_completed_90=True, national_completed_100=True
        ),
        PersonData(
            name="总经理B", role=Role.DM, region="华北", org_unit="北京分公司",
            month_revenue={1: 500000, 2: 600000, 3: 700000, 4: 800000, 5: 750000, 6: 650000},
            company_total_revenue=4000000, annual_target=3500000,
            collection_rate=0.92, region_completed_90=True
        ),
        PersonData(
            name="销售C", role=Role.SALES_NEW, region="华东", org_unit="上海分公司",
            month_revenue={1: 80000, 2: 90000, 3: 100000, 4: 110000, 5: 95000, 6: 85000},
            company_total_revenue=2000000, annual_target=500000,
            collection_rate=0.90, personal_allocation_ratio=0.25
        )
    ]
    
    calculator = BonusCalculator()
    results = calculator.calculate_batch(persons)
    
    print("\n【批量计算结果汇总】")
    print("-" * 60)
    print(f"{'姓名':<10} {'岗位':<12} {'过程激励':>12} {'完成奖':>12} {'其他':>10} {'合计':>12}")
    print("-" * 60)
    
    total = 0
    for detail, validation in results:
        other = detail.region_bonus_total + detail.national_bonus_total + detail.fixed_subsidy + detail.ceo_bonus
        print(f"{detail.name:<10} {detail.role.value:<12} "
              f"¥{detail.incentive_total:>10,.0f} ¥{detail.completion_bonus_total:>10,.0f} "
              f"¥{other:>8,.0f} ¥{detail.grand_total:>10,.0f}")
        total += detail.grand_total
    
    print("-" * 60)
    print(f"{'总计':<24} {' ':>24} ¥{total:>10,.0f}")


def main():
    """运行所有示例"""
    example_cp()
    example_dm()
    example_sales()
    example_custom_config()
    example_validation_errors()
    example_batch_calculation()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
