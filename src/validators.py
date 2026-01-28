"""
2026上半年奖金计算引擎 - 数据校验模块
Data validation module for bonus calculation
"""
from typing import List, Dict, Optional
from models import PersonData, ValidationResult
from config import Role, GlobalConfig


class BonusValidator:
    """奖金数据校验器"""
    
    def __init__(self, config: GlobalConfig = None):
        self.config = config or GlobalConfig()
    
    def validate_person(self, person: PersonData) -> ValidationResult:
        """校验单人数据"""
        result = ValidationResult()
        
        # 1. 基本信息校验
        self._validate_basic_info(person, result)
        
        # 2. 产值数据校验
        self._validate_revenue(person, result)
        
        # 3. 回款率校验
        self._validate_collection_rate(person, result)
        
        # 4. 完成率校验
        self._validate_completion_rate(person, result)
        
        # 5. 分配比例校验
        self._validate_allocation_ratio(person, result)
        
        # 6. CEO奖金校验
        self._validate_ceo_bonus(person, result)
        
        # 7. 岗位特定校验
        self._validate_role_specific(person, result)
        
        return result
    
    def validate_batch(self, persons: List[PersonData]) -> Dict[str, ValidationResult]:
        """批量校验"""
        results = {}
        for person in persons:
            results[person.name] = self.validate_person(person)
        
        # 校验组内分配比例合计
        self._validate_group_allocation(persons, results)
        
        return results
    
    def _validate_basic_info(self, person: PersonData, result: ValidationResult):
        """校验基本信息"""
        if not person.name or not person.name.strip():
            result.add_error("姓名不能为空")
        
        if not person.region or not person.region.strip():
            result.add_error("区域不能为空")
        
        if not person.org_unit or not person.org_unit.strip():
            result.add_error("组织单元不能为空")
        
        # 岗位有效性已通过枚举类型约束
    
    def _validate_revenue(self, person: PersonData, result: ValidationResult):
        """校验产值数据"""
        # 检查是否有产值数据
        if not person.month_revenue:
            result.add_warning("未填写任何月度产值")
        
        # 检查产值非负
        for month, revenue in person.month_revenue.items():
            if revenue < 0:
                result.add_error(f"{month}月产值不能为负数: {revenue}")
        
        # 检查月份有效性 (1-6月)
        for month in person.month_revenue.keys():
            if month < 1 or month > 6:
                result.add_error(f"无效的月份: {month}")
        
        # 非常委岗位需要分公司产值
        if person.role != Role.CP:
            if person.company_total_revenue is None:
                # 如果未设置分公司产值，将使用个人产值
                result.add_warning("未填写分公司总产值，将使用个人产值计算")
            elif person.company_total_revenue < 0:
                result.add_error(f"分公司产值不能为负数: {person.company_total_revenue}")
    
    def _validate_collection_rate(self, person: PersonData, result: ValidationResult):
        """校验回款率"""
        if person.collection_rate < 0:
            result.add_error(f"回款率不能为负数: {person.collection_rate}")
        elif person.collection_rate > 1:
            result.add_error(f"回款率不能超过100%: {person.collection_rate * 100}%")
        
        # 回款率预警
        if person.collection_rate < self.config.threshold_90:
            result.add_warning(
                f"回款率({person.collection_rate*100:.1f}%)低于90%奖门槛"
                f"({self.config.threshold_90*100:.1f}%)，可能无法获得完成奖"
            )
    
    def _validate_completion_rate(self, person: PersonData, result: ValidationResult):
        """校验完成率"""
        from config import CompletionRateMode
        
        if self.config.completion_rate_mode == CompletionRateMode.FROM_TARGET:
            # 自动计算模式需要年度目标
            if person.role != Role.CP:  # 常委不需要目标
                if person.annual_target is None or person.annual_target <= 0:
                    result.add_error("完成率自动计算模式下，年度目标必须大于0")
        else:
            # 手填模式需要完成率
            if person.completion_rate_manual is None:
                result.add_warning("完成率手填模式下，建议填写完成率")
            elif person.completion_rate_manual < 0:
                result.add_error(f"完成率不能为负数: {person.completion_rate_manual}")
            elif person.completion_rate_manual > 2:
                result.add_warning(f"完成率超过200%({person.completion_rate_manual*100:.1f}%)，请确认是否正确")
    
    def _validate_allocation_ratio(self, person: PersonData, result: ValidationResult):
        """校验分配比例"""
        if person.personal_allocation_ratio is not None:
            if person.personal_allocation_ratio < 0:
                result.add_error(f"分配比例不能为负数: {person.personal_allocation_ratio}")
            elif person.personal_allocation_ratio > 1:
                result.add_error(f"分配比例不能超过100%: {person.personal_allocation_ratio * 100}%")
    
    def _validate_ceo_bonus(self, person: PersonData, result: ValidationResult):
        """校验CEO奖金"""
        if person.ceo_bonus is not None and person.ceo_bonus < 0:
            result.add_error(f"CEO奖金不能为负数: {person.ceo_bonus}")
    
    def _validate_role_specific(self, person: PersonData, result: ValidationResult):
        """岗位特定校验"""
        if person.role == Role.CP:
            # 常委不需要产值激励相关数据
            pass
        elif person.role == Role.DM:
            # 总经理需要区域完成情况
            if not any([person.region_completed_90, person.region_completed_100]):
                result.add_warning("总经理岗位建议填写区域完成情况")
    
    def _validate_group_allocation(
        self, 
        persons: List[PersonData], 
        results: Dict[str, ValidationResult]
    ):
        """校验同组织内分配比例合计"""
        # 按组织单元分组
        org_allocations: Dict[str, float] = {}
        org_members: Dict[str, List[str]] = {}
        
        for person in persons:
            if person.personal_allocation_ratio is not None:
                org = person.org_unit
                if org not in org_allocations:
                    org_allocations[org] = 0.0
                    org_members[org] = []
                org_allocations[org] += person.personal_allocation_ratio
                org_members[org].append(person.name)
        
        # 检查合计是否超过1
        for org, total in org_allocations.items():
            if total > 1.0:
                warning = f"组织单元'{org}'内分配比例合计为{total*100:.1f}%，超过100%"
                # 给该组织内所有成员添加警告
                for name in org_members[org]:
                    if name in results:
                        results[name].add_warning(warning)


def validate_input_data(persons: List[PersonData], config: GlobalConfig = None) -> Dict[str, ValidationResult]:
    """
    便捷函数：校验输入数据
    
    Args:
        persons: 人员数据列表
        config: 全局配置
    
    Returns:
        校验结果字典 {姓名: ValidationResult}
    """
    validator = BonusValidator(config)
    return validator.validate_batch(persons)
