#!/usr/bin/env python3
"""Verify and decode seven PNG/JPEG files with Pillow. Visual QA remains required."""
import argparse
import hashlib
import io
import json
import re
import warnings as warning_control
from pathlib import Path


def dimensions(data):
    from PIL import Image

    with warning_control.catch_warnings():
        warning_control.simplefilter('error', Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(data)) as picture:
                kind = picture.format
                if kind not in {'PNG', 'JPEG'}:
                    raise ValueError('只接受实际格式为PNG或JPEG的图片')
                if getattr(picture, 'n_frames', 1) != 1:
                    raise ValueError('每页须为一张静态图片，不能使用多帧图片')
                picture.verify()
            # verify() alone does not decode JPEG pixels. Reopen and load every pixel.
            with Image.open(io.BytesIO(data)) as picture:
                picture.load()
                width, height = picture.size
            return kind.lower(), width, height
        except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise ValueError(f'图片像素量超出解码器安全限制：{exc}') from exc


def check(directory, number, strict_size=False):
    errors, warnings, rows = [], [], []
    if not re.fullmatch(r'[0-9]+', number):
        return {'ok': False, 'errors': ['编号须为ASCII数字（0—9）。'], 'warnings': [], 'images': []}
    try:
        from PIL import Image  # noqa: F401: dependency preflight, no header-only fallback
    except ImportError:
        return {'ok': False, 'errors': ['缺少Pillow：请使用已安装Pillow的Python运行；未完成图片解码检查。'],
                'warnings': [], 'images': [], 'decoding_checked': False}
    if not directory.is_dir():
        return {'ok': False, 'errors': ['图片目录不存在'], 'warnings': [], 'images': []}
    extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff', '.avif', '.heic', '.heif', '.svg'}
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in extensions)
    if len(files) != 7:
        errors.append(f'目录中有{len(files)}张图片，应恰好7张；预览图请放其他目录。')
    masters = Path(__file__).resolve().parents[1] / 'assets' / 'masters'
    master_hashes = {hashlib.sha256(p.read_bytes()).hexdigest() for p in masters.glob('*.jpg')}
    found, hashes, sizes = {}, {}, set()
    pattern = re.compile(r'xhs-' + re.escape(number.zfill(3)) + r'-p(0[1-7])\.(png|jpg|jpeg)$', re.I)
    for path in files:
        match = pattern.fullmatch(path.name)
        if not match:
            errors.append(f'文件名不符合本组编号和页码：{path.name}')
        else:
            page = int(match.group(1))
            if page in found:
                errors.append(f'P{page}重复。')
            found[page] = path.name
        try:
            data = path.read_bytes()
        except OSError as exc:
            errors.append(f'{path.name}无法读取：{exc}')
            continue
        digest = hashlib.sha256(data).hexdigest()
        if digest in hashes:
            errors.append(f'{path.name}与{hashes[digest]}内容完全相同。')
        hashes[digest] = path.name
        if digest in master_hashes:
            errors.append(f'{path.name}仍是原始049母版，不能当作新图交付。')
        try:
            kind, width, height = dimensions(data)
            expected_extensions = {'.png'} if kind == 'png' else {'.jpg', '.jpeg'}
            if path.suffix.lower() not in expected_extensions:
                errors.append(f'{path.name}扩展名与真实图片格式不一致。')
            if width <= 0 or height <= 0 or width * 4 != height * 3:
                errors.append(f'{path.name}实测{width}×{height}，不符合3:4。')
            if (width, height) != (1080, 1440):
                message = f'{path.name}实测{width}×{height}，与默认目标1080×1440不同，需如实交代。'
                (errors if strict_size else warnings).append(message)
            sizes.add((width, height))
            rows.append({'file': path.name, 'format': kind, 'width': width, 'height': height,
                         'sha256': digest, 'decodable': True})
        except (ValueError, OSError, SyntaxError) as exc:
            errors.append(f'{path.name}：{exc}')
    missing = sorted(set(range(1, 8)) - set(found))
    if missing:
        errors.append(f'缺少页码：{missing}')
    if len(sizes) > 1:
        errors.append('7张图片的像素尺寸不统一。')
    return {'ok': not errors, 'images': rows, 'errors': errors, 'warnings': warnings,
            'decoding_checked': True,
            'manual_checks': ['逐页与母版和定稿对照', '中文准确', '主题正确', '缩略图可读', '无遮挡裁切', '未混用稿件版本']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--number', required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--strict-size', action='store_true', help='将1080×1440尺寸差异作为错误')
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9]+', args.number):
        parser.error('number须为ASCII数字编号（0—9）')
    result = check(args.directory, args.number, args.strict_size)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
