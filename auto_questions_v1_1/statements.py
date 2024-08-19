# encoding: utf8
# version: 1.1
# author: Qin Yuhang
# date: 2024-08-16

import json5
import random
import abc
from pathlib import Path
from typing import Any, Callable
from fractions import Fraction
import enum

# statement()函数返回字典的键
_STATEMENT = "statement"
_PROCESS = "process"
_QUESTION = "question"
_QUESTION_TYPE = "question_type"

@enum.unique
class TimeScale(enum.Enum):
    """时间尺度枚举类"""
    Order = 0
    Year = 1

# 模板文件路径
TEMPLATE_FILES = {
    TimeScale.Order: Path("templates/order.json5"),
    TimeScale.Year: Path("templates/year.json5"),
}

# 模板字典
TEMPLATES: dict[str, Any] = {}

# 详细信息输出强度
VERBOSE = 0

def get_templates(time_scale: TimeScale) -> dict[str, Any]:
    """获取指定时间尺度的模板字典

    Args:
        time_scale (TimeScale): 时间尺度枚举类

    Returns:
        dict[str, Any]: 模板字典
    """
    global TEMPLATES
    curr_file = Path(__file__).parent / TEMPLATE_FILES[time_scale]
    with curr_file.open("r", encoding="utf-8") as f:
        TEMPLATES = json5.load(f)
        return TEMPLATES

class Statement(metaclass=abc.ABCMeta):
    """陈述类的抽象基类"""
    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def statement(self, question_mode: bool = False) -> dict[str, str]:
        """输出statement的自然文本陈述或对应的问题及回答

        Args:
            question_mode (bool, optional): 是否是问题模式. 默认为False.

        Returns:
            dict[str, str]: statement的自然文本陈述或对应的问题及类型
        """
        pass

    @staticmethod
    def _replacement(template: str, replacements: dict[str, str]) -> str:
        """替换模板中的占位符

        Args:
            template (str): 模板字符串
            replacements (dict[str, str]): 替换字典，键是占位符（不含方括号），值是替换后的字符串

        Returns:
            str: 替换后的字符串
        """
        for key, value in replacements.items():
            template = template.replace(f"[{key}]", value)
        return template

    @staticmethod
    def _check_template(template: str, *args: str) -> bool:
        """检查模板是否含有特定的占位符

        Args:
            template (str): 模板字符串
            *args (str): 占位符列表

        Returns:
            bool: 模板是否含有特定的占位符
        """
        return all([f"[{arg}]" in template for arg in args])
    
    def __str__(self) -> str:
        return ""

    @abc.abstractmethod
    def __eq__(self, value: object) -> bool:
        """判断两个陈述是否等价的函数，需要在子类中实现
        
        Args:
            value (object): 另一个陈述
            
        Returns:
            bool: 两个陈述是否等价"""
        return False

class Event(Statement):
    """事件类，作为一种特殊的陈述类"""
    def __init__(self, verb: str, object: str, time: int):
        super().__init__()
        self.verb = verb
        self.object = object
        self.time = time

    @property
    def event(self) -> str:
        """结合谓语和宾语，返回对事件的自然文本描述

        Returns:
            str: 对事件的自然文本描述
        """
        return f"{self.verb}{self.object}"
    
    @abc.abstractmethod
    def statement(self, question_mode: bool = False) -> dict[str, str]:
        pass
   
    def __str__(self) -> str:
        return self.event

    def __eq__(self, value: object) -> bool:
        """判断两个事件是否等价

        Args:
            value (object): 另一个事件

        Returns:
            bool: 两个事件是否等价
        """
        if isinstance(value, Event):
            return self.verb == value.verb and self.object == value.object and self.time == value.time
        return False

class Relation(Statement):
    """关系类，作为一种特殊的陈述类"""
    def __init__(self, prev_statement: Statement, next_statement: Statement):
        super().__init__()
        self.prev_statement = prev_statement
        self.next_statement = next_statement

    @abc.abstractmethod
    def statement(self, question_mode: bool = False) -> dict[str, str]:
        pass

    def __eq__(self, value: object) -> bool:
        """判断两个关系是否等价

        Args:
            value (object): 另一个关系

        Returns:
            bool: 两个关系是否等价
        """
        if isinstance(value, Relation):
            return self.prev_statement == value.prev_statement and self.next_statement == value.next_statement
        return False

PROCESS_LIST: list[str] = [] # 过程描述列表

def verbose(func: Callable[[Statement, bool], dict[str, str]]) -> Callable[[Statement, bool], dict[str, str]]:
    """详细信息输出装饰器

    Args:
        func (Callable[[Statement, bool], dict[str, str]): 陈述类的statement方法

    Returns:
        Callable[[Statement, bool], dict[str, str]: 陈述类的statement方法
    """
    global PROCESS_LIST
    def wrapper(self: Statement, question_mode: bool = False) -> dict[str, str]:
        result = func(self, question_mode)
        if VERBOSE >= 1: # 输出到控制台
            if not question_mode: # 生成陈述
                if isinstance(self, Event):
                    print(f"生成事件描述：{self.event}")
                elif isinstance(self, Relation):
                    print(f"生成事件关系描述：{self.prev_statement} -> {self.next_statement}")
            else: # 生成问题和回答
                if isinstance(self, Event):
                    print(f"生成问题：{self.event}，问题类型：{result[_QUESTION_TYPE]}")
        # 放弃使用这个装饰器进行输出到最终结果
        """
        elif VERBOSE >= 2: # 输出到最终结果
            if not question_mode:
                if isinstance(self, Event):
                    PROCESS_LIST.append(f"生成事件描述：{self.event}")
                    # result |= {_PROCESS: f"生成事件描述：{self.event}"}
                elif isinstance(self, Relation):
                    PROCESS_LIST.append(f"生成事件关系描述：{self.prev_statement} -> {self.next_statement}")
                    # result |= {_PROCESS: f"生成事件关系描述：{self.prev_statement} -> {self.next_statement}"}
            else:
                pass
        """
        return result
    return wrapper

class TemporalEvent(Event):
    """瞬时事件类，表示一个瞬时事件"""
    def __init__(self, verb: str, object: str, time: int):
        """瞬时事件类，表示一个瞬时事件

        Args:
            verb (str): 事件的动词
            object (str): 事件的宾语
            time (int): 事件发生的时间
        """
        super().__init__(verb, object, time)

    @verbose
    def statement(self, question_mode: bool = False) -> dict[str, str]:
        if question_mode: # 生成一个问题和回答
            arg_list: list[str] = ["event", "time"] # 占位符列表
            temp_list: list[str] = [i for i in TEMPLATES["temporal_event"] if self._check_template(i, *arg_list)] # 合适的模板列表
            assert temp_list, "模板中没有合适的占位符，请检查模板"
            temp: str = random.choice(temp_list) # 随机选择一个模板
            rp_dict: dict[str, str] = {"verb": self.verb, "object": self.object, "event": str(self.event), "time": str(self.time)} # 替换字典
            q_arg: str = random.choice(arg_list) # 选择一个问题的占位符
            rp_dict |= {q_arg: "____"} # 将问题的占位符替换为"____"
            question = self._replacement(temp, rp_dict) # 生成问题
            return {_QUESTION: question, _QUESTION_TYPE: q_arg}
        else: # 生成一个陈述
            temp: str = random.choice(TEMPLATES["temporal_event"])
            state = self._replacement(temp, {"verb": self.verb, "object": self.object, "event": str(self.event), "time": str(self.time)})
            return {_STATEMENT: state}

class LastingEvent(Event):
    """持续事件类，表示一个持续事件"""
    def __init__(self, verb: str, object: str, time: int, endtime: int):
        """持续事件类，表示一个持续事件

        Args:
            verb (str): 事件的动词
            object (str): 事件的宾语
            time (int): 事件开始的时间
            endtime (int): 事件结束的时间
        """
        super().__init__(verb, object, time)
        self.endtime = endtime
        self.start_event = TemporalEvent("开始", self.event, time)
        self.end_event = TemporalEvent("结束", self.event, endtime)

    @property
    def duration(self) -> int:
        """返回事件的持续时间

        Returns:
            int: 事件的持续时间

        Raises:
            AssertionError: 结束时间必须大于等于开始时间
        """
        assert self.endtime >= self.time, "结束时间必须大于等于开始时间"
        return self.endtime - self.time

    def duration_statement(self) -> str:
        """返回事件的持续时间的自然文本描述

        Returns:
            str: 事件的持续时间的自然文本描述
        """
        temp: str = random.choice(TEMPLATES["duration"])
        temp = self._replacement(temp, {"verb": self.verb, "object": self.object, "event": str(self.event), "duration": str(self.duration)})
        return temp
    
    @verbose
    def statement(self, question_mode: bool = False) -> dict[str, str]:
        style_decide = random.choice(["whole", "separate"])
        if question_mode: # 生成一个问题和回答
            # TODO: 生成一个问题和回答
            if style_decide == "whole":
                pass
            elif style_decide == "separate":
                pass
        else: # 生成一个陈述
            if style_decide == "whole":
                temp: str = random.choice(TEMPLATES["lasting_event"])
                state = self._replacement(temp, {"verb": self.verb, "object": self.object, "event": str(self.event), "start": str(self.time), "end": str(self.endtime), "duration": str(self.duration)})
                return {_STATEMENT: state}
            elif style_decide == "separate":
                output_attrs = random.choices(["start_event", "end_event", "duration"], k=2)
                outputs: list[str] = []
                for attr in output_attrs:
                    if attr == "start_event":
                        outputs.append(self.start_event.statement()[_STATEMENT])
                    elif attr == "end_event":
                        outputs.append(self.end_event.statement()[_STATEMENT])
                    elif attr == "duration":
                        outputs.append(self.duration_statement())
                link: str = random.choice(TEMPLATES["link"])
                return {_STATEMENT: link.join(outputs)}

    def set_start_event(self, verb: str, object: str):
        """设置事件的开始事件，这个时间将作为内部的一个瞬时事件

        Args:
            verb (str): 事件的动词
            object (str): 事件的宾语
        """
        self.start_event = TemporalEvent(verb, object, self.time)

    def set_end_event(self, verb: str, object: str):
        """设置事件的结束事件，这个时间将作为内部的一个瞬时事件

        Args:
            verb (str): 事件的动词
            object (str): 事件的宾语
        """
        self.end_event = TemporalEvent(verb, object, self.endtime)

class TempRelation(Relation):
    """点对点关系类，表示两个瞬时事件之间的关系"""
    def __init__(self, prev_statement: TemporalEvent, next_statement: TemporalEvent):
        """点对点关系类，表示两个瞬时事件之间的关系

        Args:
            prev_statement (TemporalEvent): 前一个事件
            next_statement (TemporalEvent): 后一个事件
        """
        super().__init__(prev_statement, next_statement)

    @property
    def diff(self) -> int:
        """两个事件之间的时间差"""
        return abs(self.next_statement.time - self.prev_statement.time)
    
    @verbose
    def statement(self, question_mode: bool = False) -> dict[str, str]:
        if question_mode:
            # TODO: 生成一个问题和回答
            pass
        else:
            temp: str # 选择的模板
            TEMPORAL_RELATION: str = "temporal_relation"
            if self.next_statement.time > self.prev_statement.time:
                temp = random.choice(TEMPLATES[TEMPORAL_RELATION]["after"])
            elif self.next_statement.time < self.prev_statement.time:
                temp = random.choice(TEMPLATES[TEMPORAL_RELATION]["before"])
            else:
                temp = random.choice(TEMPLATES[TEMPORAL_RELATION]["simultaneous"])
            replace_dict: dict[str, str] = {
                "verb1": self.next_statement.verb,
                "object1": self.next_statement.object,
                "event1": str(self.next_statement.event),
                "verb2": self.prev_statement.verb,
                "object2": self.prev_statement.object,
                "event2": str(self.prev_statement.event),
                "diff": str(self.diff)
            } # 替换字典
            state = self._replacement(temp, replace_dict)
            return {_STATEMENT: state}

class TempLastingRelation(Relation):
    """点对段关系类，表示一个瞬时事件和一个持续事件之间的关系"""
    def __init__(self, prev_statement: TemporalEvent, next_statement: LastingEvent):
        """点对段关系类，表示一个瞬时事件和一个持续事件之间的关系

        Args:
            prev_statement (TemporalEvent): 瞬时事件
            next_statement (LastingEvent): 持续事件
        """
        super().__init__(prev_statement, next_statement)

    @verbose
    def statement(self, question_mode: bool = False) -> dict[str, str]:
        if question_mode:
            pass
        else:
            output_attrs = random.choices(["start_event", "end_event", "duration"], k=2)
            outputs: list[str] = []
            for attr in output_attrs:
                if attr == "start_event":
                    outputs.append(TempRelation(self.prev_statement, self.next_statement.start_event).statement()[_STATEMENT])
                elif attr == "end_event":
                    outputs.append(TempRelation(self.prev_statement, self.next_statement.end_event).statement()[_STATEMENT])
                elif attr == "duration":
                    outputs.append(self.next_statement.duration_statement())
            link: str = random.choice(TEMPLATES["link"])
            return {_STATEMENT: link.join(outputs)}

class LastingTempRelation(Relation):
    """段对点关系类，表示一个持续事件到一个瞬时事件之间的关系"""
    def __init__(self, prev_statement: LastingEvent, next_statement: TemporalEvent):
        """段对点关系类，表示一个持续事件和一个瞬时事件之间的关系

        Args:
            prev_statement (LastingEvent): 持续事件
            next_statement (TemporalEvent): 瞬时事件
        """
        super().__init__(prev_statement, next_statement)

    @verbose
    def statement(self, question_mode: bool = False) -> dict[str, str]:
        prev_temporal: TemporalEvent = random.choice([self.prev_statement.start_event, self.prev_statement.end_event])
        return TempRelation(prev_temporal, self.next_statement).statement(question_mode)

class LastingRelation(Relation):
    """段对段关系类，表示两个持续事件之间的关系"""
    def __init__(self, prev_statement: LastingEvent, next_statement: LastingEvent):
        """段对段关系类，表示两个持续事件之间的关系

        Args:
            prev_statement (LastingEvent): 前一个持续事件
            next_statement (LastingEvent): 后一个持续事件
        """
        super().__init__(prev_statement, next_statement)

    @property
    def duration_diff(self) -> int:
        """两个持续事件之间的持续时间差"""
        return abs(self.next_statement.duration - self.prev_statement.duration)
    
    def duration_relation(self) -> str:
        """返回两个持续事件的持续时间关系的自然文本描述

        Raises:
            ValueError: 内部参数出现错误时抛出异常

        Returns:
            str: 两个持续事件的持续时间关系的自然文本描述
        """
        DURATION_RELATION: str = "duration_relation"
        init_dict: dict[str, str] = {
            "verb1": self.next_statement.verb,
            "object1": self.next_statement.object,
            "event1": str(self.next_statement.event),
            "verb2": self.prev_statement.verb,
            "object2": self.prev_statement.object,
            "event2": str(self.prev_statement.event),
        } # 替换字典
        # 选择模板，根据条件添加替换字典键值对
        if self.next_statement.duration == self.prev_statement.duration: # 持续时间相同
            typ = "equal"
            curr_dict = init_dict | {"duration": str(self.prev_statement.duration)}
        else:
            mode = random.choice(["diff", "ratio"])
            if mode == "diff": # 表述两个事件的持续时间差
                typ = "longer" if self.next_statement.duration > self.prev_statement.duration else "shorter"
                curr_dict = init_dict | {"diff": str(self.duration_diff)}
            elif mode == "ratio": # 表述两个事件的持续时间比
                fraction = Fraction(self.next_statement.duration, self.prev_statement.duration)
                typ = "times" if fraction.is_integer() else "ratio"
                if typ == "times": # 如果是整数倍数，只显示倍数
                    curr_dict = init_dict | {"times": str(fraction.numerator)}
                else: # 如果不是整数倍数，显示比值
                    curr_dict = init_dict | {"ratio": str(fraction)}
            else:
                raise ValueError(f"mode参数{mode}错误")
        temp: str = random.choice(TEMPLATES[DURATION_RELATION][typ])
        return self._replacement(temp, curr_dict)
    
    @verbose
    def statement(self, question_mode: bool = False) -> dict[str, str]:
        if question_mode:
            pass
        else:
            output_attrs = random.choices(["start_event", "end_event", "duration"], k=2)
            outputs: list[str] = []
            for attr in output_attrs:
                prev_temporal: TemporalEvent = random.choice([self.prev_statement.start_event, self.prev_statement.end_event])
                if attr == "start_event":
                    outputs.append(TempRelation(prev_temporal, self.next_statement.start_event).statement()[_STATEMENT])
                elif attr == "end_event":
                    outputs.append(TempRelation(prev_temporal, self.next_statement.end_event).statement()[_STATEMENT])
                elif attr == "duration":
                    outputs.append(self.duration_relation())
            link: str = random.choice(TEMPLATES["link"])
            return {_STATEMENT: link.join(outputs)}