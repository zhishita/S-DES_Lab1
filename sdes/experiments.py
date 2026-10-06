"""字节转换、完整密钥搜索和固定明文碰撞分析。"""
from datetime import datetime, timezone
from time import perf_counter_ns
from .core import encrypt_block, decrypt_block, require_uint, subkeys


def encode_text(text: str, key: int, encoding: str = "ascii") -> dict:
    require_uint(key, 10, "密钥")
    if encoding not in ("ascii", "utf-8"):
        raise ValueError("编码必须是 ascii 或 utf-8")
    raw = text.encode(encoding, errors="strict")
    cipher = bytes(encrypt_block(byte, key) for byte in raw)
    return {"hex": cipher.hex().upper(), "binary": " ".join(f"{b:08b}" for b in cipher),
            "escaped": repr(cipher.decode("latin-1")), "bytes": len(raw), "encoding": encoding}


def decode_text(cipher_hex: str, key: int, encoding: str = "ascii") -> dict:
    require_uint(key, 10, "密钥")
    if encoding not in ("ascii", "utf-8"):
        raise ValueError("编码必须是 ascii 或 utf-8")
    cipher = bytes.fromhex(cipher_hex)
    plain = bytes(decrypt_block(byte, key) for byte in cipher)
    return {"text": plain.decode(encoding, errors="strict"), "hex": plain.hex().upper(), "bytes": len(plain)}


def crack_keys(pairs: list[tuple[int, int]], progress=None) -> dict:
    if not pairs:
        raise ValueError("至少需要一组明文—密文对")
    for plain, cipher in pairs:
        require_uint(plain, 8, "明文")
        require_uint(cipher, 8, "密文")
    # 冷启动：清除子密钥缓存后计时，算法常量表的导入时间另计。
    subkeys.cache_clear()
    start_time = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    start = perf_counter_ns()
    candidates, timeline = [], []
    for key in range(1024):
        if all(encrypt_block(plain, key) == cipher for plain, cipher in pairs):
            candidates.append(f"{key:010b}")
        if (key + 1) % 64 == 0:
            event = {"checked": key + 1, "elapsed_ms": (perf_counter_ns() - start) / 1e6,
                     "candidates": candidates.copy()}
            timeline.append(event)
            if progress is not None:
                progress(event)
    elapsed = (perf_counter_ns() - start) / 1e6
    return {"started_utc": start_time, "finished_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
            "elapsed_ms": elapsed, "checked": 1024, "candidates": candidates, "timeline": timeline,
            "pairs": [[f"{p:08b}", f"{c:08b}"] for p, c in pairs]}


def collision_report(plain: int) -> dict:
    require_uint(plain, 8, "明文")
    buckets = [[] for _ in range(256)]
    for key in range(1024):
        buckets[encrypt_block(plain, key)].append(f"{key:010b}")
    nonempty = [b for b in buckets if b]
    collisions = [{"cipher": f"{index:08b}", "keys": keys, "count": len(keys)}
                  for index, keys in enumerate(buckets) if len(keys) > 1]
    return {"plain": f"{plain:08b}", "distinct_ciphertexts": len(nonempty),
            "collision_buckets": len(collisions), "max_bucket": max(map(len, nonempty)),
            "unique_buckets": sum(len(b) == 1 for b in nonempty), "collisions": collisions}
