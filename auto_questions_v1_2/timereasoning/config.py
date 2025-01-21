# encoding: utf8
# date: 2024-11-27

from pathlib import Path

# language settings

START = "start"
END = "end"

LANG_CONFIG = {
    "zh": {
        START: "开始",
        END: "结束"
    },
    "en": {
        START: "start",
        END: "end"
    }
}

# 1-8新增：名字和代词的关系
NAME_PRONOUN = {
    "Jack": "he",
}

# 1-21新增：记录命题难度的文件路径
PROP_DIFFICULTY_PATH = Path(__file__).parent / "difficulty/prop_difficulty.json5"