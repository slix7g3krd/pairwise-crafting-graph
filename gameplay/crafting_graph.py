"""第 63 批：合成一把剑需要矿石，矿石的配方又要一把剑，点了合成后材料扣了但产..."""

def has_cycle(graph):
    """环检测。"""
    raise NotImplementedError("TODO: has_cycle")

def topo_order(graph):
    """拓扑顺序。"""
    raise NotImplementedError("TODO: topo_order")

def rollback_materials(current, used):
    """替代回滚。"""
    raise NotImplementedError("TODO: rollback_materials")

def batch_deduct(stock, per_item, quantity):
    """批量扣料。"""
    raise NotImplementedError("TODO: batch_deduct")

def reserve(shared, needed):
    """材料预留。"""
    raise NotImplementedError("TODO: reserve")

def round_qty(value):
    """取整规则。"""
    raise NotImplementedError("TODO: round_qty")

def byproduct(base, extra):
    """副产物。"""
    raise NotImplementedError("TODO: byproduct")

def cache_valid(version, current):
    """缓存失效。"""
    raise NotImplementedError("TODO: cache_valid")

def station_tier(required, actual):
    """工作站层级。"""
    raise NotImplementedError("TODO: station_tier")

def async_order(sequence):
    """异步顺序。"""
    raise NotImplementedError("TODO: async_order")

def recursion_limit(depth, max_depth):
    """递归上限。"""
    raise NotImplementedError("TODO: recursion_limit")

def same_table(client, server):
    """前后端同表。"""
    raise NotImplementedError("TODO: same_table")

def refund_all(used, returned):
    """完整回滚。"""
    raise NotImplementedError("TODO: refund_all")

def recipe_valid(recipe, inventory):
    """配方校验。"""
    raise NotImplementedError("TODO: recipe_valid")

def depth_limit(depth, limit):
    """递归深度。"""
    raise NotImplementedError("TODO: depth_limit")
