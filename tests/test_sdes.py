import unittest
from sdes.core import (encrypt_block, decrypt_block, subkeys, trace_block,
                       parse_bits, permute, IP, IP_INVERSE)
from sdes.experiments import encode_text, decode_text, crack_keys, collision_report
from sdes.webapp import dispatch


class AlgorithmTests(unittest.TestCase):
    def test_published_examples(self):
        self.assertEqual(subkeys(0b1010000010), (0b10100100, 0b01000011))
        self.assertEqual(encrypt_block(0b10010111, 0b1010000010), 0b00111000)
        self.assertEqual(encrypt_block(0b00111111, 0b0101001001), 0b10101011)

    def test_inverse_permutation(self):
        for block in range(256):
            self.assertEqual(permute(permute(block, 8, IP), 8, IP_INVERSE), block)

    def test_trace_matches_fast_path(self):
        # 每个主密钥均覆盖，正向与逆向的逐轮计算核对查表实现。
        for key in range(1024):
            block = (key * 73) % 256
            self.assertEqual(int(trace_block(block, key)["output"], 2), encrypt_block(block, key))
            self.assertEqual(int(trace_block(block, key, True)["output"], 2), decrypt_block(block, key))

    def test_validation(self):
        for value in ("", "0010", "01234567", " 0000000", "000000000"):
            with self.assertRaises(ValueError):
                parse_bits(value, 8)
        for block, key in ((-1, 0), (256, 0), (0, -1), (0, 1024), (True, 0), (1.5, 2)):
            with self.assertRaises(ValueError):
                encrypt_block(block, key)

    def test_ascii_all_bytes(self):
        text = ''.join(chr(n) for n in range(128))
        for key in (0, 642, 1023):
            encrypted = encode_text(text, key)
            self.assertEqual(decode_text(encrypted["hex"], key)["text"], text)
            self.assertEqual(encrypted["bytes"], 128)
        self.assertEqual(decode_text(encode_text('', 642)["hex"], 642)["text"], '')

    def test_unicode_and_errors(self):
        text = '信息安全导论 🔐'
        self.assertEqual(decode_text(encode_text(text, 642, 'utf-8')["hex"], 642, 'utf-8')["text"], text)
        with self.assertRaises(UnicodeEncodeError):
            encode_text(text, 642)
        for value in ('0', 'GG'):
            with self.assertRaises(ValueError):
                decode_text(value, 642)
        with self.assertRaises(ValueError):
            encode_text('', 1024)

    def test_complete_search(self):
        plain, key = 151, 642
        cipher = encrypt_block(plain, key)
        result = crack_keys([(plain, cipher)])
        self.assertEqual(result['checked'], 1024)
        self.assertIn(f'{key:010b}', result['candidates'])
        self.assertEqual(result['candidates'], ['0111001010', '1010000010', '1011001010'])
        self.assertEqual(len(result['timeline']), 16)
        many = crack_keys([(p, encrypt_block(p, key)) for p in range(256)])
        self.assertIn(f'{key:010b}', many['candidates'])
        self.assertLessEqual(len(many['candidates']), len(result['candidates']))
        discriminating = crack_keys([(p, encrypt_block(p, key)) for p in (151, 0, 255, 65, 8)])
        self.assertEqual(discriminating['candidates'], [f'{key:010b}'])
        self.assertEqual(crack_keys([(plain,cipher),(plain,cipher ^ 1)])['candidates'], [])
        with self.assertRaises(ValueError):
            crack_keys([])

    def test_collision_accounting(self):
        result = collision_report(0)
        self.assertGreater(result['collision_buckets'], 0)
        count = sum(row['count'] for row in result['collisions']) + result['unique_buckets']
        self.assertEqual(count, 1024)
        for row in result['collisions']:
            self.assertTrue(all(encrypt_block(0, int(key, 2)) == int(row['cipher'], 2) for key in row['keys']))

    def test_request_validation(self):
        for payload in ({'action':'unknown'}, {'action':'crack','pairs':'0 1 2'}, {'action':'crack','pairs':''}):
            with self.assertRaises(ValueError):
                dispatch(payload)
        self.assertEqual(dispatch({'action':'encrypt','key':'1010000010','block':'10010111'})['output'], '00111000')


if __name__ == '__main__':
    unittest.main()
