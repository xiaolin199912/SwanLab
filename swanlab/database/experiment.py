#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
@DATE: 2023-12-01 19:33:40
@File: swanlab/database/expriment.py
@IDE: vscode
@Description:
    实验类，操作和记录实验相关的信息
"""
from .table import ExperimentPoxy
from .chart import ChartTable
import os
from ..env import swc
from typing import Union
from ..utils import create_time, generate_color, get_package_version
from .system import get_system_info
import sys
import random
from .modules import BaseType
from urllib.parse import quote
from ..log import swanlog as swl


class ExperimentTable(ExperimentPoxy):
    """初始化一个实验，需要传入一些实验的基本信息，如实验名称，实验描述，实验配置等信息"""

    def __init__(self, experiment_id: int, name: str, description: str, config: dict, index: int):
        # 初始化一个实验配置，name必须保证唯一，但是不在此处检查，而是在创建实验的时候检查
        # 创建name对应的文件夹
        swc.add_exp(name)
        if not os.path.exists(swc.logs_folder):
            os.makedirs(swc.logs_folder)
        super().__init__(swc.logs_folder)
        self.experiment_id = experiment_id
        self.name = name
        # tags数据不会被序列化
        self.tags = {}
        self.system = get_system_info()
        self.description = description
        self.config = config
        self.argv = sys.argv
        self.index = index
        self.status = 0  # 0: 正在运行，1: 运行成功，-1: 运行失败
        self.__chart = ChartTable(experiment_id=experiment_id)
        self.color = generate_color(experiment_id)

    def __dict__(self) -> dict:
        """序列化此对象

        Returns
        -------
        dict
            序列化后的字典对象
        """
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "version": get_package_version(),
            "status": self.status,
            "description": self.description,
            "config": self.config,
            "color": self.color,
            "system": self.system,
            "argv": self.argv,
            "index": self.index,
            "create_time": self.create_time,
            "update_time": self.update_time,
        }

    def is_tag_exist(self, tag: str) -> bool:
        """判断tag是否已经存在于此实验中

        Parameters
        ----------
        tag : str
            tag名称

        Returns
        -------
        bool
            如果存在，返回True，否则返回False
        """
        return tag in self.tags

    def check_data_type(self, data: Union[float, int, BaseType]):
        """检查data的数据类型，如果不是期望的数据类型，尝试转换为float
        如果转换出错，返回None

        Parameters
        ----------
        data : Union[float, int, BaseType]
            数据
        """
        # 检查数据类型，data必须是int，float或者可以被float化的类型，或者swanlab.BaseType的子类
        if not isinstance(data, (int, float, BaseType)):
            try:
                return float(data)
            except:
                return None
        return data

    def add(self, tag: str, data: Union[float, int, BaseType], step: int = None):
        """记录一条新的tag数据

        Parameters
        ----------
        tag : str
            tag名称
        data : Union[float, str]
            tag数据，可以是浮点型，也可以是字符串，具体与添加的图表类型有关系
        namespace : str
            命名空间，用于区分不同的数据资源（对应{experiment_name}$chart中的tag）
        step : int
            步数，用于区分同一tag下的不同数据，如果为None，则自动加1
        """
        # 如果是第一次添加
        if not self.is_tag_exist(tag):
            # 在实验中记录此tag,初始化一些临时数据
            self.tags[tag] = {"num": 0, "max": None, "min": None, "indexs": []}
            # 在chart中记录此tag，将data传入
            if isinstance(data, BaseType):
                data.tag = tag
                data.step = 1 if step is None else step
            self.__chart.add(tag=tag, data=data)
        if self.__chart.is_chart_error(tag):
            return swl.warning(f"Chart {tag} has been marked as error, ignored.")
        # 更新tag的数量，并拿到tag的索引
        # 通过self.tags寻找到对应的tag配置
        summary = self.tags[tag]
        # 更新tag的数量，并拿到tag的索引
        tag_num = self.update_tag_num(tag)
        index = tag_num if step is None else step
        # 如果step已经存在，那么就warning
        if index in summary["indexs"]:
            swl.warning(f"The step '{index}' of tag: {tag} already exists and is no longer updated.")
            return
        # 更新tag的索引
        if isinstance(data, BaseType) and data.tag is None:
            data.tag = tag
            data.step = index
        data = data.get_data() if isinstance(data, BaseType) else data
        data = self.__chart.try_convert_data(data, tag)
        # 记录最大、最小值
        summary["max"] = data if summary["max"] is None else max(summary["max"], data)
        summary["min"] = data if summary["min"] is None else min(summary["min"], data)
        summary["indexs"].append(index)
        # 新的summary是被保存的数据
        summary = {"num": summary["num"], "max": summary["max"], "min": summary["min"]}
        # 只有保存时的tag是被编码后的tag
        tag = quote(tag, safe="")
        self.save_tag(tag, data, index, tag_num, summary)

    def update_tag_num(self, tag: str) -> int:
        self.tags[tag]["num"] += 1
        return self.tags[tag]["num"]

    def success(self):
        """实验成功完成，更新实验状态"""
        self.update_time = create_time()
        self.status = 1

    def fail(self):
        """实验失败，更新状态"""
        self.update_time = create_time()
        self.status = -1


# 树木名称列表
_tree_names = [
    "oak",  # 橡树
    "maple",  # 枫树
    "pine",  # 松树
    "beech",  # 榉树
    "willow",  # 柳树
    "birch",  # 桦树
    "spruce",  # 云杉
    "cypress",  # 柏树
    "cedar",  # 雪松
    "hemlock",  # 铁杉
    "poplar",  # 杨树
    "redwood",  # 红杉
]

# 正向形容词列表
_positive_adjectives = [
    "lush",  # 茂盛的
    "majestic",  # 壮观的
    "vibrant",  # 蓬勃的
    "verdant",  # 翠绿的
    "beautiful",  # 美丽的
    "sturdy",  # 稳固的
    "abundant",  # 富饶的
    "tall",  # 高大的
    "shady",  # 树荫浓密的
    "hardy",  # 耐寒的
]


def generate_random_tree_name(exists_name: [str] = []) -> str:
    """随机生成树木名称, 以树木的名称命名实验

    Parameters
    ----------
    exists_name : [str], optional
        已存在的树木名称, by default []

    Returns
    -------
    str
        随机生成的树木名称, 例如: lush-oak-1
    """
    # 随机选择一个树木名称和一个正向形容词
    tree_name = random.choice(_tree_names)
    adjective = random.choice(_positive_adjectives)

    # 拼接生成的树木名称
    generated_name = f"{adjective}-{tree_name}-{exists_name.__len__() + 1}"
    return generated_name


def make_experiment_name_unique(name: str, exists_name: [str]) -> str:
    """检查实验名称是否已经存在，如果存在，调用一个递归函数，后缀加1

    Parameters
    ----------
    name : str
        待检查的实验名称

    exists_name : [str]
        已经存在的实验名称列表

    Returns
    -------
    str
        检查后的实验名称
    """
    if name in exists_name:
        # 如果名称已经存在，递归调用自己，后缀加1，需要判断后缀是否存在以及是否可以转换为数字
        name_arr = name.split("-")
        # 如果最后一个元素是数字，那么后缀加1
        if name_arr[-1].isdigit():
            name_arr[-1] = str(int(name_arr[-1]) + 1)
        else:
            # 如果最后一个元素不是数字，那么添加一个1
            name_arr.append("1")
        # 重新拼接名称
        new_name = "-".join(name_arr)
        return make_experiment_name_unique(new_name, exists_name)
    return name


def check_experiment_name(name: str):
    """检查实验名称是否符合规范，如果不符合规范，报错

    Parameters
    ----------
    name : str
        名称
    """
    return