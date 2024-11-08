# encoding: utf8
# Author: Qin Yuhang
# Date: 2024/08/14
# 用于记录时间轴上的事件

import json5
from pathlib import Path
from typing import Self, Optional, Any
from fractions import Fraction
from enum import Enum
import random
import re

class TimeScale(Enum):
    """时间的尺度

    Args:
        Enum (int): 时间的各种尺度
    """
    Order = 0
    Year = 1

SCALE_FILES = {
    TimeScale.Order: "order.json5",
    TimeScale.Year: "year.json5", 
} # 时间尺度对应的文件名

TEMPLATES: dict[str, Any] = {} # 出题模板

class Event:
    """事件类，用于描述时间轴上的事件"""
    def __init__(self, text: str) -> Self:
        """初始化事件

        Args:
            text (str): 事件的文字描述
        """
        self.text = text

    def __str__(self) -> str:
        """事件的字符串描述

        Returns:
            str: 事件的文字描述
        """
        return self.text

    def statement(self, question_mode: bool = False) -> str:
        """生成事件的描述或问题

        Args:
            question_mode (bool, optional): 是否是问题模式，默认为False

        Raises:
            NotImplementedError: statement方法未实现

        Returns:
            str: 事件的描述或问题
        """
        raise NotImplementedError("statement方法未实现")

class PointEvent(Event):
    """点事件，即发生在某一时刻的事件，是事件的一种特例"""
    def __init__(self, text: str, time: int) -> Self:
        """初始化一个点事件并返回

        Args:
            text (str): 事件的文字描述
            time (int): 事件发生的时间

        Returns:
            Self: 事件对象
        """
        super().__init__(text)
        self.time = time

    def statement(self, question_mode: bool = False) -> str:
        use_statement: str = random.choice(TEMPLATES["point"])
        use_statement = use_statement.replace("[event]", self.text)
        time: str = random.choice(TEMPLATES["question_words"]) if question_mode else str(self.time)
        use_statement = use_statement.replace("[time]", time)
        return use_statement

class DurationEvent(Event):
    """持续事件，即发生在某一时间段内的事件，是事件的一种特例"""
    def __init__(self, text: str, start_time: int, end_time: int) -> Self:
        """初始化一个持续事件并返回

        Args:
            text (str): 事件的文字描述
            start_time (int): 事件开始时间
            end_time (int): 事件结束时间

        Returns:
            Self: 事件对象
        """
        super().__init__(text)
        assert start_time < end_time, f"事件{text}开始时间必须小于结束时间"
        self.start_time = start_time
        self.end_time = end_time
        self.start_event: PointEvent = PointEvent(f"开始{text}", start_time)
        self.end_event: PointEvent = PointEvent(f"{text}结束", end_time)
    
    @property
    def duration(self) -> int:
        """获取事件持续时间

        Returns:
            int: 事件持续时间
        """
        return self.end_time - self.start_time
    
    def set_start_event(self, text: str) -> None:
        """设置事件的开始事件（相当于一个点事件）

        Args:
            text (str): 开始事件的文字描述
        """
        self.start_event = PointEvent(text, self.start_time)

    def set_end_event(self, text: str) -> None:
        """设置事件的结束事件（相当于一个点事件）

        Args:
            text (str): 结束事件的文字描述
        """
        self.end_event = PointEvent(text, self.end_time)

    def statement(self, question_mode: bool = False) -> str:
        if question_mode:
            output_attr = random.choice(["start_time", "end_time", "duration"])
            if output_attr == "start_time":
                return self.start_event.statement(question_mode)
            elif output_attr == "end_time":
                return self.end_event.statement(question_mode)
            elif output_attr == "duration":
                use_statement: str = random.choice(TEMPLATES["length"])
                use_statment = use_statement.replace("[event]", self.text)
                word: str = random.choice(TEMPLATES["question_words"])
                return use_statement.replace("[duration]", word)
        else:
            use_statement: str = random.choice(TEMPLATES["duration"])
            use_statement = use_statement.replace("[event]", self.text).replace("[start_time]", str(self.start_time)).replace("[end_time]", str(self.end_time)).replace("[duration]", str(self.duration))
            return use_statement
    
class PointEventRelation(Event):
    """点事件关系，即两个点事件之间的关系"""
    def __init__(self, event1: PointEvent, event2: PointEvent) -> Self:
        """初始化点事件关系并返回

        Args:
            event1 (PointEvent): 点事件1
            event2 (PointEvent): 点事件2

        Returns:
            Self: 点事件关系对象
        """
        super().__init__("")
        self.event1 = event1
        self.event2 = event2

    def statement(self, question_mode: bool = False) -> str:
        """生成事件关系的描述或问题

        Args:
            question_mode (bool, optional): 是否是问题模式，默认为False

        Returns:
            str: 事件关系的描述或问题
        """
        if question_mode:
            if self.event1.time == self.event2.time:
                return None
            elif self.event1.time < self.event2.time:
                use_statement = random.choice(TEMPLATES["point2point"]["before"])
            else:
                use_statement = random.choice(TEMPLATES["point2point"]["after"])
            use_statement = use_statement.replace("[event1]", self.event1.text).replace("[event2]", self.event2.text)
            word: str = random.choice(TEMPLATES["question_words"])
            return use_statement.replace("[diff]", word)
        else:
            if self.event1.time == self.event2.time:
                use_statement: str = random.choice(TEMPLATES["point2point"]["same"])
            elif self.event1.time < self.event2.time:
                use_statement: str = random.choice(TEMPLATES["point2point"]["before"])
            else:
                use_statement: str = random.choice(TEMPLATES["point2point"]["after"])
            use_statement = use_statement.replace("[event1]", self.event1.text).replace("[event2]", self.event2.text).replace("[diff]", str(abs(self.event1.time - self.event2.time)))
            return use_statement

class PointDurationRelation(Event):
    def __init__(self, event1: PointEvent, event2: DurationEvent) -> Self:
        super().__init__("")
        self.event1 = event1
        self.event2 = event2

    def statement(self, question_mode: bool = False) -> str:
        if question_mode:
            set_event = random.choice([self.event2.start_event, self.event2.end_event])
            return PointEventRelation(self.event1, set_event).statement(question_mode)
        else:
            output_attrs = random.choices(["start_time", "end_time", "duration"], k=2)
            outputs = []
            for attr in output_attrs:
                if attr == "start_time":
                    outputs.append(PointEventRelation(self.event1, self.event2.start_event).statement())
                elif attr == "end_time":
                    outputs.append(PointEventRelation(self.event1, self.event2.end_event).statement())
                elif attr == "duration":
                    pass

class DurationPointRelation(Event):
    def __init__(self, event1: DurationEvent, event2: PointEvent) -> Self:
        super().__init__("")
        self.event1 = event1
        self.event2 = event2

    def statement(self, question_mode: bool = False) -> str:
        set_event = random.choice([self.event1.start_event, self.event1.end_event])
        return PointEventRelation(set_event, self.event2).statement(question_mode)

class DurationEventRelation(Event):
    def __init__(self, event1: DurationEvent, event2: DurationEvent) -> Self:
        super().__init__("")
        self.event1 = event1
        self.event2 = event2

    def statement(self, question_mode: bool = False) -> str:
        pass

class TimeLine:
    """时间轴类，用于记录时间轴上的事件"""
    def __init__(self, name: str, scale: TimeScale = TimeScale.Order) -> Self:
        """初始化时间轴并返回

        Args:
            name (str): 人名，说明这个时间轴描述了谁的生活史
            scale (TimeScale): 时间轴的尺度，默认为顺序（无尺度）
        
        Returns:
            Self: 时间轴对象
        """
        self.name = name
        self.scale = scale
        self.events: list[Event] = []
        self._templates: dict[str, Any] = {} # 出题使用的模板
        self._statements: list[str] = [] # 生成的命题

    def add_event(self, *events: Event) -> None:
        """向事件序列添加一个或多个事件

        Args:
            events (Event): 事件对象
        """
        assert all(isinstance(event, Event) for event in events), "事件必须是Event对象"
        self.events.extend(events)

    def _load_templates(self) -> None:
        """加载出题模板"""
        template_file = Path(__file__).parent / "templates" / SCALE_FILES[self.scale]
        with template_file.open(mode='r', encoding='utf8') as f:
            self._templates = json5.load(f)

    def _choose_initial_statement(self, initial_event: Event) -> str:
        """选择初始命题
        
        Args:
            initial_event (Event): 初始事件
            
        Returns:
            str: 命题
        
        Raises:
            TypeError: 不支持的事件类型
        """
        INITIAL_KEY = "initial"
        if isinstance(initial_event, PointEvent):
            return self._choose_statement(self._templates[INITIAL_KEY]["point"], event=initial_event, time=initial_event.time)
        elif isinstance(initial_event, DurationEvent):
            return self._choose_statement(self._templates[INITIAL_KEY]["duration"], event=initial_event, start=initial_event.start_time, end=initial_event.end_time, duration=initial_event.duration)
        else:
            raise TypeError(f"不支持的事件类型：{type(initial_event)}")
    
    def _choose_statement(self, template_lst: list[str], **kwargs: dict[str, Any]) -> str:
        """随机选择一个命题模板并根据参数生成命题
        
        Args:
            template_lst (list[str]): 用于随机选择的命题模板列表
            **kwargs (dict[str, Any]): 用于生成命题的参数
        
        Returns:
            str: 命题

        Raises:
            AssertionError: 未替换的参数
        """
        use_statement = random.choice(template_lst)
        # 利用正则表达式替换被选择模板中的参数，生成命题
        for key, value in kwargs.items():
            use_statement = re.sub(r"\[" + key + r"\]", str(value), use_statement)
        assert "[" not in use_statement, f"未替换的参数：{re.findall(r"\[(.*?)\]", use_statement)}" # 检查是否有未替换的参数
        return use_statement
    
    def _single_point(self, event: PointEvent, question_mode: bool = False) -> str:
        """单个点事件的描述

        Args:
            event (PointEvent): 点事件
            question_mode (bool): 是否是问题模式，默认为False

        Returns:
            str: 对于单个点事件的描述
        """
        return self._choose_statement(self._templates["single_point"], event=event, time=event.time)
    
    def _single_length(self, event: DurationEvent, question_mode: bool = False) -> str:
        """对单个持续事件长度的描述

        Args:
            event (DurationEvent): 持续事件
            question_mode (bool): 是否是问题模式，默认为False

        Returns:
            str: 对于单个持续事件的描述
        """
        return self._choose_statement(self._templates["single_duration"], event=event, length=event.duration)
    
    def _single_duration(self, event: DurationEvent, question_mode: bool = False) -> str:
        """对单个持续事件的描述

        Args:
            event (DurationEvent): 持续事件
            question_mode (bool): 是否是问题模式，默认为False

        Returns:
            str: 对于单个持续事件的描述
        """
        choose_num = 1 if question_mode else 2 # 问题模式只选择一个属性描述持续事件的性质
        output_attrs = random.choices(["start_time", "end_time", "duration"], k=choose_num) # 随机选择2个属性描述持续事件的性质
    
    def _point2point(self, curr_event: PointEvent, new_event: PointEvent) -> str:
        """点事件到点事件关系的描述

        Args:
            curr_event (PointEvent): 已知的点事件
            new_event (PointEvent): 新的点事件

        Returns:
            str: 对于点事件到点事件关系的描述
        """
        template_subtype: str = "point2point" # 模板子类型
        if curr_event.time < new_event.time: # 点事件1在点事件2之前
            return self._choose_statement(self._templates[template_subtype]["before"], event1=curr_event, event2=new_event, diff=new_event.time - curr_event.time)
        elif curr_event.time > new_event.time: # 点事件1在点事件2之后
            return self._choose_statement(self._templates[template_subtype]["after"], event1=curr_event, event2=new_event, diff=curr_event.time - new_event.time)
        else: # 点事件1和点事件2同时发生
            return self._choose_statement(self._templates[template_subtype]["same"], event1=curr_event, event2=new_event)

    def _length2length(self, curr_event: DurationEvent, new_event: DurationEvent) -> str:
        """持续事件到持续事件关系的描述

        Args:
            curr_event (DurationEvent): 已知的持续事件
            new_event (DurationEvent): 新的持续事件

        Returns:
            str: 对于持续事件到持续事件关系的描述
        """
        pass
    
    def _point2duration(self, curr_event: PointEvent, new_event: DurationEvent) -> str:
        """点事件到持续事件的推理

        Args:
            curr_event (PointEvent): 已知的点事件
            new_event (DurationEvent): 新的持续事件

        Raises:
            ValueError: 不支持的描述属性

        Returns:
            str: 命题，即推理结果
        """
        output_attrs = random.choices(["start_time", "end_time", "duration"], k=2) # 随机选择2个属性描述持续事件的性质
        outputs: list[str] = [] # 用于存储输出的命题
        for attr in output_attrs:
            if attr == "start_time": # 描述持续事件的开始时间
                outputs.append(self._point2point(curr_event, new_event.start_event))
            elif attr == "end_time": # 描述持续事件的结束时间
                outputs.append(self._point2point(curr_event, new_event.end_event))
            elif attr == "duration": # 描述持续事件的持续时间
                outputs.append(self._choose_statement(self._templates["point2duration"]["duration"], event=new_event, duration=new_event.duration))
            else: # 不支持的描述属性
                raise ValueError(f"不支持的描述属性：{attr}")
        return "，并且".join(outputs)

    def _duration2point(self, curr_event: DurationEvent, new_event: PointEvent) -> str:
        """持续事件到点事件的推理

        Args:
            curr_event (DurationEvent): 已知的持续事件
            new_event (PointEvent): 新的点事件

        Returns:
            str: 命题，即推理结果
        """
        if new_event.time <= curr_event.start_time: # 点事件在持续事件开始之前或同时开始
            return self._point2point(curr_event.start_event, new_event)
        elif new_event.time >= curr_event.end_time: # 点事件在持续事件结束之后或同时结束
            return self._point2point(curr_event.end_event, new_event)
        else: # 点事件在持续事件中
            base_event: PointEvent = random.choice([curr_event.start_event, curr_event.end_event])
            return self._point2point(base_event, new_event)

    def _duration2duration(self, curr_event: DurationEvent, new_event: DurationEvent) -> str:
        """持续事件到持续事件的推理

        Args:
            curr_event (DurationEvent): 已知的持续事件
            new_event (DurationEvent): 新的持续事件

        Raises:
            ValueError: 不支持的描述属性

        Returns:
            str: 命题，即推理结果
        """
        output_attrs = random.choices(["start_time", "end_time", "duration"], k=2) # 随机选择2个属性描述新的持续事件的性质
        outputs: list[str] = [] # 用于存储输出的命题
        for attr in output_attrs:
            if attr == "start_time": # 描述新的持续事件的开始时间
                outputs.append(self._duration2point(curr_event, new_event.start_event))
            elif attr == "end_time": # 描述新的持续事件的结束时间
                outputs.append(self._duration2point(curr_event, new_event.end_event))
            elif attr == "duration": # 描述新的持续事件的持续时间
                outputs.append(self._choose_statement(self._templates["duration2duration"]["ratio"], event1=curr_event, event2=new_event, fraction=Fraction(new_event.duration, curr_event.duration)))
            else: # 不支持的描述属性
                raise ValueError(f"不支持的描述属性：{attr}")
        return "，并且".join(outputs)
    
    def _event2event(self, new_event: Event, curr_event: Optional[Event] = None,) -> str:
        """根据当前事件和新事件推理出命题
        
        Args:
            new_event (Event): 新事件
            curr_event (Optional[Event]): 当前事件，默认为None
            
        Returns:
            str: 命题，即推理结果

        Raises:
            TypeError: 不支持的推理方式
        """
        if isinstance(curr_event, PointEvent) and isinstance(new_event, PointEvent):
            return self._point2point(curr_event, new_event)
        elif isinstance(curr_event, PointEvent) and isinstance(new_event, DurationEvent):
            return self._point2duration(curr_event, new_event)
        elif isinstance(curr_event, DurationEvent) and isinstance(new_event, PointEvent):
            return self._duration2point(curr_event, new_event)
        elif isinstance(curr_event, DurationEvent) and isinstance(new_event, DurationEvent):
            return self._duration2duration(curr_event, new_event)
        else:
            raise TypeError(f"不支持的推理方式：{type(curr_event)} -> {type(new_event)}")
    
    def run(self, random_seed: Optional[int] = None) -> dict[str, str]:
        """运行时间轴，输出一组对事件的陈述
        
        Args:
            random_seed (Optional[int]): 随机种子，默认为None（不设置随机种子）
        
        Returns:
            dict[str, str]: 生成的命题
        """
        assert len(self.events) > 1, "时间轴上没有2个或以上的事件，请通过add_event方法添加事件"
        searched_events: list[Event] = [] # 已经搜索过的事件
        self._load_templates() # 加载出题模板
        if random_seed is not None:
            random.seed(random_seed) # 设置随机种子
        # 随机一个起始事件，并将其加入到已搜索事件列表中
        start_event: Event = random.choice(self.events)
        searched_events.append(start_event)
        self._statements.append(self._choose_initial_statement(start_event)) # 输出初始命题
        # 不断抽取新的事件生成命题，直到所有事件都被抽取
        while any(event not in searched_events for event in self.events):
            # 从已搜索事件中随机抽取一个事件
            current_event: Event = random.choice(searched_events)
            # 从未搜索事件中随机抽取一个事件
            next_event: Event = random.choice([event for event in self.events if event not in searched_events])
            # 输出命题
            print(f"正在推理：{current_event} -> {next_event}")
            self._statements.append(self._event2event(current_event, next_event))
            # 将新抽取的事件加入到已搜索事件列表中
            searched_events.append(next_event)

        return {"statements": "\n".join(self._statements)} # 返回生成的命题