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
from proposition.config import SEMICOLON, COLON # 引入标点符号用于串联表达
from proposition.graph import Graph

class Scene(metaclass = abc.ABCMeta):
    """
    推理场景的抽象类
    用于定义推理场景的基本属性和操作
    """
    def __init__(self, guide: str = "") -> None:
        """初始化推理场景

        Args:
            guide (str, optional): 引导语. 默认为空字符串.
        """
        self.guide = guide # 引导语
        self.relations: list[relation.Relation] = [] # 关系列表
        self.rules: list[rule.Rule] = [] # 规则列表
        self.temps: dict[str, list[str]] = [] # 模板字典
        # 命题收集变量
        self._init_props: list[prop.Proposition] = []
        self._all_props: list[prop.Proposition] = []
        self._chosen_group: list[prop.Proposition] = []
        self._statements: list[str] = []
        self._asked_prop: prop.Proposition = None
        self._ask_info: dict[str, Any] = {}
        self._value_range: dict[str, list[Any]] = dict()
        self._knowledges: list[prop.Proposition] = []
        self.graph: Graph = None
        self.chain: str = ""

    def add_knowledge(self, number: int = 5, seed: Union[int, float, None] = None) -> None:
        """添加知识命题

        Args:
            number (int): 要添加的知识命题数量. 默认为5.
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
        """
        assert number > 0, "知识命题数量必须大于0"
        random.seed(seed)
        print(f"开始添加知识命题.共添加{number}个.")
    
    def get_all_props(self) -> None:
        """获得场景的全部命题"""
        assert len(self._init_props) >= 2, "命题数量必须大于等于2"
        print("开始生成全部命题！")
        curr_props = deepcopy(self._init_props)
        knowledge = deepcopy(self._knowledges)
        rm = RM(curr_props, self.relations, self.rules, knowledge)
        self._all_props = rm.run()
        print(f"全部命题生成完毕！生成了{len(self._all_props)}个命题")

    def get_all_groups(self) -> None:
        """调用搜索机，以发现可行的陈述命题组合
        """
        assert len(self._all_props) > 0, "必须先生成全部命题"
        print("开始搜索一组可行的命题组合.")
        knowledge = deepcopy(self._knowledges)
        sm = SM(self._init_props, self._all_props, self.relations, self.rules, knowledge)
        self._chosen_group = sm.run()
        print(f"命题组合搜索结束.")
        print(f"获取推理图.")
        rm = RM(deepcopy(self._chosen_group), self.relations, self.rules, deepcopy(self._knowledges), graph_construct=True)
        rm.run()
        self.graph = rm.graph
        print(f"推理图获取完毕.")

    def get_statements(self) -> list[str]:
        """获取一组命题组合的全部陈述

        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.

        Returns:
            list[str]: 一组命题组合的全部陈述
        """
        # assert len(self._all_groups) > 0, "必须先获取可以表述全部情形的命题组合"
        # random.seed(seed)
        # idxs = random.choice(self._all_groups) # 选择一组命题
        # self._chosen_group = [self._all_props[i] for i in idxs] # 选中的命题组合
        self._statements = [i.state(self.temps) for i in self._chosen_group] # 陈述列表
        print("得到随机选择一组命题的陈述.")
        return self._statements

    @abc.abstractmethod
    def ask(self, seed: Union[int, float, None] = None) -> Dict[str, Any]:
        """随机选择一个命题，提问，并根据具体情况获得备选项，最后返回问题信息

        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.

        Returns:
            Dict[str, Any]: 问题信息
        """
        # 修改：选择的命题需要是未进入描述的命题
        # 修改：提问的命题需要是可提问的命题
        print("随机选择一个未进入描述的命题，提问.")
        self._asked_prop = random.choice([i for i in self._all_props if not i.got(self._chosen_group) and i.askable])
        self._ask_info = self._asked_prop.ask(self.temps)
        print("提问完毕.")
        return self._ask_info

    def get_answers(self, seed: Union[int, float, None] = None, options: int = 4, all_wrong_prob: float = .1) -> Dict[str, Any]:
        """获取选项和正确答案

        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
            options (int, optional): 选项数量. 默认为4.
            all_wrong_prob (float, optional): 全部错误选项的概率. 默认为0.1.

        Returns:
            Dict[str, Any]: 答案信息
        """
        assert self._asked_prop is not None, "必须先执行ask()方法进行提问"
        am = AM(self._all_props, self._asked_prop, self._ask_info, seed, options, all_wrong_prob)
        for k, v in self._value_range.items():
            am.set_value_range(k, v)
        return am.run()
    
    def get_chain(self) -> str:
        assert self._asked_prop is not None, "必须先执行ask()方法进行提问"
        reason_path = self.graph.backtrace(self._asked_prop)
        self.chain = "\n".join([i.state(self.temps) for i in reason_path])
        return self.chain
    
    def run(self, execute: int = 10, seed: Union[int, float, None] = None) -> list[dict[str, Any]]:
        """运行场景，获取一组题目

        Args:
            execute (int, optional): 运行次数. 默认为10.
            limit (Optional[int], optional): 搜索深度限制. 默认为None(根据隐藏值计算).
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
        
        Returns:
            list[dict[str, Any]]: 一组题目
        """
        self.get_all_props()
        question_list = []
        for i in range(execute):
            print(f"开始第{i + 1}次获取.")
            self.get_all_groups()
            self.get_statements()
            self.ask(seed)
            answers = self.get_answers(seed)
            chain = self.get_chain()
            if answers is None:
                print("未能获取答案，跳过.")
                continue
            text = self.guide + COLON + SEMICOLON.join(self._statements) # 题面文本，由引导语和陈述组成
            item = {"guide": self.guide, "statement": self._statements, "text": text, "question": self._ask_info[prop.SENTENCE],} | answers | {"chain": chain}
            question_list.append(item)
        print(f"获取题目{execute}次，获得题目{len(question_list)}个.")
        return question_list