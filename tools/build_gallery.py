"""Build the demo showroom from existing GIFs without changing their pixels."""
import argparse
import hashlib
import html
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD = 'https://github.com/Jensen-02/onepic-gif-stickers/releases/download/v0.3.0-preview/onepic-gif-demos-46.zip'


def image_table(items, prefix):
    rows = []
    for start in range(0, len(items), 4):
        cells = []
        for item in items[start:start + 4]:
            url = html.escape(prefix + item['file'], quote=True)
            caption = html.escape(item['caption'])
            cells.append(f'<td align="center"><a href="{url}"><img src="{url}" width="180" alt="{caption}"></a><br>{caption}</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    return '<table>\n' + '\n'.join(rows) + '\n</table>'


def markdown(data, prefix):
    lookup = {(pack['id'], item['id']): item for pack in data['packs'] for item in pack['items']}
    featured = [lookup[tuple(key)] for key in data['featured']]
    parts = [
        '## 表情包展厅', '',
        f"这里收录 **{len(data['packs'])} 个系列、{data['count']} 张 GIF**。点击动图查看原尺寸，各系列默认收起，点标题即可展开。", '',
        f'[下载全部 {data["count"]} 张示例]({DOWNLOAD}) · ZIP 内附离线展厅，解压后打开 `index.html`。', '',
        '### 精选动态预览', '', image_table(featured, prefix), '',
        '▲ 同一张主图可以换画风，每张表情包的动作则跟着文案走。', ''
    ]
    for pack in data['packs']:
        parts += [
            '<details>', f'<summary><strong>{html.escape(pack["title"])} · {len(pack["items"])} 张 · 点击展开</strong></summary>', '',
            image_table(pack['items'], prefix), '', '</details>', ''
        ]
    return '\n'.join(parts)


def offline_html(data, prefix):
    def cards(items):
        result = []
        for item in items:
            url = html.escape(prefix + item['file'], quote=True)
            caption = html.escape(item['caption'])
            result.append(f'<a class="card" href="{url}" target="_blank" rel="noopener"><img loading="lazy" src="{url}" alt="{caption}"><span>{caption}</span></a>')
        return '<div class="grid">' + ''.join(result) + '</div>'
    lookup = {(pack['id'], item['id']): item for pack in data['packs'] for item in pack['items']}
    featured = cards([lookup[tuple(key)] for key in data['featured']])
    sections = ''.join(f'<details><summary>{html.escape(p["title"])}<small>{len(p["items"])} 张</small></summary>{cards(p["items"])}</details>' for p in data['packs'])
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>一图成套 · 表情包展厅</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f4f6f8;color:#202631;font-family:system-ui,"Microsoft YaHei",sans-serif}}main{{max-width:1060px;margin:auto;padding:48px 24px}}.eyebrow{{font-size:13px;color:#536d84;letter-spacing:2px}}h1{{font-size:36px;margin:12px 0}}p{{color:#5a6473;line-height:1.8}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}}.card{{display:block;background:white;border:1px solid #e6eaf0;border-radius:16px;padding:12px;text-align:center;color:inherit;text-decoration:none}}.card:hover{{border-color:#7c9bbe}}.card img{{display:block;width:100%;aspect-ratio:1;object-fit:contain;border-radius:10px}}.card span{{display:block;padding:12px 0 4px;font-weight:600}}details{{margin-top:16px;background:#fff;border:1px solid #e0e5eb;border-radius:16px;padding:20px}}summary{{cursor:pointer;font-size:19px;font-weight:650}}summary small{{float:right;color:#75808e}}details .grid{{margin-top:20px}}h2{{margin-top:32px;font-size:22px}}.download{{display:inline-block;padding:11px 18px;background:#233f5d;color:white;border-radius:10px;text-decoration:none}}footer{{padding-top:32px;font-size:13px;color:#697687}}@media(max-width:700px){{.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}h1{{font-size:28px}}main{{padding:28px 16px}}}}
</style></head><body><main><div class="eyebrow">ONEPIC GIF STICKERS</div><h1>一图成套 · 表情包展厅</h1><p>{len(data['packs'])} 个系列 · {data['count']} 张 GIF。点击动图查看原尺寸，点系列标题展开全部。</p><a class="download" href="{DOWNLOAD}">下载全部示例</a><h2>精选动态预览</h2>{featured}<h2>全部系列</h2>{sections}<footer>椰子的AI小岛 · <a href="https://github.com/Jensen-02/onepic-gif-stickers">项目主页</a></footer></main></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, help='Optional offline demo ZIP path')
    args = parser.parse_args()
    data = json.loads((ROOT / 'docs/gallery.json').read_text(encoding='utf-8'))
    items = [i for p in data['packs'] for i in p['items']]
    assert data['count'] == len(items)
    assert len({i['sha256'] for i in items}) == len(items)
    for item in items:
        file = (ROOT / item['file']).resolve()
        assert file.is_relative_to(ROOT) and file.suffix == '.gif'
        assert hashlib.sha256(file.read_bytes()).hexdigest() == item['sha256']
    readme = ROOT / 'README.md'
    text = readme.read_text(encoding='utf-8')
    marker = '## 表情包展厅' if '## 表情包展厅' in text else '## 试作示例'
    start, end = text.index(marker), text.index('## 能做什么')
    readme.write_text(text[:start] + markdown(data, '') + '\n' + text[end:], encoding='utf-8')
    (ROOT / 'docs/gallery.md').write_text('# 一图成套\n\n[返回首页](../README.md)\n\n' + markdown(data, '../'), encoding='utf-8')
    (ROOT / 'docs/gallery.html').write_text(offline_html(data, '../'), encoding='utf-8')
    if args.zip:
        args.zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.zip, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('index.html', offline_html(data, ''))
            archive.write(ROOT / 'LICENSE', 'LICENSE')
            archive.write(ROOT / 'docs/gallery.json', 'gallery.json')
            for item in items:
                archive.write(ROOT / item['file'], item['file'])
        with zipfile.ZipFile(args.zip) as archive:
            assert archive.testzip() is None
            assert len([name for name in archive.namelist() if name.endswith('.gif')]) == data['count']
        checksum = hashlib.sha256(args.zip.read_bytes()).hexdigest()
        args.zip.with_suffix('.sha256').write_text(checksum + '  ' + args.zip.name + '\n', encoding='utf-8')
    print(f"Built showroom: {len(data['packs'])} series, {data['count']} unique GIFs")


if __name__ == '__main__':
    main()
