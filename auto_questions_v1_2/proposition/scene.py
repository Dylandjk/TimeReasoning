# encoding: utf8
# date: 2024-09-04
# author: Qin Yuhang

"""
关于推理场景的基本定义和基本操作
"""

import abc
from copy import deepcopy
import random
from typing import Union, Any, Dict, Optional
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.prop as prop
import proposition.relation as relation
import proposition.rule as rule
from proposition.machines import ReasonMachine as RM
from proposition.machines import SearchMachine as SM
from proposition.machines import AnswerMachine as AM

class Scene(metaclass = abc.ABCMeta):
    """
    推理场景的抽象类
    用于定义推理场景的基本属性和操作
    """
    def __init__(self, guide: str = "") -> None:
        self.guide = guide # 引导语
        self.relations: list[relation.Relation] = [] # 关系列表
        self.rules: list[rule.Rule] = [] # 规则列表
        self.temps: dict[str, list[str]] = [] # 模板字典
        # 命题收集变量
        self._init_props: list[prop.Proposition] = []
        self._all_props: list[prop.Proposition] = []
        self._all_groups: list[list[int]] = []
        self._statements: list[str] = []
        self._asked_prop: prop.Proposition = None
        self._ask_info: dict[str, Any] = {}
        self._value_range: dict[str, list[Any]] = dict()

    def get_all_props(self) -> None:
        """获得场景的全部命题"""
        assert len(self._init_props) >= 2, "命题数量必须大于等于2"
        print("开始生成全部命题！")
        curr_props = deepcopy(self._init_props)
        rm = RM(curr_props, self.relations, self.rules)
        self._all_props = rm.run()
        print(f"全部命题生成完毕！生成了{len(self._all_props)}个命题")

    def get_all_groups(self, limit: Optional[int] = None) -> None:
        """调用搜索机，扩圈以发现可行的陈述命题组合
        
        Args:
            limit (int | None, optional): 限制搜索深度. 默认为None.
        """
        assert len(self._all_props) > 0, "必须先生成全部命题"
        print("开始扩圈！")
        sm = SM(self._init_props, self._all_props, self.relations, self.rules, limit)
        self._all_groups = sm.run()
        print(f"扩圈完毕！共获得命题组合{len(self._all_groups)}个")

    def get_statements(self, seed: Union[int, float, None] = None) -> list[str]:
        """获取一组命题组合的全部陈述

        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.

        Returns:
            list[str]: 一组命题组合的全部陈述
        """
        assert len(self._all_groups) > 0, "必须先获取可以表述全部情形的命题组合"
        random.seed(seed)
        idxs = random.choice(self._all_groups) # 选择一组命题
        self._statements = [self._all_props[i].state(self.temps) for i in idxs]
        print("随机选择一组命题，得到其陈述.")
        return self._statements

    @abc.abstractmethod
    def ask(self, seed: Union[int, float, None] = None) -> Dict[str, Any]:
        """随机选择一个命题，提问，并根据具体情况获得备选项，最后返回问题信息

        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.

        Returns:
            Dict[str, Any]: 问题信息
        """
        print("随机选择一个命题，提问.")
        self._asked_prop = random.choice(self._all_props)
        self._ask_info = self._asked_prop.ask(self.temps)
        print("提问完毕.")
        return self._ask_info

    def get_answers(self, seed: Union[int, float, None] = None, options: int = 4, all_wrong_prob: float = .1):
        """获取选项和正确答案

        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
            options (int, optional): 选项数量. 默认为4.
            all_wrong_prob (float, optional): 全部错误选项的概率. 默认为0.1.

        Returns:
            _type_: _description_
        """
        assert self._asked_prop is not None, "必须先执行ask()方法进行提问"
        am = AM(self._all_props, self._asked_prop, self._ask_info, seed, options, all_wrong_prob)
        for k, v in self._value_range.items():
            am.set_value_range(k, v)
        return am.run()
    
    def run(self, execute: int = 10, limit: Optional[int] = None, seed: Union[int, float, None] = None) -> list[dict[str, Any]]:
        """运行场景，获取一组题目

        Args:
            execute (int, optional): 运行次数. 默认为10.
            limit (Optional[int], optional): 搜索深度限制. 默认为None(根据隐藏值计算).
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
        
        Returns:
            list[dict[str, Any]]: 一组题目
        """
        self.get_all_props()
        self.get_all_groups(limit)
        self.get_statements(seed)
        question_list = []
        for _ in range(execute):
            self.ask(seed)
            answers = self.get_answers(seed)
            item = {"guide": self.guide, "statement": self._statements, "question": self._ask_info[prop.SENTENCE],} | answers
            question_list.append(item)
        print(f"获取题目{execute}次，获得题目{len(question_list)}个.")
        return question_list