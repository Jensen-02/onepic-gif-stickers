"""Build the public action reference from the skill's topic files."""
import argparse
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / 'skills/onepic-gif-stickers/references'
INDEX = REFERENCES / 'action-library.md'
OUTPUT = ROOT / 'docs/actions.md'
TOPIC_PATTERN = re.compile(
    r'^\| \[([^\]]+)\]\((actions/[^)]+\.md)\) \| (\d+) \| '
    r'(A\d+)–(A\d+) \| (.+) \|$', re.MULTILINE
)


def render():
    index = INDEX.read_text(encoding='utf-8-sig')
    topics = TOPIC_PATTERN.findall(index)
    if not topics:
        raise ValueError('No topics found in action-library.md')
    sections, ids, actions, profiles = [], [], [], []
    for title, relative, count, first, last, _ in topics:
        source = (REFERENCES / relative).resolve()
        if not source.is_relative_to(REFERENCES.resolve()):
            raise ValueError(f'Topic outside references: {relative}')
        content = source.read_text(encoding='utf-8').strip()
        heading, body = content.split('\n', 1)
        if heading != '# ' + title:
            raise ValueError(f'Topic title mismatch: {relative}')
        rows = [line for line in content.splitlines() if re.match(r'^\| A\d+ \|', line)]
        topic_ids = []
        for row in rows:
            cells = [cell.strip() for cell in row.strip('|').split('|')]
            if len(cells) != 5 or not all(cells) or cells[2] not in ('轻', '大'):
                raise ValueError(f'Invalid action row in {relative}: {row}')
            topic_ids.append(cells[0])
            actions.append(cells[3])
            profiles.append(cells[2])
        if len(rows) != int(count) or not topic_ids or (topic_ids[0], topic_ids[-1]) != (first, last):
            raise ValueError(f'Topic count or ID range mismatch: {relative}')
        ids.extend(topic_ids)
        sections.append(
            '<details>\n'
            f'<summary><strong>{html.escape(title)} · {count} 个 · {first}–{last} · 点击展开</strong></summary>\n\n'
            + body.strip() + '\n\n</details>'
        )
    if len(set(actions)) != len(actions):
        raise ValueError('Duplicate action descriptions')
    if ids != [f'A{number:03d}' for number in range(1, len(ids) + 1)]:
        raise ValueError('Missing, duplicate or out-of-order action IDs')
    if f'共 **{len(ids)} 个动作灵感，{len(topics)} 个主题**' not in index:
        raise ValueError('Index total does not match topic files')

    # 主题文件是唯一动作正文来源，网页不另维护一份动作内容。
    intro = index.split('## 按需使用')[0]
    intro = intro.replace('# 动作参考库\n', '# 动作参考库\n\n[返回首页](../README.md) · [画风参考](styles.md)\n', 1)
    adaptation = '## 画风与动作分开设计' + index.split('## 画风与动作分开设计', 1)[1]
    adaptation = adaptation.replace('(style-library.md)', '(styles.md)')
    for reference in ('creative.md', 'quality.md'):
        adaptation = adaptation.replace(f'({reference})', f'(../skills/onepic-gif-stickers/references/{reference})')
    help_text = (
        '各主题默认收起，点击标题展开。每条提供聊天含义、文案例子、轻／大动效、角色动作与循环思路。'
        '这些只是设计起点，可以换道具、改幅度或另创动作，不必按编号选取。\n\n'
        '轻动效也需要完整过渡；大动效也要安排起势、重心与收势。循环建议需结合实际生成结果检查。'
    )
    document = intro.rstrip() + '\n\n' + help_text + '\n\n' + '\n\n'.join(sections) + '\n\n' + adaptation.strip() + '\n'
    print(f'Action library: {len(topics)} themes, {len(ids)} actions, light={profiles.count("轻")}, large={profiles.count("大")}')
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check that the published Markdown is up to date')
    args = parser.parse_args()
    document = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != document:
            raise SystemExit('docs/actions.md is out of date; run tools/build_action_library.py')
    else:
        OUTPUT.write_text(document, encoding='utf-8')


if __name__ == '__main__':
    main()
