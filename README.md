# yoonkiwoong.github.io

A minimal HTML-based blog repository containing all pages, styles, and written posts.

## Writing a post

Create a folder under `content/posts/` named after the date, and put a single Markdown file in it:

```
content/posts/2025-11-16/Hello, world!.md
```

The folder name becomes the URL (`/post/2025-11-16/`) and the file name becomes the title, so neither is repeated inside the file. Images placed in the same folder are copied next to the post. The published and updated dates shown on the page come from the folder's git history, not from its name.

Push to `main` and GitHub Actions builds the site and deploys it to GitHub Pages. To build locally, `pip install markdown` and run `python build.py`; the output goes to `public/`.
