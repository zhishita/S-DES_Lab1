"""从真实计算生成五关结果和可分享的原始记录，运行目录为仓库根目录。"""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
from time import perf_counter
from sdes.core import encrypt_block, decrypt_block, trace_block
from sdes.experiments import encode_text, decode_text, crack_keys, collision_report

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / 'results'


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    RESULTS.mkdir(exist_ok=True)
    start = perf_counter()
    result = {'generated_utc':datetime.now(timezone.utc).isoformat(),
              'python':sys.version, 'platform':platform.platform(), 'runtime_seconds':0}
    # 测试本项目函数，而非复写同一实现做期望值。
    tests = subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],
                           cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    (RESULTS / 'unit_tests.txt').write_text(tests.stdout + tests.stderr, encoding='utf-8')
    if tests.returncode:
        raise RuntimeError('单元测试失败，见 results/unit_tests.txt')
    result['unit_tests'] = 'passed'
    result['stage1'] = [trace_block(p,k) for p,k in ((151,642),(63,329),(0,0),(255,1023))]
    table = bytearray()
    full_start = perf_counter()
    for key in range(1024):
        ciphertexts = set()
        for plain in range(256):
            cipher = encrypt_block(plain, key)
            assert decrypt_block(cipher, key) == plain, (plain,key,cipher)
            table.append(cipher)
            ciphertexts.add(cipher)
        assert len(ciphertexts) == 256, key
    python_hash = hashlib.sha256(table).hexdigest()
    result['full_roundtrip'] = {'combinations':len(table),'key_permutations':1024,
                               'seconds':perf_counter()-full_start,'sha256':python_hash}
    # Node 不可用时显式报错，不能将缺失交叉测试包装成通过。
    node = subprocess.run(['node',str(ROOT / 'tests/reference.js')],capture_output=True,text=True,check=True)
    independent = json.loads(node.stdout)
    assert independent['checked'] == len(table) and independent['sha256'] == python_hash
    with (ROOT / 'tests/peer_vectors.csv').open(encoding='utf-8-sig',newline='') as file:
        rows = list(csv.DictReader(file))
    errors = []
    for index,row in enumerate(rows,2):
        plain,key,cipher = (int(row[name],2) for name in ('pt','key','ct'))
        if encrypt_block(plain,key) != cipher or decrypt_block(cipher,key) != plain:
            errors.append(index)
    assert not errors, errors
    result['stage2'] = {'independent_javascript':independent, 'peer_csv_rows':len(rows),
                        'peer_mismatches':errors,
                        'peer_source':'https://github.com/Qisheng-Zhang/Information_Security_Lab1/blob/main/对方.csv',
                        'peer_csv_sha256':hashlib.sha256((ROOT / 'tests/peer_vectors.csv').read_bytes()).hexdigest(),
                        'method':'公开静态测试向量互验；未声称与该组现场协作或运行其源码'}
    string_examples = []
    for text,encoding in [('Hello, S-DES!','ascii'),('This is a test','ascii'),('信息安全导论 🔐','utf-8')]:
        encoded = encode_text(text,642,encoding)
        decoded = decode_text(encoded['hex'],642,encoding)
        assert decoded['text'] == text
        string_examples.append({'text':text, **encoded,'restored':decoded['text']})
    result['stage3'] = string_examples
    selected_plain = random.Random(20261006).randrange(256)
    selected_key = random.Random(20261007).randrange(1024)
    single = crack_keys([(151,encrypt_block(151,642))])
    multiple = crack_keys([(p,encrypt_block(p,642)) for p in (151,0,255,65)])
    discriminating = crack_keys([(p,encrypt_block(p,642)) for p in (151,0,255,65,8)])
    randomized = crack_keys([(selected_plain,encrypt_block(selected_plain,selected_key))])
    result['stage4'] = {'single':single, 'multiple':multiple, 'discriminating':discriminating,
                        'random_seed_plain':20261006,'random_seed_key':20261007,
                        'random_actual_key':f'{selected_key:010b}','random_pair':randomized}
    save_json(RESULTS/'bruteforce_timeline.json',single)
    # 按每个固定明文枚举所有密钥，报告完整 256 行数据。
    reports = [collision_report(plain) for plain in range(256)]
    with (RESULTS/'collision_summary.csv').open('w',encoding='utf-8',newline='') as file:
        writer = csv.DictWriter(file,fieldnames=['plain','distinct_ciphertexts','collision_buckets','max_bucket','unique_buckets'])
        writer.writeheader()
        writer.writerows({k:r[k] for k in writer.fieldnames} for r in reports)
    mappings = {}
    for key in range(1024):
        mapping = bytes(table[key*256:(key+1)*256])
        mappings.setdefault(mapping,[]).append(f'{key:010b}')
    equivalent = [keys for keys in mappings.values() if len(keys)>1]
    save_json(RESULTS/'equivalent_keys.json', equivalent)
    result['stage5'] = {'plaintexts':256,'keys_per_plaintext':1024,
                        'all_plaintexts_have_collisions':all(r['collision_buckets']>0 for r in reports),
                        'mean_distinct_ciphertexts':sum(r['distinct_ciphertexts'] for r in reports)/256,
                        'min_distinct_ciphertexts':min(r['distinct_ciphertexts'] for r in reports),
                        'max_distinct_ciphertexts':max(r['distinct_ciphertexts'] for r in reports),
                        'max_bucket':max(r['max_bucket'] for r in reports),
                        'zero_plain':reports[0], 'distinct_full_mappings':len(mappings),
                        'equivalent_key_groups':len(equivalent)}
    result['runtime_seconds'] = perf_counter()-start
    save_json(RESULTS/'experiment_results.json',result)
    with (RESULTS/'cross_vectors.csv').open('w',encoding='utf-8',newline='') as file:
        writer = csv.writer(file);writer.writerow(['pt','key','ct'])
        generator = random.Random(20261006)
        for _ in range(200):
            p,k = generator.randrange(256),generator.randrange(1024)
            writer.writerow([f'{p:08b}',f'{k:010b}',f'{encrypt_block(p,k):08b}'])
    print(json.dumps({'unit_tests':result['unit_tests'],'roundtrip':len(table),'python_js_sha256':python_hash,
                      'peer_vectors':len(rows),'single_candidates':single['candidates'],
                      'multi_candidates':multiple['candidates'],'elapsed_ms':single['elapsed_ms'],
                      'mean_distinct_ciphertexts':result['stage5']['mean_distinct_ciphertexts'],
                      'max_bucket':result['stage5']['max_bucket'],'equivalent_groups':len(equivalent)},ensure_ascii=False))


if __name__ == '__main__':
    main()
