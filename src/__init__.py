"""
2026上半年奖金计算引擎 - 包初始化
Package initialization
"""
from config import (
    GlobalConfig,
    RoleConfig,
    Role,
    CompletionBonusMode,
    CompletionRateMode,
    DEFAULT_GLOBAL_CONFIG,
    DEFAULT_ROLE_CONFIG
)

from models import (
    PersonData,
    BonusDetail,
    ValidationResult
)

from validators import (
    BonusValidator,
    validate_input_data
)

from bonus_engine import (
    BonusCalculator,
    calculate_bonus,
    calculate_bonus_batch
)

__version__ = "1.0.0"
__all__ = [
    # Config
    "GlobalConfig",
    "RoleConfig", 
    "Role",
    "CompletionBonusMode",
    "CompletionRateMode",
    "DEFAULT_GLOBAL_CONFIG",
    "DEFAULT_ROLE_CONFIG",
    
    # Models
    "PersonData",
    "BonusDetail",
    "ValidationResult",
    
    # Validators
    "BonusValidator",
    "validate_input_data",
    
    # Calculator
    "BonusCalculator",
    "calculate_bonus",
    "calculate_bonus_batch",
]
