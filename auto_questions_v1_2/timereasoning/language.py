# encoding: utf8
# date: 2024-12-12

from pycnnum import num2cn # 引入中文数字转换库
import calendar
import sys
from pathlib import Path
from typing import Any
import re

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from proposition import language, prop, machines
from timereasoning import scene, timescale

# constants.
# 匹配英文中数字-名词结构的pattern
NUM_NOUN_PATTERN = re.compile(r"([0-9]+) ([a-zA-Z]+)\(s\)")

class TimeParallelScene(language.LangParallelScene):
    def __init__(self, original_scene: scene.TimeScene) -> None:
        super().__init__(original_scene)
        self.original_scene: scene.TimeScene = original_scene # 原始场景
        self.scale = original_scene.scale # 时间尺度
        # 添加中英文模板
        self.add_temp("zh", timescale.choose_templates(self.scale, "zh"))
        self.add_temp("en", timescale.choose_templates(self.scale, "en"))

    def _decide_noun_number(self, lang: str, text: str) -> str:
        """根据语言调整名词的单复数

        Args:
            lang (str): 语言
            text (str): 文本

        Raises:
            ValueError: 若语言类型未知，则报错

        Returns:
            str: 调整后的文本
        """
        if lang == "zh":
            return text
        elif lang == "en":
            # 获得数字-名词结构的全部匹配
            matches = NUM_NOUN_PATTERN.findall(text)
            # 根据数字调整名词
            for num, noun in matches:
                if int(num) == 1:
                    text = text.replace(f"{num} {noun}(s)", f"{num} {noun}")
                else:
                    text = text.replace(f"{num} {noun}(s)", f"{num} {noun}s")
            return text
        else:
            raise ValueError(f"Unknown language: {lang}")
    
    def get_statements(self, lang) -> list[str]:
        statements = super().get_statements(lang)
        # 利用原始场景的语言属性调整陈述表达
        self.original_scene.lang = lang
        new_statements = [self.original_scene._exp_trans(i) for i in statements]
        # 12-24新增：调整名词的单复数表达
        new_statements = [self._decide_noun_number(lang, i) for i in new_statements]
        return new_statements

    def get_question(self, lang) -> str:
        question = super().get_question(lang)
        # 利用原始场景的语言属性调整问题表达
        self.original_scene.lang = lang
        new_question = self.original_scene._exp_trans(question)
        # 12-24新增：调整名词的单复数表达
        new_question = self._decide_noun_number(lang, new_question)
        return new_question

    def get_answers(self, lang) -> dict[str, Any]:
        answer_info = super().get_answers(lang)
        if "time" in (typ := self._ask_info.get(prop.TYPE)):
            if self.scale == timescale.TimeScale.Weekday and lang == "zh":
                for k, v in answer_info[machines.OPTIONS].items():
                    # 11-30更新：为防止“以上选项均不正确”报错，加入try-except结构排错
                    try:
                        num = int(v)
                    except ValueError:
                        continue
                    zh_num = num2cn(v)
                    zh_num = "日" if zh_num == "零" else zh_num
                    answer_info[machines.OPTIONS][k] = zh_num
            elif self.scale == timescale.TimeScale.Weekday and lang == "en":
                for k, v in answer_info[machines.OPTIONS].items():
                    # 11-30更新：为防止“以上选项均不正确”报错，加入try-except结构排错
                    try:
                        num = int(v)
                    except ValueError:
                        continue
                    answer_info[machines.OPTIONS][k] = calendar.day_name[int(v)-1]
            elif self.scale == timescale.TimeScale.Month and lang == "en":
                for k, v in answer_info[machines.OPTIONS].items():
                    # 11-30更新：为防止“以上选项均不正确”报错，加入try-except结构排错
                    try:
                        num = int(v)
                    except ValueError:
                        continue
                    answer_info[machines.OPTIONS][k] = calendar.month_name[int(v)]
        return answer_info

    def get_options(self, lang: str) -> dict[str, Any]:
        option_dic = super().get_options(lang)
        new_dic = {k: self.original_scene._exp_trans(v) for k, v in option_dic.items()}
        # 12-24新增：调整名词的单复数表达
        new_dic = {k: self._decide_noun_number(lang, v) for k, v in new_dic.items()}
        return new_dic