import re
import shutil
import markdown
from pathlib import Path
from itertools import groupby

CONTENT_DIRECTORY = Path("content")
POSTS_DIRECTORY = Path("content/posts")
TEMPLATE_DIRECTORY = Path("templates")
STATIC_DIRECTORY = Path("static")
PUBLIC_DIRECTORY = Path("public")


# Utility (File System): Clear and recreate a directory
def initialize_directory(path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


# Utility (File System): Write content to a file, creating directories if needed
def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


# Utility (File System): Read content from a file
def read_file(path):
    return path.read_text(encoding='utf-8')


# Utility (File System): Copy static files to the public directory
def copy_static_files():
    if STATIC_DIRECTORY.exists():
        shutil.copytree(STATIC_DIRECTORY, PUBLIC_DIRECTORY / "static")


# Utility (File System): Copy image assets from source to target directory
def copy_assets(source_directory, target_directory):
    for image_file in source_directory.glob("*.[jp][pn]g"):
        shutil.copy(image_file, target_directory)


# Utility (Content Processing): Generate a URL-friendly slug from text
def generate_url_slug(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')


# Utility (Content Processing): Add an ID anchor to a heading tag
def add_anchor_to_heading(match):
    tag, text = match.groups()
    slug = generate_url_slug(text)
    return f'<{tag} id="{slug}">{text}</{tag}>'


# Utility (Content Processing): Convert Markdown text to HTML with anchors
def convert_markdown_to_html(raw_text):
    html = markdown.markdown(raw_text, extensions=['fenced_code'])
    return re.sub(r'<(h[23])>(.*?)</\1>', add_anchor_to_heading, html)


# Utility (Content Processing): Render a template with context data
def render_template(template_name, context):
    template = read_file(TEMPLATE_DIRECTORY / template_name)
    for key, value in context.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template


# Utility (Content Processing): Render a post to HTML
def render_post(post, previous_post=None, next_post=None):
    post_navigation = '<nav class="post-nav" aria-label="Post navigation">'
    
    previous_link = ''
    previous_title = ''
    next_link = ''
    next_title = ''
    
    if previous_post:
        previous_link = f'<a href="/{previous_post["url"]}" rel="prev">← Previous</a>'
        previous_title = previous_post["title"]
    
    if next_post:
        next_link = f'<a href="/{next_post["url"]}" rel="next">Next →</a>'
        next_title = next_post["title"]
    
    post_navigation += f'<div>{previous_link}</div>'
    post_navigation += f'<div>{next_link}</div>'
    post_navigation += f'<div>{previous_title}</div>'
    post_navigation += f'<div>{next_title}</div>'
    post_navigation += '</nav>'

    post_body = convert_markdown_to_html(read_file(post["path"]))

    post_data = {
        "{title}": post["title"],
        "{content}": post_body,
        "{date}": post["date"],
        "{post_nav}": post_navigation
    }

    post_template = read_file(TEMPLATE_DIRECTORY / "post.html")
    post_content = post_template
    for placeholder, value in post_data.items():
        post_content = post_content.replace(placeholder, value)

    return render_template("layout.html", {
        "title": f"{post['title']} | YOONKIWOONG",
        "content": post_content,
        "url": f"https://yoonkiwoong.github.io/{post['url']}",
        "canonical_url": f"https://yoonkiwoong.github.io/{post['url']}"
    })


# Utility (Date Helpers): Get the date from a post dictionary
def get_post_date(post):
    return post["date"]


# Utility (Date Helpers): Get the year from a post dictionary
def get_post_year(post):
    return post["date"][:4]


def generate_pages():
    for page_file in CONTENT_DIRECTORY.rglob("*.md"):
        if POSTS_DIRECTORY in page_file.parents:
            continue

        page_html = render_template("layout.html", {
            "title": f"{page_file.stem.title()} | YOONKIWOONG",
            "content": convert_markdown_to_html(read_file(page_file)),
            "url": f"https://yoonkiwoong.github.io/{page_file.stem}/",
            "canonical_url": f"https://yoonkiwoong.github.io/{page_file.stem}/"
        })
        output_directory = PUBLIC_DIRECTORY / page_file.stem
        output_directory.mkdir(parents=True, exist_ok=True)

        copy_assets(page_file.parent, output_directory)

        write_file(output_directory / "index.html", page_html)


def collect_posts():
    posts = []
    for post_file in POSTS_DIRECTORY.rglob("*.md"):
        post_date = post_file.parent.name
        posts.append({
            "title": post_file.stem,
            "date": post_date,
            "url": f"post/{post_date}/",
            "path": post_file
        })
    return sorted(posts, key=get_post_date, reverse=True)


def generate_posts(posts):
    for index, post in enumerate(posts):
        next_post = posts[index - 1] if index > 0 else None
        previous_post = posts[index + 1] if index < len(posts) - 1 else None

        post_html = render_post(post, previous_post, next_post)

        post_directory = PUBLIC_DIRECTORY / post["url"]
        write_file(post_directory / "index.html", post_html)

        copy_assets(post["path"].parent, post_directory)


def generate_index(posts):
    if not posts:
        return

    latest_post = posts[0]
    previous_post = posts[1] if len(posts) > 1 else None

    index_html = render_post(latest_post, previous_post=previous_post, next_post=None)

    write_file(PUBLIC_DIRECTORY / "index.html", index_html)

    copy_assets(latest_post["path"].parent, PUBLIC_DIRECTORY)


def generate_archive(posts):
    archive_content = "<h1>Archive</h1>"

    for year, group in groupby(posts, key=get_post_year):
        archive_content += f"<h2>{year}</h2><ul>"
        for post in group:
            archive_content += f'<li><a href="/{post["url"]}">{post["title"]}</a> | <small>{post["date"]}</small></li>'
        archive_content += "</ul>"

    archive_html = render_template("layout.html", {
        "title": "Archive | YOONKIWOONG",
        "content": archive_content,
        "url": "https://yoonkiwoong.github.io/archive/",
        "canonical_url": "https://yoonkiwoong.github.io/archive/"
    })
    write_file(PUBLIC_DIRECTORY / "archive" / "index.html", archive_html)


def main():
    initialize_directory(PUBLIC_DIRECTORY)
    copy_static_files()

    generate_pages()

    posts = collect_posts()

    generate_posts(posts)
    generate_index(posts)
    generate_archive(posts)

    print("Build Complete")


if __name__ == "__main__":
    main()
