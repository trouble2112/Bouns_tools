"""
2026上半年奖金计算引擎 - 配置模块
Configuration module for bonus calculation
"""
from dataclasses import dataclass, field
from typing import Dict, List, Literal
from enum import Enum


class CompletionBonusMode(Enum):
    """完成奖叠加模式"""
    EXCLUSIVE = "exclusive"  # 达到100%仅发100%，不重复发90%
    STACK = "stack"          # 90%和100%可叠加


class CompletionRateMode(Enum):
    """完成率计算模式"""
    FROM_TARGET = "from_target"  # 合计产值/全年目标
    MANUAL = "manual"            # 手填完成率


class Role(Enum):
    """岗位类型"""
    CP = "CP"                    # 常委
    DM = "DM"                    # 总经理
    VP = "VP"                    # 副总经理
    MGR = "MGR"                  # 部门经理
    SALES_USER = "SALES_USER"   # 销售-用户部
    SALES_NEW = "SALES_NEW"     # 销售-新购
    SALES_EDU = "SALES_EDU"     # 销售-高校


@dataclass
class GlobalConfig:
    """全局参数配置"""
    
    # 时间系数 (1-6月)
    time_coefficients: Dict[int, float] = field(default_factory=lambda: {
        1: 1.15,
        2: 1.15,
        3: 1.10,
        4: 1.00,
        5: 0.90,
        6: 0.85
    })
    
    # 回款门槛
    threshold_90: float = 0.85   # 90%奖的回款率门槛
    threshold_100: float = 0.90  # 100%奖的回款率门槛
    
    # 完成奖叠加模式 (按岗位设置默认值)
    dm_completion_bonus_mode: CompletionBonusMode = CompletionBonusMode.EXCLUSIVE
    other_completion_bonus_mode: CompletionBonusMode = CompletionBonusMode.STACK
    
    # 完成率计算模式
    completion_rate_mode: CompletionRateMode = CompletionRateMode.FROM_TARGET
    
    # 是否拆分50%即时/50%回款后
    include_payout_timing: bool = False
    
    # 固定参数
    cp_subsidy: float = 60000.0           # 常委固定补贴(半年)
    sales_monthly_subsidy: float = 800.0   # 新购/高校销售月补贴
    
    # 区域/全国奖金额
    region_90_bonus: float = 30000.0      # 大区90%奖
    region_100_bonus: float = 30000.0     # 大区100%奖
    national_90_bonus: float = 40000.0    # 全国90%奖
    national_100_bonus: float = 40000.0   # 全国100%奖
    
    # DM区域完成奖
    dm_region_bonus: float = 40000.0
    
    # DM完成奖上限
    dm_completion_bonus_cap: float = 40000.0


@dataclass
class RoleConfig:
    """岗位配置"""
    
    # 过程激励比例
    incentive_rates: Dict[Role, float] = field(default_factory=lambda: {
        Role.CP: 0.0,
        Role.DM: 0.004,
        Role.VP: 0.004,
        Role.MGR: 0.01,
        Role.SALES_USER: 0.02,
        Role.SALES_NEW: 0.03,
        Role.SALES_EDU: 0.03
    })
    
    # 完成奖比例 (分公司产值乘数)
    completion_bonus_rate: float = 0.015  # 1.5%
    
    # DM完成奖比例 (分公司产值乘数)
    dm_completion_bonus_rate: float = 0.004  # 0.4%
    
    # 是否有固定补贴的岗位
    has_fixed_subsidy: Dict[Role, bool] = field(default_factory=lambda: {
        Role.CP: True,
        Role.DM: False,
        Role.VP: False,
        Role.MGR: False,
        Role.SALES_USER: False,
        Role.SALES_NEW: True,
        Role.SALES_EDU: True
    })
    
    # 是否有区域奖的岗位
    has_region_bonus: Dict[Role, bool] = field(default_factory=lambda: {
        Role.CP: True,
        Role.DM: True,
        Role.VP: False,
        Role.MGR: False,
        Role.SALES_USER: False,
        Role.SALES_NEW: False,
        Role.SALES_EDU: False
    })
    
    # 是否有全国奖的岗位
    has_national_bonus: Dict[Role, bool] = field(default_factory=lambda: {
        Role.CP: True,
        Role.DM: False,
        Role.VP: False,
        Role.MGR: False,
        Role.SALES_USER: False,
        Role.SALES_NEW: False,
        Role.SALES_EDU: False
    })


# 默认配置实例
DEFAULT_GLOBAL_CONFIG = GlobalConfig()
DEFAULT_ROLE_CONFIG = RoleConfig()
