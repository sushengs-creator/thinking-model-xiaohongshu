#!/usr/bin/env python3
"""Portable regression tests. Run with Python 3.9+ and Pillow; no network or user files."""
import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit('Tests require Pillow. Use a Python environment with Pillow installed.')

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


copy = load_module('check_copy')
images = load_module('check_images')
TITLES = ['思维模型070:大数定律——' + q for q in
          ['越多越准吗？', '数据可信吗？', '样本够大吗？', '越测越偏吗？', '平均靠谱吗？']]
BODY = '🔑先检查样本怎么来的。\n#思维模型\n#认知升级\n#心理学\n#大数定律\n#判断力'


class CopyChecks(unittest.TestCase):
    def check(self, expected, titles=TITLES, body=BODY, **kwargs):
        result = copy.check('070', '大数定律', titles, body, **kwargs)
        self.assertEqual(result['ok'], expected, result)
        return result

    def test_default_and_recommended(self):
        self.check(True, title=TITLES[0] + '\n')

    def test_default_candidate_count(self):
        self.check(False, titles=TITLES[:1])

    def test_explicit_candidate_count(self):
        self.check(True, titles=TITLES[:1], title_count=1)

    def test_duplicate_candidates(self):
        self.check(False, titles=TITLES[:4] + TITLES[:1])

    def test_recommended_mismatch(self):
        self.check(False, title=TITLES[1])

    def test_recommended_multiple_lines(self):
        self.check(False, title='\n'.join(TITLES[:2]))

    def test_empty_question(self):
        self.check(False, titles=['思维模型070:大数定律——'] + TITLES[1:])

    def test_punctuation_only_question(self):
        self.check(False, titles=['思维模型070:大数定律——？？'] + TITLES[1:])

    def test_title_length(self):
        self.check(False, titles=['思维模型070:大数定律——数据越多就一定越靠谱吗？'] + TITLES[1:])

    def test_body_hard_limit(self):
        self.check(False, body='文' * 1001 + '\n' + BODY)

    def test_soft_targets_remain_warnings(self):
        result = self.check(True, body='文' * 810 + '\n' + BODY)
        self.assertTrue(result['warnings'])

    def test_user_topic_override(self):
        body = '🔑检查样本。\n#思维模型\n#样本偏差'
        self.check(True, body=body, hashtags=['思维模型', '样本偏差'])

    def test_override_still_matches_topics(self):
        self.check(False, hashtags=['思维模型', '样本偏差'])

    def test_default_topics_not_silently_disabled(self):
        self.check(False, body='🔑检查样本。\n#思维模型\n#样本偏差')

    def test_text_after_topics(self):
        self.check(False, body=BODY + '\n又一段正文。')

    def test_code_fence_in_body(self):
        self.check(False, body='```\n正文\n```\n' + BODY)

    def test_body_only(self):
        result = self.check(True, titles=None)
        self.assertEqual(result['scope'], ['body'])

    def test_titles_only(self):
        result = self.check(True, body=None, title=TITLES[0])
        self.assertEqual(result['scope'], ['titles'])

    def test_no_input(self):
        self.check(False, titles=None, body=None)

    def test_ascii_number(self):
        self.assertFalse(copy.check('０７０', '大数定律', TITLES, BODY)['ok'])

    def test_number_normalization(self):
        self.assertTrue(copy.check('70', '大数定律', TITLES, BODY)['ok'])
        self.assertTrue(copy.check('1000', '杠杆', ['思维模型1000:杠杆——为何要借力？'],
                                   BODY, title_count=1)['ok'])

    def test_cli_scopes_and_override_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for filename, content in [('titles.txt', '\n'.join(TITLES)), ('title.txt', TITLES[0]), ('body.txt', BODY)]:
                (directory / filename).write_text(content, encoding='utf-8')
            base = [sys.executable, str(HERE / 'check_copy.py'), '--number', '070', '--name', '大数定律']
            cases = [(['--body', str(directory / 'body.txt')], 0),
                     (['--titles', str(directory / 'titles.txt'), '--title', str(directory / 'title.txt')], 0),
                     ([], 2),
                     (['--body', str(directory / 'body.txt'), '--hashtags', '思维模型', '#思维模型'], 2),
                     (['--body', str(directory / 'body.txt'), '--hashtags', '两个 词'], 2),
                     (['--title', str(directory / 'title.txt')], 2)]
            for arguments, exit_code in cases:
                with self.subTest(arguments=arguments):
                    result = subprocess.run(base + arguments, capture_output=True, text=True)
                    self.assertEqual(result.returncode, exit_code, result.stdout + result.stderr)


class ImageChecks(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        for page in range(1, 8):
            Image.new('RGB', (1080, 1440), (page * 30, page * 20, page * 10)).save(self.path(page))

    def path(self, page):
        return self.directory / f'xhs-070-p{page:02}.png'

    def check(self, expected, **kwargs):
        result = images.check(self.directory, '070', **kwargs)
        self.assertEqual(result['ok'], expected, result)
        return result

    def test_real_decodable_images(self):
        self.check(True)

    def test_header_only_image(self):
        self.path(1).write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\x0dIHDR' + struct.pack('>II', 1080, 1440))
        self.check(False)

    def test_truncated_png(self):
        self.path(1).write_bytes(self.path(1).read_bytes()[:80])
        self.check(False)

    def test_truncated_jpeg(self):
        target = self.path(1).with_suffix('.jpg')
        self.path(1).unlink()
        Image.new('RGB', (1080, 1440), 'red').save(target)
        target.write_bytes(target.read_bytes()[:-20])
        self.check(False)

    def test_wrong_extension(self):
        Image.new('RGB', (1080, 1440), 'red').save(self.path(1), format='JPEG')
        self.check(False)

    def test_duplicate_image(self):
        self.path(2).write_bytes(self.path(1).read_bytes())
        self.check(False)

    def test_missing_page(self):
        self.path(7).unlink()
        self.check(False)

    def test_other_model_page(self):
        self.path(7).rename(self.directory / 'xhs-071-p07.png')
        self.check(False)

    def test_extra_unsupported_image(self):
        Image.new('RGB', (10, 10), 'red').save(self.directory / 'extra.gif')
        self.check(False)

    def test_non_uniform_size(self):
        Image.new('RGB', (1086, 1448), 'red').save(self.path(1))
        self.check(False)

    def test_wrong_ratio(self):
        Image.new('RGB', (1080, 1441), 'red').save(self.path(1))
        self.check(False)

    def test_size_warning_and_strict_option(self):
        for page in range(1, 8):
            Image.new('RGB', (1086, 1448), (page * 30, page * 20, page * 10)).save(self.path(page))
        self.assertTrue(self.check(True)['warnings'])
        self.check(False, strict_size=True)

    def test_missing_decoder_fails_clearly(self):
        result = subprocess.run([sys.executable, '-S', str(HERE / 'check_images.py'), '--number', '070',
                                 '--directory', str(self.directory)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse(json.loads(result.stdout)['decoding_checked'])


if __name__ == '__main__':
    unittest.main()
