# Copyright (C) 2026 xhdlphzr
#
# This file is part of EasyMate.
#
# EasyMate is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
#
# EasyMate is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with EasyMate.  If not, see <https://www.gnu.org/licenses/>.

import json
import os
import heapq
from geopy.distance import distance

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(__file__)

# 加载站点数据
with open(os.path.join(BASE_DIR, 'station.json'), 'r', encoding='utf-8') as f:
    station_data = json.load(f)

# 构建站名到ID的映射
name_to_id = {}
for sid, info in station_data.items():
    name = info['站点']
    name_to_id[name] = int(sid)

STATION_SIZE = 409

# 加载邻接矩阵图数据
graph = []
with open(os.path.join(BASE_DIR, 'graph.txt'), 'r', encoding='utf-8') as f:
    for line in f:
        row = list(map(int, line.strip().split()))
        graph.append(row)

for i in range(STATION_SIZE):
    for j in range(STATION_SIZE):
        if graph[i][j] <= 0:
            graph[i][j] = -1

# 换乘惩罚因子（分钟），可调
PEAK_PENALTY = 5      # 高峰期换乘惩罚
OFF_PEAK_PENALTY = 2  # 平峰期换乘惩罚

def a_star(start_id, end_id, time, graph, peak_penalty, off_peak_penalty):
    """
    A*算法实现（内部使用，依赖 station_data）
    """
    # 根据时间判断速度 (m/h) 和惩罚
    def now_speed(t):
        return 35000 if (420 <= t < 540) or (1020 <= t < 1140) else 40000

    def now_punishment(t):
        return peak_penalty if (420 <= t < 540) or (1020 <= t < 1140) else off_peak_penalty

    # 启发式函数（直线距离/速度）
    def heuristic(idx1, idx2):
        coord1 = (station_data[str(idx1)]['纬度'], station_data[str(idx1)]['经度'])
        coord2 = (station_data[str(idx2)]['纬度'], station_data[str(idx2)]['经度'])
        dis = distance(coord1, coord2).m
        return round(dis / 40000 * 60)  # 固定速度 40000 m/h

    # 是否换乘
    def is_transfer(prev, now, nxt):
        if prev == -1 or nxt == -1:
            return False
        lines_prev = set(station_data[str(prev)]['线路'])
        lines_now = set(station_data[str(now)]['线路'])
        lines_nxt = set(station_data[str(nxt)]['线路'])
        return (lines_prev & lines_now) != (lines_now & lines_nxt)

    # 初始化
    open_list = []
    heapq.heappush(open_list, (heuristic(start_id, end_id), heuristic(start_id, end_id), start_id))
    close_set = set()
    prev = [-1] * (STATION_SIZE + 1)
    g = [float('inf')] * (STATION_SIZE + 1)
    g[start_id] = time

    while open_list:
        f, h, u = heapq.heappop(open_list)
        if f > g[u] + heuristic(u, end_id):
            continue
        if u in close_set:
            continue
        close_set.add(u)

        if u == end_id:
            # 重构路径
            path = []
            cur = u
            while cur != -1:
                path.append(station_data[str(cur)]['站点'])
                cur = prev[cur]
            path.reverse()
            return g[end_id], g[end_id] - time, path

        for v in range(1, STATION_SIZE + 1):
            w = graph[u][v]
            if w == -1:
                continue
            travel_time = round(w / now_speed(g[u]) * 60)  # 分钟
            if is_transfer(prev[u], u, v):
                travel_time += now_punishment(g[u])

            new_g = g[u] + travel_time
            if new_g < g[v]:
                g[v] = new_g
                prev[v] = u
                heapq.heappush(open_list, (new_g + heuristic(v, end_id), heuristic(v, end_id), v))

    # 没有路径
    return None

def execute(start: str, end: str, time: int = None) -> str:
    """
    查询北京地铁从 start 到 end 的最优路径（按时间最短）。
    参数：
        start: 起点站名
        end: 终点站名
        time: 出发时间（距离当天 0:00 的分钟数），默认为当前时间
    返回：
        换乘方案文本
    """
    if start not in name_to_id:
        return f"未找到起点站：{start}"
    if end not in name_to_id:
        return f"未找到终点站：{end}"

    start_id = name_to_id[start]
    end_id = name_to_id[end]

    # 若未提供时间，使用当前本地时间
    if time is None:
        import datetime
        now = datetime.datetime.now()
        time = now.hour * 60 + now.minute

    result = a_star(start_id, end_id, time, graph, PEAK_PENALTY, OFF_PEAK_PENALTY)
    if result is None:
        return f"未找到从 {start} 到 {end} 的路径。"

    total_minutes, travel_minutes, path = result
    # 格式化输出
    lines = []
    current_line = None
    for i, station in enumerate(path):
        if i == 0:
            lines.append(f"从 {station} 出发")
        else:
            # 获取该站所属线路（取第一条线路）
            sid = name_to_id[station]
            station_info = station_data[str(sid)]
            line = station_info['线路'][0] if station_info['线路'] else '未知线路'
            if current_line is None:
                current_line = line
                lines.append(f"乘坐 {line} 线")
            elif line != current_line:
                lines.append(f"在 {station} 换乘 {line} 线")
                current_line = line
    lines.append(f"到达 {path[-1]}")
    lines.append(f"全程约 {travel_minutes} 分钟（含换乘时间）")
    return "\n".join(lines)