from dataclasses import dataclass

@dataclass(frozen=True)
class BaseGlobalContext:
    """
    Base Class cho Global Context (Immutable).
    """
    pass

@dataclass
class BaseDomainContext:
    """
    Base Class cho Domain Context (Mutable).
    """
    pass

@dataclass
class BaseSystemContext:
    """
    Base Class cho System Context (Wrapper).
    """
    global_ctx: BaseGlobalContext
    domain_ctx: BaseDomainContext
