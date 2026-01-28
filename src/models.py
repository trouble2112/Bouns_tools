"""
2026上半年奖金计算引擎 - 数据模型
Data models for bonus calculation
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from config import Role


@dataclass
class PersonData:
    """人员输入数据"""
    
    # 基本信息
    name: str                           # 姓名
    role: Role                          # 岗位
    region: str                         # 区域
    org_unit: str                       # 组织单元(分公司/部门)
    
    # 产值数据 (1-6月)
    month_revenue: Dict[int, float] = field(default_factory=dict)
    
    # 分公司总产值 (若与个人不同)
    company_total_revenue: Optional[float] = None
    
    # 目标与完成率
    annual_target: Optional[float] = None       # 全年目标
    completion_rate_manual: Optional[float] = None  # 手填完成率
    
    # 回款率
    collection_rate: float = 0.0
    
    # 区域/全国完成情况
    region_completed_90: bool = False
    region_completed_100: bool = False
    national_completed_90: bool = False
    national_completed_100: bool = False
    
    # 个人分配比例 (0~1)
    personal_allocation_ratio: Optional[float] = None
    
    # CEO奖金 (手动输入)
    ceo_bonus: Optional[float] = None
    
    def get_total_revenue(self) -> float:
        """计算个人产值合计"""
        return sum(self.month_revenue.values())
    
    def get_company_revenue(self) -> float:
        """获取分公司产值(若未设置则使用个人产值)"""
        if self.company_total_revenue is not None:
            return self.company_total_revenue
        return self.get_total_revenue()


@dataclass
class BonusDetail:
    """奖金明细结果"""
    
    # 基本信息
    name: str
    role: Role
    region: str
    org_unit: str
    
    # 过程激励 (分月)
    monthly_incentives: Dict[int, float] = field(default_factory=dict)
    incentive_total: float = 0.0
    
    # 过程激励发放拆分 (可选)
    incentive_immediate: Optional[float] = None   # 即时发放50%
    incentive_after_collection: Optional[float] = None  # 回款后发放50%
    
    # 完成奖
    completion_bonus_90: float = 0.0     # 90%档完成奖
    completion_bonus_100: float = 0.0    # 100%档完成奖
    completion_bonus_total: float = 0.0  # 完成奖小计
    
    # 区域奖
    region_bonus_90: float = 0.0
    region_bonus_100: float = 0.0
    region_bonus_total: float = 0.0
    
    # 全国奖
    national_bonus_90: float = 0.0
    national_bonus_100: float = 0.0
    national_bonus_total: float = 0.0
    
    # 固定补贴
    fixed_subsidy: float = 0.0
    
    # CEO奖金
    ceo_bonus: float = 0.0
    
    # 总计
    grand_total: float = 0.0
    
    # 元数据
    completion_bonus_mode: str = ""      # 使用的叠加模式
    completion_rate: float = 0.0         # 实际完成率
    collection_rate: float = 0.0         # 回款率
    personal_allocation_ratio: Optional[float] = None  # 个人分配比例
    
    # 标记
    warnings: List[str] = field(default_factory=list)  # 警告信息
    pending_confirmations: List[str] = field(default_factory=list)  # 待确认项
    
    def calculate_total(self):
        """计算奖金总计"""
        self.grand_total = (
            self.incentive_total +
            self.completion_bonus_total +
            self.region_bonus_total +
            self.national_bonus_total +
            self.fixed_subsidy +
            self.ceo_bonus
        )


@dataclass
class ValidationResult:
    """校验结果"""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        self.warnings.append(message)
