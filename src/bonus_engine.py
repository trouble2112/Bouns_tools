"""
2026上半年奖金计算引擎 - 核心计算模块
Core calculation engine for bonus computation

【设计原则】
1. 每个岗位有独立的calculate方法
2. 所有规则参数化，通过config配置
3. 计算过程透明，返回明细
4. 对歧义规则标记"待确认"
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from models import PersonData, BonusDetail, ValidationResult
from config import (
    GlobalConfig, RoleConfig, Role,
    CompletionBonusMode, CompletionRateMode,
    DEFAULT_GLOBAL_CONFIG, DEFAULT_ROLE_CONFIG
)
from validators import BonusValidator


class BonusCalculator:
    """奖金计算引擎"""
    
    def __init__(
        self, 
        global_config: GlobalConfig = None,
        role_config: RoleConfig = None
    ):
        self.global_config = global_config or DEFAULT_GLOBAL_CONFIG
        self.role_config = role_config or DEFAULT_ROLE_CONFIG
        self.validator = BonusValidator(self.global_config)
    
    def calculate_person(
        self, 
        person: PersonData, 
        skip_validation: bool = False
    ) -> Tuple[BonusDetail, ValidationResult]:
        """
        计算单人奖金
        
        Args:
            person: 人员数据
            skip_validation: 是否跳过校验
        
        Returns:
            (奖金明细, 校验结果)
        """
        # 数据校验
        validation = ValidationResult() if skip_validation else self.validator.validate_person(person)
        
        # 根据岗位调用对应计算方法
        if person.role == Role.CP:
            detail = self._calculate_cp(person)
        elif person.role == Role.DM:
            detail = self._calculate_dm(person)
        elif person.role in [Role.VP, Role.MGR]:
            detail = self._calculate_management(person)
        else:  # SALES_*
            detail = self._calculate_sales(person)
        
        # 合并校验警告到明细
        detail.warnings.extend(validation.warnings)
        
        return detail, validation
    
    def calculate_batch(
        self, 
        persons: List[PersonData]
    ) -> List[Tuple[BonusDetail, ValidationResult]]:
        """批量计算"""
        results = []
        
        # 先进行批量校验（包括组内分配比例）
        validations = self.validator.validate_batch(persons)
        
        # 逐人计算
        for person in persons:
            detail, _ = self.calculate_person(person, skip_validation=True)
            validation = validations.get(person.name, ValidationResult())
            detail.warnings.extend(validation.warnings)
            results.append((detail, validation))
        
        return results
    
    # ========== 常委CP计算 ==========
    def _calculate_cp(self, person: PersonData) -> BonusDetail:
        """
        常委奖金计算
        
        规则：
        - 固定补贴：60000（按月10000*6）
        - 大区90%奖：30000（若区域完成90%）
        - 大区100%奖：30000（若区域完成100%）
        - 全国90%奖：40000（若全国完成90%）
        - 全国100%奖：40000（若全国完成100%）
        - CEO奖：手动输入
        """
        detail = BonusDetail(
            name=person.name,
            role=person.role,
            region=person.region,
            org_unit=person.org_unit,
            collection_rate=person.collection_rate
        )
        
        cfg = self.global_config
        
        # 固定补贴
        detail.fixed_subsidy = cfg.cp_subsidy
        
        # 大区奖
        if person.region_completed_90:
            detail.region_bonus_90 = cfg.region_90_bonus
        if person.region_completed_100:
            detail.region_bonus_100 = cfg.region_100_bonus
        detail.region_bonus_total = detail.region_bonus_90 + detail.region_bonus_100
        
        # 全国奖
        if person.national_completed_90:
            detail.national_bonus_90 = cfg.national_90_bonus
        if person.national_completed_100:
            detail.national_bonus_100 = cfg.national_100_bonus
        detail.national_bonus_total = detail.national_bonus_90 + detail.national_bonus_100
        
        # CEO奖金
        detail.ceo_bonus = person.ceo_bonus or 0.0
        
        # 计算总计
        detail.calculate_total()
        
        return detail
    
    # ========== 总经理DM计算 ==========
    def _calculate_dm(self, person: PersonData) -> BonusDetail:
        """
        总经理奖金计算
        
        规则：
        - 过程激励：sum(月产值 * 0.4% * 时间系数)
        - 分公司完成90%奖：若完成率>=0.9且回款率>=门槛 -> min(分公司产值*0.4%, 40000)
        - 分公司完成100%奖：若完成率>=1.0且回款率>=门槛 -> min(分公司产值*0.4%, 40000)
        - 大区完成奖：40000（若区域完成）
        - CEO奖：手动输入
        - 叠加模式：默认exclusive（待确认）
        """
        detail = BonusDetail(
            name=person.name,
            role=person.role,
            region=person.region,
            org_unit=person.org_unit,
            collection_rate=person.collection_rate
        )
        
        cfg = self.global_config
        role_cfg = self.role_config
        
        # 过程激励
        incentive_rate = role_cfg.incentive_rates[Role.DM]
        detail.monthly_incentives = self._calculate_monthly_incentives(
            person.month_revenue, incentive_rate
        )
        detail.incentive_total = sum(detail.monthly_incentives.values())
        
        # 处理50/50拆分
        if cfg.include_payout_timing:
            detail.incentive_immediate = detail.incentive_total * 0.5
            detail.incentive_after_collection = detail.incentive_total * 0.5
        
        # 计算完成率
        completion_rate = self._get_completion_rate(person)
        detail.completion_rate = completion_rate
        
        # 分公司产值
        company_revenue = person.get_company_revenue()
        
        # 分公司完成奖
        bonus_base = min(company_revenue * role_cfg.dm_completion_bonus_rate, cfg.dm_completion_bonus_cap)
        
        # 90%档
        if completion_rate >= 0.9 and person.collection_rate >= cfg.threshold_90:
            detail.completion_bonus_90 = bonus_base
        
        # 100%档
        if completion_rate >= 1.0 and person.collection_rate >= cfg.threshold_100:
            detail.completion_bonus_100 = bonus_base
        
        # 应用叠加模式
        detail.completion_bonus_mode = cfg.dm_completion_bonus_mode.value
        if cfg.dm_completion_bonus_mode == CompletionBonusMode.EXCLUSIVE:
            # exclusive: 只取最高档
            detail.completion_bonus_total = max(detail.completion_bonus_90, detail.completion_bonus_100)
            detail.pending_confirmations.append(
                "DM完成奖使用exclusive模式（仅发最高档）[待业务确认]"
            )
        else:
            # stack: 叠加
            detail.completion_bonus_total = detail.completion_bonus_90 + detail.completion_bonus_100
        
        # 大区完成奖
        if person.region_completed_90 or person.region_completed_100:
            detail.region_bonus_total = cfg.dm_region_bonus
        
        # CEO奖金
        detail.ceo_bonus = person.ceo_bonus or 0.0
        
        # 计算总计
        detail.calculate_total()
        
        return detail
    
    # ========== 管理层计算 (副总经理/部门经理) ==========
    def _calculate_management(self, person: PersonData) -> BonusDetail:
        """
        副总经理/部门经理奖金计算
        
        规则：
        - 过程激励：副总经理0.4%, 部门经理1.0%
        - 分公司完成奖（总额）：分公司产值 * 1.5%
        - 个人完成奖：完成奖总额 * 个人分配比例
        - 叠加模式：默认stack（待确认）
        """
        detail = BonusDetail(
            name=person.name,
            role=person.role,
            region=person.region,
            org_unit=person.org_unit,
            collection_rate=person.collection_rate,
            personal_allocation_ratio=person.personal_allocation_ratio
        )
        
        cfg = self.global_config
        role_cfg = self.role_config
        
        # 过程激励
        incentive_rate = role_cfg.incentive_rates[person.role]
        detail.monthly_incentives = self._calculate_monthly_incentives(
            person.month_revenue, incentive_rate
        )
        detail.incentive_total = sum(detail.monthly_incentives.values())
        
        # 处理50/50拆分
        if cfg.include_payout_timing:
            detail.incentive_immediate = detail.incentive_total * 0.5
            detail.incentive_after_collection = detail.incentive_total * 0.5
        
        # 计算完成率
        completion_rate = self._get_completion_rate(person)
        detail.completion_rate = completion_rate
        
        # 分公司产值
        company_revenue = person.get_company_revenue()
        
        # 完成奖基数
        bonus_base = company_revenue * role_cfg.completion_bonus_rate
        
        # 90%档
        if completion_rate >= 0.9 and person.collection_rate >= cfg.threshold_90:
            detail.completion_bonus_90 = bonus_base
        
        # 100%档
        if completion_rate >= 1.0 and person.collection_rate >= cfg.threshold_100:
            detail.completion_bonus_100 = bonus_base
        
        # 应用叠加模式
        detail.completion_bonus_mode = cfg.other_completion_bonus_mode.value
        if cfg.other_completion_bonus_mode == CompletionBonusMode.EXCLUSIVE:
            detail.completion_bonus_total = max(detail.completion_bonus_90, detail.completion_bonus_100)
        else:
            # stack: 叠加
            detail.completion_bonus_total = detail.completion_bonus_90 + detail.completion_bonus_100
            detail.pending_confirmations.append(
                f"{person.role.value}完成奖使用stack模式（90%+100%叠加）[待业务确认]"
            )
        
        # 应用个人分配比例
        if person.personal_allocation_ratio is not None:
            detail.completion_bonus_total *= person.personal_allocation_ratio
            detail.warnings.append(
                f"完成奖已按个人分配比例{person.personal_allocation_ratio*100:.1f}%计算"
            )
        else:
            detail.warnings.append("未设置个人分配比例，显示完成奖总额")
        
        # CEO奖金
        detail.ceo_bonus = person.ceo_bonus or 0.0
        
        # 计算总计
        detail.calculate_total()
        
        return detail
    
    # ========== 销售计算 ==========
    def _calculate_sales(self, person: PersonData) -> BonusDetail:
        """
        销售人员奖金计算
        
        规则：
        - 过程激励：用户部2%, 新购/高校3%
        - 固定补贴：新购/高校 800/月
        - 分公司完成奖：分公司产值 * 1.5%
        - 叠加模式：默认stack（待确认）
        """
        detail = BonusDetail(
            name=person.name,
            role=person.role,
            region=person.region,
            org_unit=person.org_unit,
            collection_rate=person.collection_rate,
            personal_allocation_ratio=person.personal_allocation_ratio
        )
        
        cfg = self.global_config
        role_cfg = self.role_config
        
        # 过程激励
        incentive_rate = role_cfg.incentive_rates[person.role]
        detail.monthly_incentives = self._calculate_monthly_incentives(
            person.month_revenue, incentive_rate
        )
        detail.incentive_total = sum(detail.monthly_incentives.values())
        
        # 处理50/50拆分
        if cfg.include_payout_timing:
            detail.incentive_immediate = detail.incentive_total * 0.5
            detail.incentive_after_collection = detail.incentive_total * 0.5
        
        # 固定补贴 (新购/高校)
        if role_cfg.has_fixed_subsidy.get(person.role, False):
            detail.fixed_subsidy = cfg.sales_monthly_subsidy * 6  # 半年
        
        # 计算完成率
        completion_rate = self._get_completion_rate(person)
        detail.completion_rate = completion_rate
        
        # 分公司产值
        company_revenue = person.get_company_revenue()
        
        # 完成奖基数
        bonus_base = company_revenue * role_cfg.completion_bonus_rate
        
        # 90%档
        if completion_rate >= 0.9 and person.collection_rate >= cfg.threshold_90:
            detail.completion_bonus_90 = bonus_base
        
        # 100%档
        if completion_rate >= 1.0 and person.collection_rate >= cfg.threshold_100:
            detail.completion_bonus_100 = bonus_base
        
        # 应用叠加模式
        detail.completion_bonus_mode = cfg.other_completion_bonus_mode.value
        if cfg.other_completion_bonus_mode == CompletionBonusMode.EXCLUSIVE:
            detail.completion_bonus_total = max(detail.completion_bonus_90, detail.completion_bonus_100)
        else:
            detail.completion_bonus_total = detail.completion_bonus_90 + detail.completion_bonus_100
            detail.pending_confirmations.append(
                f"{person.role.value}完成奖使用stack模式（90%+100%叠加）[待业务确认]"
            )
        
        # 应用个人分配比例
        if person.personal_allocation_ratio is not None:
            detail.completion_bonus_total *= person.personal_allocation_ratio
            detail.warnings.append(
                f"完成奖已按个人分配比例{person.personal_allocation_ratio*100:.1f}%计算"
            )
        else:
            detail.warnings.append("未设置个人分配比例，显示完成奖总额")
        
        # CEO奖金
        detail.ceo_bonus = person.ceo_bonus or 0.0
        
        # 计算总计
        detail.calculate_total()
        
        return detail
    
    # ========== 辅助方法 ==========
    def _calculate_monthly_incentives(
        self, 
        month_revenue: Dict[int, float],
        rate: float
    ) -> Dict[int, float]:
        """计算月度过程激励"""
        result = {}
        for month in range(1, 7):
            revenue = month_revenue.get(month, 0.0)
            coeff = self.global_config.time_coefficients.get(month, 1.0)
            result[month] = revenue * rate * coeff
        return result
    
    def _get_completion_rate(self, person: PersonData) -> float:
        """获取完成率（根据配置模式）"""
        if self.global_config.completion_rate_mode == CompletionRateMode.FROM_TARGET:
            if person.annual_target and person.annual_target > 0:
                return person.get_total_revenue() / person.annual_target
            return 0.0
        else:
            return person.completion_rate_manual or 0.0
    
    # ========== 报表导出 ==========
    def export_to_dict(self, detail: BonusDetail) -> dict:
        """将明细转换为字典格式"""
        return {
            "基本信息": {
                "姓名": detail.name,
                "岗位": detail.role.value,
                "区域": detail.region,
                "组织单元": detail.org_unit
            },
            "过程激励": {
                "1月": detail.monthly_incentives.get(1, 0),
                "2月": detail.monthly_incentives.get(2, 0),
                "3月": detail.monthly_incentives.get(3, 0),
                "4月": detail.monthly_incentives.get(4, 0),
                "5月": detail.monthly_incentives.get(5, 0),
                "6月": detail.monthly_incentives.get(6, 0),
                "小计": detail.incentive_total,
                "即时发放(50%)": detail.incentive_immediate,
                "回款后发放(50%)": detail.incentive_after_collection
            },
            "完成奖": {
                "90%档": detail.completion_bonus_90,
                "100%档": detail.completion_bonus_100,
                "叠加模式": detail.completion_bonus_mode,
                "小计": detail.completion_bonus_total,
                "个人分配比例": detail.personal_allocation_ratio
            },
            "区域奖": {
                "90%档": detail.region_bonus_90,
                "100%档": detail.region_bonus_100,
                "小计": detail.region_bonus_total
            },
            "全国奖": {
                "90%档": detail.national_bonus_90,
                "100%档": detail.national_bonus_100,
                "小计": detail.national_bonus_total
            },
            "其他": {
                "固定补贴": detail.fixed_subsidy,
                "CEO奖金": detail.ceo_bonus
            },
            "合计": detail.grand_total,
            "参考数据": {
                "完成率": f"{detail.completion_rate*100:.1f}%",
                "回款率": f"{detail.collection_rate*100:.1f}%"
            },
            "警告": detail.warnings,
            "待确认项": detail.pending_confirmations
        }


# ========== 便捷函数 ==========
def calculate_bonus(
    person: PersonData,
    config: GlobalConfig = None
) -> Tuple[BonusDetail, ValidationResult]:
    """
    便捷函数：计算单人奖金
    
    Example:
        >>> person = PersonData(
        ...     name="张三",
        ...     role=Role.DM,
        ...     region="华北",
        ...     org_unit="北京分公司",
        ...     month_revenue={1: 100000, 2: 120000, 3: 150000, 4: 130000, 5: 140000, 6: 160000},
        ...     annual_target=800000,
        ...     collection_rate=0.92,
        ...     region_completed_90=True
        ... )
        >>> detail, validation = calculate_bonus(person)
        >>> print(detail.grand_total)
    """
    calculator = BonusCalculator(global_config=config)
    return calculator.calculate_person(person)


def calculate_bonus_batch(
    persons: List[PersonData],
    config: GlobalConfig = None
) -> List[Tuple[BonusDetail, ValidationResult]]:
    """便捷函数：批量计算奖金"""
    calculator = BonusCalculator(global_config=config)
    return calculator.calculate_batch(persons)
