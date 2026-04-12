<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### beijing_subway — Beijing Subway Transfer Assistant | 北京地铁换乘助手
- **Purpose**: Plan the optimal transfer route (shortest travel time) for the Beijing Subway from the starting station to the destination based on departure time. It automatically adapts to speed differences during morning and evening rush hours, as well as transfer time penalties.
- **Input Parameters**:
  - `start`: **str**, name of the starting station, example: `"Xizhimen"`
  - `end`: **str**, name of the destination station, example: `"Beijing South Railway Station"`
  - `time`: **int | None**, optional, departure time (minutes counted from 00:00 on the current day). The system current time will be used if not provided.
- **Output**: Natural language route plan, including transit lines, transfer stations, and total travel time (unit: minutes).
- **Dependencies & Files**:
  - Required library: `geopy`. Run `pip install geopy` if not installed.
  - Data files: `station.json`, `graph.txt`. These must be placed in the same directory as `tool.py`.
- **Operation Rules**:
  - Morning rush hour: 07:00–09:00 (420–540 minutes)
  - Evening rush hour: 17:00–19:00 (1020–1140 minutes)
  - Rush hour speed: 35km/h, transfer penalty: 5 minutes
  - Off-peak speed: 40km/h, transfer penalty: 2 minutes
  - Adjustable parameters: Modify `PEAK_PENALTY` / `OFF_PEAK_PENALTY` in `tool.py`
- **Scope Limitation**: Only supports the Beijing Subway. Data files require regular updates to align with the latest subway lines.
- **用途**：根据出发时间，规划北京地铁从起点站到终点站的最优换乘路线（时间最短），自动适配早晚高峰速度差异与换乘时间惩罚。
- **输入参数**：
  - `start`：**str**，起点站名称，示例：`"西直门"`
  - `end`：**str**，终点站名称，示例：`"北京南站"`
  - `time`：**int | None**，可选，出发时间（距当日 00:00 的分钟数），不传入则使用系统当前时间
- **输出**：自然语言路线方案，包含乘坐线路、换乘站、总耗时（单位：分钟）
- **依赖与文件**：
  - 依赖库：`geopy`，未安装执行 `pip install geopy`
  - 数据文件：`station.json`、`graph.txt`，必须与 `tool.py` 同目录
- **运行规则**：
  - 早高峰：07:00–09:00（420–540 分钟）
  - 晚高峰：17:00–19:00（1020–1140 分钟）
  - 高峰速度：35km/h，换乘惩罚：5 分钟
  - 平峰速度：40km/h，换乘惩罚：2 分钟
  - 调整参数：修改 `tool.py` 中 `PEAK_PENALTY` / `OFF_PEAK_PENALTY`
- **范围限制**：仅支持北京地铁，需定期更新数据文件匹配最新线路