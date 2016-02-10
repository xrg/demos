# File: enums.py

class IntEnumC:
    def __init__(self,*args):
        raise RuntimeError("Enum objects shall not be instantiated")

    @classmethod
    def _check(cls, value):
        if getattr(cls, '_min', None) is None:
            vals = []
            for k, v in cls.__dict__.items():
                if k.startswith('_') or not isinstance(v, int):
                    continue
                vals.append(v)
            cls._min = min(vals)
            cls._max = max(vals)

        if not isinstance(value, int):
            raise ValueError("enum values must be integers")
        if value < cls._min or value > cls._max:
            raise ValueError("%s=%d out of range (%d,%d)" % (cls.__name__, value, cls._min, cls._max))
        return True

    @classmethod
    def get_valueitems(cls, prefix=None):
        if prefix is True:
            prefix = cls.__name__

        if prefix:
            prefix += '.'
        else:
            prefix = ''
        ret = {}
        for k, v in cls.__dict__.items():
            if k.startswith('_') or not isinstance(v, int):
                continue
            ret[prefix + k] = v

        return ret

    @classmethod
    def deconstruct(cls):
        return 'demos.common.utils.enums.' + cls.__name__, ['*' '-* remove args!'], {}

# Enum definitions -------------------------------------------------------------

class State(IntEnumC):

    DRAFT = 1
    PENDING = 2
    WORKING = 3
    RUNNING = 4
    COMPLETED = 5
    PAUSED = 6
    ERROR = 7
    TEMPLATE = 8

class Type(IntEnumC):

    ELECTIONS = 1
    REFERENDUM = 2

class VcType(IntEnumC):
    
    SHORT = 1
    LONG = 2

#eof
