# 任务与渲染清单

任务放在skill目录外。建议保存：
- brief.json：参考文件、身份约束、主题、数量、语言、协作方式、实际生成工具和已批准事项。
- plan.json：每条的编号、文案、使用场景、主动作、道具、关键过程、循环方式和修订号。
- sources/：原图、生成姿势及对应提示词。
- render.json：仅列本轮要导出的条目。
- output-vNN/：每轮新建，包含导出和验收材料。

render.json示例，路径相对于清单所在目录；字体可以使用本机绝对路径，脚本不会打包该路径或字体：
```json
{
  "size": 512,
  "background": "white",
  "show_text": true,
  "font": "/path/to/chinese-rounded-bold.ttf",
  "font_size": 56,
  "stroke_width": 4,
  "caption_color": "#20242a",
  "resampling": "smooth",
  "alpha_threshold": 128,
  "count": 1,
  "items": [{
    "id": "01",
    "caption": "收到收到",
    "frames": ["sources/01/a.png", "sources/01/b.png", "sources/01/c.png"],
    "durations_ms": [200, 100, 300]
  }]
}
```

- size为正方形边长，64–2048。background为white或transparent；轻场景应已包含在源帧中，使用white输出。
- show_text默认true；整套设false关闭画面文字，单条items可覆盖该值。无字版不预留顶部字区，也不要求font字段；caption仍保留作内部含义与文件标签。浏览页的导航标签不会绘入GIF。源帧本身若含字，此开关不会擦除它。
- 每条至少2帧，所有帧尺寸相同，且应具有可观察的角色动作；技术上的不同像素不是语义动作证明。
- durations_ms必须与帧一一对应，20–10000ms、10ms整数倍，避免悄悄截断GIF时长；这些是编码约束，不是创作推荐值。
- id为短英数字、下划线或连字符，编号与文案不能重复。默认文案2–6字；明确要求较长文案时，在该条加入allow_long_caption:true。1字文案也须该例外标记。
- resampling为smooth或pixel。pixel使用最近邻采样；像素风仍需检查最终像素网格。
- transparent采用alpha_threshold二值化透明，不将预览棋盘格当Alpha。原图没有透明时不会凭空抠图。
- 任何条目开启文字时，字体文件必须可读且由代理检查中文字形。自动缩小字号不是中文字体可用性的验证。
- font_embolden可设为true，为细圆体加一像素同色描边；stroke_width大于1时生效，外层仍保留白描边。默认关闭。
- count为本轮导出数；追加与修复可只列新条目。整套交付时再核对用户要求的总数。

一条动作的帧应使用相同画布坐标。合成器将整张帧以共享比例放进字幕下方或无字版全画布安全区，保留动作造成的位置变化，不根据每帧主体大小单独裁切归一。
