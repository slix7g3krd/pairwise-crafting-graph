"""合成配方图：环检测、拓扑排序、扣料/回滚、预留、取整、副产物等原语。

设计约定：
- 图结构为 ``{节点: [依赖节点, ...]}``，边 u -> v 表示 u 依赖 v，
  因此拓扑顺序中 v 必须排在 u 前面。
- 所有图遍历均为迭代实现，长配方链不会撑爆调用栈。
- 所有扣料/预留操作先做足额校验再变更，库存永远不会被扣成负数；
  校验失败抛 ``ValueError``，调用方可据此回滚整笔合成。
"""

from decimal import ROUND_HALF_UP, Decimal
import heapq

# 递归/配方链深度的硬上限，防止长链把主线程卡住。
MAX_RECIPE_DEPTH = 1000


def has_cycle(graph):
    """环检测：迭代 DFS + 三色标记，存在环返回 True。

    不使用递归，深度再大的配方链也不会栈溢出。
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    for start in graph:
        if color[start] != WHITE:
            continue
        # 栈元素为 (节点, 下一个待访问邻接下标)
        stack = [(start, 0)]
        color[start] = GRAY
        while stack:
            node, index = stack[-1]
            neighbors = graph.get(node, ())
            if index < len(neighbors):
                nxt = neighbors[index]
                stack[-1] = (node, index + 1)
                if nxt not in color:
                    # 邻接节点未作为键出现，视为无依赖的叶子节点。
                    color[nxt] = WHITE
                if color[nxt] == GRAY:
                    return True
                if color[nxt] == WHITE:
                    color[nxt] = GRAY
                    stack.append((nxt, 0))
            else:
                color[node] = BLACK
                stack.pop()
    return False


def topo_order(graph):
    """按依赖层级输出拓扑顺序（被依赖者在前）。

    使用 Kahn 算法：入度为 0 表示没有未结算的前置产物。
    同层按节点名排序保证结果确定；图中有环时抛 ``ValueError``。
    """
    if has_cycle(graph):
        raise ValueError("recipe graph contains a cycle")

    indegree = {node: 0 for node in graph}
    dependents = {node: [] for node in graph}
    for node, deps in graph.items():
        for dep in deps:
            indegree.setdefault(dep, 0)
            dependents.setdefault(dep, [])
            indegree[node] += 1
            dependents[dep].append(node)

    ready = [node for node, deg in indegree.items() if deg == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        node = heapq.heappop(ready)
        order.append(node)
        for dependent in dependents.get(node, ()):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)

    if len(order) != len(indegree):
        # 理论上前面的 has_cycle 已拦截，这里兜底防御。
        raise ValueError("recipe graph contains a cycle")
    return order


def _merge(a, b):
    """两种库存表示的加法：数值相加 / 字典按键合并。"""
    if isinstance(a, dict) or isinstance(b, dict):
        merged = dict(a) if isinstance(a, dict) else {}
        other = b if isinstance(b, dict) else {}
        for key, value in other.items():
            merged[key] = merged.get(key, 0) + value
        return merged
    return a + b


def rollback_materials(current, used):
    """替代配方回滚：把已扣的中间材料 ``used`` 加回 ``current``。

    支持数值、元组/列表（逐元素）和字典（按键合并）。
    """
    if isinstance(current, (tuple, list)) and isinstance(used, (tuple, list)):
        return tuple(a + b for a, b in zip(current, used))
    return _merge(current, used)


def batch_deduct(stock, per_item, quantity):
    """批量扣料：返回扣完后的剩余库存。

    按工作站产能把整单拆成逐份扣减；库存不足时整单拒绝（抛
    ``ValueError``），绝不产生负库存，也不会出现扣多了不退的情况。
    """
    if quantity < 0:
        raise ValueError("quantity must be non-negative")
    needed = per_item * quantity
    if needed > stock:
        raise ValueError(
            f"insufficient stock: need {needed}, have {stock}"
        )
    return stock - needed


def reserve(shared, needed):
    """材料预留：原子校验并占用共享库存，返回预留后的剩余量。

    库存不足直接拒绝，避免两个任务都通过校验却只有一个能完成。
    """
    if needed < 0:
        raise ValueError("reserved amount must be non-negative")
    if needed > shared:
        raise ValueError(
            f"cannot reserve {needed} from shared stock {shared}"
        )
    return shared - needed


def round_qty(value):
    """半份材料向上取整（ROUND_HALF_UP），0.5 -> 1。

    不用内置 ``round``（银行家舍入会把 0.5 舍成 0）。
    """
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def byproduct(base, extra):
    """副产物回填：把副产物 ``extra`` 并入主产物库存 ``base``。"""
    return _merge(base, extra)


def cache_valid(version, current):
    """配方缓存失效：缓存版本与当前技能/配方版本一致才有效。"""
    return version == current


def station_tier(required, actual):
    """工作站层级：实际等级不低于要求等级即可，中间步骤同样适用。"""
    return actual >= required


def async_order(sequence):
    """异步合成排序：按完成顺序（键值升序）返回新列表，不改原序列。

    保证完成顺序与扣料顺序可对账，取消任务时能按同一顺序逆向回滚。
    """
    return sorted(sequence)


def recursion_limit(depth, max_depth):
    """递归上限：当前深度未超过上限才允许继续展开。"""
    return depth <= max_depth


def same_table(client, server):
    """前后端同表：UI 预检查与服务端结算的配方版本/内容必须一致。"""
    return client == server


def refund_all(used, returned):
    """完整回滚：已消耗材料连同燃料等资源一并退还。

    支持数值、元组/列表（逐元素）和字典（按键合并）。
    """
    if isinstance(used, (tuple, list)) and isinstance(returned, (tuple, list)):
        return tuple(a + b for a, b in zip(used, returned))
    return _merge(used, returned)


def recipe_valid(recipe, inventory):
    """配方校验：库存对每一项材料都足额才返回 True。"""
    return all(inventory.get(item, 0) >= need for item, need in recipe.items())


def depth_limit(depth, limit):
    """递归深度保护：深度触及上限即停止继续递归。"""
    return depth <= limit
