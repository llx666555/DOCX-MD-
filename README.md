# docx2md

  把 DOCX 文件转成 Markdown，主要用来**省 token**——Word 里的字号、颜色、行距、缩进对大模型全是噪声，转成 Markdown 后结构保留、体积砍掉大半，喂给大模型能省下一大截 token。

  ## 使用方式

  下载 `dist/docx2md.exe`，三种用法：

  1. **双击打开** — 按提示输入或拖入文件路径
  2. **拖到 exe 图标上** — 自动转换，结果输出到同目录 `output/` 下
  3. **命令行**：
     docx2md.exe 文件.docx
     docx2md.exe 文件夹
     docx2md.exe 文件夹 -o 输出目录
     docx2md.exe 文件夹 -r          # 递归子目录

  ## 输出格式

  output/
  ├── 文件名.md
  └── images/
      └── 文件名/
          └── 图片.png

  - Markdown 保留标题、加粗、列表、表格、链接等结构
  - 图片自动抽到 `images/` 子目录，文中用相对路径引用

  ## 技术原理

  DOCX → mammoth → HTML → markdownify → Markdown

  - **mammoth**：只提取语义（标题、列表、表格），忽略字号颜色等视觉样式
  - **markdownify**：把 HTML 标签转成 Markdown 语法

  ## 从源码运行（需要 Python）

  ```bash
  pip install mammoth markdownify
  python docx2md.py 文件.docx

  自行打包 exe

  pip install pyinstaller
  pyinstaller --onefile --name "docx2md" docx2md.py

  产物在 dist/docx2md.exe。
