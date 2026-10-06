"""纯函数算法内核：从最高位开始，以 1 为置换表起始编号。"""
from functools import lru_cache

P10 = (3, 5, 2, 7, 4, 10, 1, 9, 8, 6)
P8 = (6, 3, 7, 4, 8, 5, 10, 9)
IP = (2, 6, 3, 1, 4, 8, 5, 7)
IP_INVERSE = (4, 1, 3, 5, 7, 2, 8, 6)
EP = (4, 1, 2, 3, 2, 3, 4, 1)
P4 = (2, 4, 3, 1)
S1 = ((1, 0, 3, 2), (3, 2, 1, 0), (0, 2, 1, 3), (3, 1, 0, 2))
# 作业指定版本：最后一行为 (2, 1, 0, 3)，与常见教材不同。
S2 = ((0, 1, 2, 3), (2, 3, 1, 0), (3, 0, 1, 2), (2, 1, 0, 3))


def require_uint(value: int, width: int, label: str) -> int:
    if type(value) is not int or not 0 <= value < (1 << width):
        raise ValueError(f"{label}必须是 0 到 {(1 << width) - 1} 的整数")
    return value


def parse_bits(value: str, width: int, label: str = "输入") -> int:
    if not isinstance(value, str) or len(value) != width or set(value) - {"0", "1"}:
        raise ValueError(f"{label}必须恰好包含 {width} 个 0 或 1")
    return int(value, 2)


def permute(value: int, width: int, positions: tuple[int, ...]) -> int:
    result = 0
    for position in positions:
        result = (result << 1) | ((value >> (width - position)) & 1)
    return result


def rotate_half(half: int, distance: int) -> int:
    return ((half << distance) | (half >> (5 - distance))) & 31


@lru_cache(maxsize=1024)
def subkeys(key: int) -> tuple[int, int]:
    require_uint(key, 10, "密钥")
    arranged = permute(key, 10, P10)
    left, right = arranged >> 5, arranged & 31
    left, right = rotate_half(left, 1), rotate_half(right, 1)
    first = permute((left << 5) | right, 10, P8)
    # 第二次在 LS-1 结果上再循环左移 2 位（累计 3 位）。
    left, right = rotate_half(left, 2), rotate_half(right, 2)
    return first, permute((left << 5) | right, 10, P8)


def substitute(nibble: int, table: tuple) -> int:
    row = ((nibble >> 2) & 2) | (nibble & 1)
    column = (nibble >> 1) & 3
    return table[row][column]


def round_details(block: int, key: int) -> dict:
    left, right = block >> 4, block & 15
    expanded = permute(right, 4, EP)
    mixed = expanded ^ key
    first, second = substitute(mixed >> 4, S1), substitute(mixed & 15, S2)
    joined = (first << 2) | second
    transformed = permute(joined, 4, P4)
    output = ((left ^ transformed) << 4) | right
    return {"input": f"{block:08b}", "EP": f"{expanded:08b}",
            "xor": f"{mixed:08b}", "S1": f"{first:02b}", "S2": f"{second:02b}",
            "P4": f"{transformed:04b}", "output": f"{output:08b}"}


# 两张小表减少全空间枚举的开销，不缓存明密文结果。
ROUND_F = tuple(tuple(permute((substitute((permute(right, 4, EP) ^ key) >> 4, S1) << 2)
                                      | substitute((permute(right, 4, EP) ^ key) & 15, S2), 4, P4)
                            for right in range(16)) for key in range(256))
INITIAL = tuple(permute(block, 8, IP) for block in range(256))
FINAL = tuple(permute(block, 8, IP_INVERSE) for block in range(256))


def _crypt(block: int, keys: tuple[int, int]) -> int:
    current = INITIAL[block]
    left, right = current >> 4, current & 15
    left ^= ROUND_F[keys[0]][right]
    left, right = right, left
    left ^= ROUND_F[keys[1]][right]
    return FINAL[(left << 4) | right]


def encrypt_block(block: int, key: int) -> int:
    require_uint(block, 8, "分组")
    require_uint(key, 10, "密钥")
    return _crypt(block, subkeys(key))


def decrypt_block(block: int, key: int) -> int:
    require_uint(block, 8, "分组")
    require_uint(key, 10, "密钥")
    return _crypt(block, subkeys(key)[::-1])


def trace_block(block: int, key: int, decrypt: bool = False) -> dict:
    require_uint(block, 8, "分组")
    require_uint(key, 10, "密钥")
    first, second = subkeys(key)
    used = (second, first) if decrypt else (first, second)
    initial = INITIAL[block]
    round_one = round_details(initial, used[0])
    middle = int(round_one["output"], 2)
    swapped = ((middle & 15) << 4) | (middle >> 4)
    round_two = round_details(swapped, used[1])
    output = FINAL[int(round_two["output"], 2)]
    return {"input": f"{block:08b}", "key": f"{key:010b}", "K1": f"{first:08b}",
            "K2": f"{second:08b}", "round_keys": [f"{k:08b}" for k in used],
            "IP": f"{initial:08b}", "round_one": round_one, "SW": f"{swapped:08b}",
            "round_two": round_two, "output": f"{output:08b}", "hex": f"{output:02X}"}
