#!/usr/bin/env python3
"""Conservative local copy checks; no network or third-party dependencies."""
import argparse
import json
import re
from pathlib import Path


def count(text):
    # Include spaces, punctuation, hashtags and every emoji code point.
    # Newlines do not count. This is not the platform's grapheme counter.
    return len(text.replace('\r', '').replace('\n', ''))


def check_titles(number, name, titles, selected, title_count, errors, warnings):
    prefix = f'思维模型{number}:{name}——'
    rows = []
    if len(titles) != title_count:
        errors.append(f'标题候选应为{title_count}个，实际为{len(titles)}个。')
    if len(titles) != len(set(titles)):
        errors.append('标题候选存在完全重复项。')
    if selected is None:
        warnings.append('未提供推荐标题文件；完整制作包须另核对title.txt与首个候选一致。')
    else:
        selected = selected.rstrip('\r\n')
        if not selected or '\n' in selected or '\r' in selected:
            errors.append('推荐标题文件须恰含一行非空标题。')
        elif not titles or selected != titles[0]:
            errors.append('推荐标题须与titles.txt第一行完全一致。')
    for i, candidate in enumerate(titles, 1):
        n = count(candidate)
        rows.append({'index': i, 'characters': n, 'title': candidate})
        if n > 20:
            errors.append(f'标题{i}为{n}字符，超过20。')
        if candidate != candidate.strip():
            errors.append(f'标题{i}带有首尾空白。')
        if not candidate.startswith(prefix):
            errors.append(f'标题{i}未保留完整固定前缀：{prefix}')
        else:
            question = candidate[len(prefix):].strip()
            if not question or not any(char.isalnum() for char in question):
                errors.append(f'标题{i}缺少有内容的痛点问句。')
            elif not re.search(r'[?？吗呢么]$', question):
                warnings.append(f'标题{i}需要人工确认是否为清楚的痛点问句。')
        if re.search('[\U0001F000-\U0001FAFF\u2600-\u27BF\u200d\ufe0f]', candidate):
            errors.append(f'标题{i}含emoji或相关变体字符。')
    return rows


def check_body(number, body, hashtags, errors, warnings):
    body_length = count(body)
    if not body.strip():
        errors.append('正文为空。')
    elif body_length > 1000:
        errors.append(f'正文含符号与话题共{body_length}字符，超过1000。')
    elif body_length > 800:
        warnings.append('正文超过800的精简目标，但仍在1000硬上限内。')
    if body.lstrip().startswith(('【小红书正文】', '小红书正文：',
                                '思维模型' + number + ':', '思维模型' + number + '：')):
        errors.append('正文文件混入交付标签或标题。')
    if '**' in body:
        errors.append('正文含Markdown加粗符号。')
    if '```' in body or '~~~' in body:
        errors.append('正文含Markdown代码围栏。')
    tags = re.findall(r'(?<!\S)#([^\s#]+)', body)
    if hashtags is None:
        fixed = {'思维模型', '认知升级', '心理学'}
        if len(tags) != 5 or len(set(tags)) != 5 or not fixed.issubset(tags):
            errors.append('默认话题应为5个不重复标签：3个固定话题加2个相关变量。用户明确覆盖时使用--hashtags。')
        hashtag_policy = {'mode': 'default', 'count': 5, 'required': sorted(fixed)}
    else:
        if len(tags) != len(hashtags) or len(set(tags)) != len(tags) or set(tags) != set(hashtags):
            errors.append('文末话题与--hashtags指定的完整话题集合不一致。')
        hashtag_policy = {'mode': 'explicit_override', 'expected': hashtags}
    tag_start = re.search(r'(?<!\S)#[^\s#]+', body)
    if tag_start:
        rest = re.sub(r'(?<!\S)#[^\s#]+', '', body[tag_start.start():])
        if rest.strip():
            errors.append('话题应集中在末尾，话题之后不能再接正文。')
    long_lines = [i for i, line in enumerate(body.splitlines(), 1) if count(line) > 20]
    if long_lines:
        warnings.append(f'以下行超过20字符的排版目标，需检查语义和手机阅读：{long_lines}')
    return body_length, tags, hashtag_policy


def check(number, name, titles=None, body=None, title=None, title_count=5, hashtags=None):
    errors, warnings = [], []
    if not re.fullmatch(r'[0-9]+', number):
        errors.append('编号须为ASCII数字（0—9）。')
    if not name.strip() or name != name.strip():
        errors.append('模型名称不能为空或带有首尾空白。')
    number = number.zfill(3)
    rows = []
    body_length, tags, hashtag_policy = None, [], None
    if titles is None and body is None:
        errors.append('至少提供标题候选或正文之一。')
    if title is not None and titles is None:
        errors.append('核对推荐标题时必须提供标题候选。')
    if titles is not None:
        rows = check_titles(number, name, titles, title, title_count, errors, warnings)
    if body is not None:
        body_length, tags, hashtag_policy = check_body(number, body, hashtags, errors, warnings)
    return {'ok': not errors, 'counting': 'Unicode码点；含空格、标点、emoji及话题；不含换行；非平台计数',
            'scope': [label for label, present in [('titles', titles is not None), ('body', body is not None)] if present],
            'titles': rows, 'expected_title_count': title_count,
            'selected_title_checked': title is not None,
            'body_characters': body_length, 'hashtags': tags, 'hashtag_policy': hashtag_policy,
            'errors': errors, 'warnings': warnings,
            'manual_checks': (['概念和边界准确', '语言自然'] +
                              (['humanizer-zh实际应用', 'emoji适量', '话题相关'] if body is not None else []) +
                              (['问句与原文相符', '候选切入点有区别'] if titles is not None else []))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--number', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--titles', type=Path, help='标题候选文件；与--body至少提供一个')
    parser.add_argument('--body', type=Path, help='正文文件；与--titles至少提供一个')
    parser.add_argument('--title', type=Path, help='推荐标题文件；完整制作包须提供，并与候选第一行核对')
    parser.add_argument('--title-count', type=int, default=5, help='候选数，默认5；仅在用户明确覆盖时修改')
    parser.add_argument('--hashtags', nargs='*', help='仅在用户明确覆盖时传入完整话题集合，可带#；显式空列表表示无话题')
    args = parser.parse_args()
    if args.titles is None and args.body is None:
        parser.error('至少提供--titles或--body之一')
    if args.title is not None and args.titles is None:
        parser.error('--title必须与--titles一起使用')
    if args.hashtags is not None and args.body is None:
        parser.error('--hashtags必须与--body一起使用')
    if not re.fullmatch(r'[0-9]+', args.number):
        parser.error('number须为ASCII数字编号（0—9）')
    if not args.name.strip() or args.name != args.name.strip():
        parser.error('name不能为空或带有首尾空白')
    if args.title_count < 1:
        parser.error('title-count须为正整数')
    hashtags = None if args.hashtags is None else [tag.removeprefix('#') for tag in args.hashtags]
    if hashtags is not None and (len(set(hashtags)) != len(hashtags) or
                                any(not tag or re.search(r'[\s#]', tag) for tag in hashtags)):
        parser.error('hashtags须为不重复且不含空白的完整话题名称')
    try:
        # Keep each title's whitespace so malformed publishable text is not silently repaired.
        titles = ([s for s in args.titles.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
                  if args.titles is not None else None)
        result = check(args.number, args.name, titles,
                       args.body.read_text(encoding='utf-8-sig') if args.body is not None else None,
                       args.title.read_text(encoding='utf-8-sig') if args.title else None,
                       args.title_count, hashtags)
    except (OSError, UnicodeError) as exc:
        result = {'ok': False, 'errors': [f'无法读取UTF-8文案文件：{exc}'], 'warnings': []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
