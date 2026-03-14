from enum import StrEnum, auto


class EventType(StrEnum):
    PAGE_VIEW = auto()
    PRODUCT_VIEW = auto()
    ADD_TO_CART = auto()
    REMOVE_FROM_CART = auto()
    PURCHASE = auto()


class AnalyticsMetrics(StrEnum):
    BY_CART = auto()
    BY_REVENUE = auto()
