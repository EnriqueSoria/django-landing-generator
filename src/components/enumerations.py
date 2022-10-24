from enum import auto

from .utils import StrEnum


class ComponentType(StrEnum):
    TEXT = auto()
    INT = auto()
    BOOL = auto()
    URL = auto()
    PNG = auto()
    JPG = auto()
    COMPONENT = auto()
    COMPONENTS = auto()
    OBJECT = auto()
