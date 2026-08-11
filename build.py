import html
import re
import shutil
import subprocess
import markdown
from pathlib import Path
from datetime import datetime
from itertools import groupby

CONTENT_DIRECTORY = Path("content")
POSTS_DIRECTORY = Path("content/posts")
TEMPLATE_DIRECTORY = Path("templates")
STATIC_DIRECTORY = Path("static")
PUBLIC_DIRECTORY = Path("public")

# Language declared per document as `<!-- lang: ko -->`; unmarked documents fall back to SITE_LANGUAGE
SITE_LANGUAGE = "ko"
LANGUAGE_PATTERN = re.compile(r'<!--\s*lang:\s*(en|ko)\s*-->\s*')


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


# Utility (Content Processing): Convert Markdown text to HTML with optional anchors
def convert_markdown_to_html(raw_text, add_anchors=True):
    converted_html = markdown.markdown(raw_text, extensions=['fenced_code'])
    if add_anchors:
        return re.sub(r'<(h[23])>(.*?)</\1>', add_anchor_to_heading, converted_html)
    return converted_html


# Utility (Content Processing): Read the declared language and strip its marker
def extract_language(raw_text):
    match = LANGUAGE_PATTERN.search(raw_text)
    language = match.group(1) if match else SITE_LANGUAGE
    return language, LANGUAGE_PATTERN.sub('', raw_text, count=1)


# Utility (Content Processing): Render a template with context data
def render_template(template_name, context):
    template = read_file(TEMPLATE_DIRECTORY / template_name)
    for key, value in context.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template


# Utility (Content Processing): Extract first <p> tag content from HTML
def extract_first_paragraph(content_html):
    match = re.search(r'<p>(.*?)</p>', content_html, re.DOTALL)
    if match:
        # Remove HTML tags from paragraph content
        text = re.sub(r'<[^>]+>', '', match.group(1))
        # Decode entities so the result is plain text, escaped again at the output boundary
        text = html.unescape(text)
        # Replace newlines and multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    return ""


# Utility (Content Processing): Generate description and OG tags HTML
def generate_meta_tags(title, description, image_url, url, page_type="website"):
    title = html.escape(title)
    description = html.escape(description)
    return f'''<meta name="description" content="{description}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:url" content="{url}">
    <meta property="og:type" content="{page_type}">'''


# Utility (Content Processing): Render a post to HTML
def render_post(post, previous_post=None, next_post=None, published_date=None, updated_date=None):
    post_navigation = '<nav class="post-nav" aria-label="Post navigation">'

    if previous_post:
        post_navigation += (
            f'<a class="post-nav-prev" href="/{previous_post["url"]}" rel="prev">'
            f'<span class="post-nav-label">← Previous</span>'
            f'<span class="post-nav-title">{html.escape(previous_post["title"])}</span></a>'
        )

    if next_post:
        post_navigation += (
            f'<a class="post-nav-next" href="/{next_post["url"]}" rel="next">'
            f'<span class="post-nav-label">Next →</span>'
            f'<span class="post-nav-title">{html.escape(next_post["title"])}</span></a>'
        )

    post_navigation += '</nav>'

    language, raw_body = extract_language(read_file(post["path"]))
    post_body = convert_markdown_to_html(raw_body)
    escaped_title = html.escape(post["title"])

    post_data = {
        "{title}": escaped_title,
        "{content}": post_body,
        "{date}": post["date"],
        "{published_date}": published_date or "",
        "{updated_date}": updated_date or "",
        "{post_nav}": post_navigation
    }

    post_template = read_file(TEMPLATE_DIRECTORY / "post.html")
    post_content = post_template
    for placeholder, value in post_data.items():
        post_content = post_content.replace(placeholder, value)

    # Generate meta tags for post
    description = extract_first_paragraph(post_body) or post["title"]
    meta_tags = generate_meta_tags(
        title=f"{post['title']} | YOONKIWOONG",
        description=description,
        image_url="https://yoonkiwoong.github.io/static/og-image.jpg",
        url=f"https://yoonkiwoong.github.io/{post['url']}",
        page_type="article"
    )

    return render_template("common.html", {
        "lang": language,
        "title": f"{escaped_title} | YOONKIWOONG",
        "content": post_content,
        "meta_tags": meta_tags,
        "canonical_url": f"https://yoonkiwoong.github.io/{post['url']}"
    })


# Utility (Git): Get the first commit date of a file (published)
def get_published_date(file_path):
    try:
        published_result = subprocess.run(
            ['git', 'log', '--follow', '--format=%aI', '--reverse', str(file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        published_date_iso = published_result.stdout.strip().split('\n')[0]
        published_date = datetime.fromisoformat(published_date_iso).strftime('%Y-%m-%d')
        return published_date
    except (subprocess.CalledProcessError, ValueError):
        return None


# Utility (Git): Get the last modified date of a file (updated)
def get_updated_date(file_path):
    try:
        updated_result = subprocess.run(
            ['git', 'log', '-1', '--format=%aI', str(file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        updated_date_iso = updated_result.stdout.strip()
        updated_date = datetime.fromisoformat(updated_date_iso).strftime('%Y-%m-%d')
        return updated_date
    except (subprocess.CalledProcessError, ValueError):
        return None


# Utility (Date Helpers): Get the date from a post dictionary
def get_post_date(post):
    return post["published_date"]


# Utility (Date Helpers): Get the year from a post dictionary
def get_post_year(post):
    return post["published_date"][:4]


def generate_about():
    about_file = CONTENT_DIRECTORY / "about" / "about.md"
    if not about_file.exists():
        return

    language, raw_body = extract_language(read_file(about_file))
    content_html = convert_markdown_to_html(raw_body, add_anchors=False)
    description = extract_first_paragraph(content_html) or "About YOONKIWOONG"

    meta_tags = generate_meta_tags(
        title="About | YOONKIWOONG",
        description=description,
        image_url="https://yoonkiwoong.github.io/static/og-image.jpg",
        url="https://yoonkiwoong.github.io/about/"
    )

    page_html = render_template("common.html", {
        "lang": language,
        "title": "About | YOONKIWOONG",
        "content": content_html,
        "meta_tags": meta_tags,
        "canonical_url": "https://yoonkiwoong.github.io/about/"
    })

    output_directory = PUBLIC_DIRECTORY / "about"
    output_directory.mkdir(parents=True, exist_ok=True)
    copy_assets(about_file.parent, output_directory)
    write_file(output_directory / "index.html", page_html)


def collect_posts():
    posts = []
    for post_file in POSTS_DIRECTORY.rglob("*.md"):
        post_date = post_file.parent.name
        # Files without git history (new posts before first commit) fall back to the folder-name date
        published_date = get_published_date(post_file) or post_date
        updated_date = get_updated_date(post_file)
        
        posts.append({
            "title": post_file.stem,
            "date": post_date,
            "published_date": published_date,
            "updated_date": updated_date,
            "url": f"post/{post_date}/",
            "path": post_file
        })
    return sorted(posts, key=get_post_date, reverse=True)


def generate_posts(posts):
    for index, post in enumerate(posts):
        next_post = posts[index - 1] if index > 0 else None
        previous_post = posts[index + 1] if index < len(posts) - 1 else None

        post_html = render_post(post, previous_post, next_post, 
                                post["published_date"], post["updated_date"])

        post_directory = PUBLIC_DIRECTORY / post["url"]
        write_file(post_directory / "index.html", post_html)

        copy_assets(post["path"].parent, post_directory)


def generate_index(posts):
    if not posts:
        return

    latest_post = posts[0]
    previous_post = posts[1] if len(posts) > 1 else None

    index_html = render_post(latest_post, previous_post=previous_post, next_post=None,
                             published_date=latest_post["published_date"],
                             updated_date=latest_post["updated_date"])

    write_file(PUBLIC_DIRECTORY / "index.html", index_html)

    copy_assets(latest_post["path"].parent, PUBLIC_DIRECTORY)


def generate_archive(posts):
    archive_content = "<h1>Archive</h1>"

    for year, group in groupby(posts, key=get_post_year):
        archive_content += f"<h2>{year}</h2><ul>"
        for post in group:
            archive_content += f'<li><a href="/{post["url"]}">{html.escape(post["title"])}</a> | <small>{post["published_date"]}</small></li>'
        archive_content += "</ul>"

    meta_tags = generate_meta_tags(
        title="Archive | YOONKIWOONG",
        description="Archive of all posts by YOONKIWOONG",
        image_url="https://yoonkiwoong.github.io/static/og-image.jpg",
        url="https://yoonkiwoong.github.io/archive/"
    )

    archive_html = render_template("common.html", {
        "lang": SITE_LANGUAGE,
        "title": "Archive | YOONKIWOONG",
        "content": archive_content,
        "meta_tags": meta_tags,
        "canonical_url": "https://yoonkiwoong.github.io/archive/"
    })
    write_file(PUBLIC_DIRECTORY / "archive" / "index.html", archive_html)


def main():
    initialize_directory(PUBLIC_DIRECTORY)
    copy_static_files()

    # 1. Build about page
    generate_about()

    # 2. Build archive page
    posts = collect_posts()
    generate_archive(posts)

    # 3. Build post pages
    generate_posts(posts)
    generate_index(posts)

    print("Build Complete")


if __name__ == "__main__":
    main()
