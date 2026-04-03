import os
import re
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'therapist-pipeline', '.env'))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

def generate_slug(title):
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = slug.strip('-')
    return slug

def detect_category(title):
    title_lower = title.lower()
    
    if any(word in title_lower for word in ['billing', 'insurance', 'superbill']):
        return "Billing"
    elif any(word in title_lower for word in ['telehealth', 'hipaa', 'video', 'zoom', 'doxy']):
        return "Telehealth"
    elif any(word in title_lower for word in ['website', 'directory', 'psychology today', 'email', 'private practice', 'marketing']):
        return "Marketing"
    elif any(word in title_lower for word in ['accounting', 'tax', 'note-taking']):
        return "Finance"
    else:
        return "Practice Management"

def extract_title(content):
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""

def extract_description(content):
    match = re.search(r'^#\s+.+$\n\n(.+?)(?:\n\n|$)', content, re.MULTILINE | re.DOTALL)
    if match:
        text = match.group(1).strip()
        text = re.sub(r'[#*`]', '', text)
        return text[:150]
    return ""

def replace_affiliate_links(content):
    pattern = r'\[AFFILIATE_LINK_([^\]]+)\]'
    
    def replace_match(match):
        product_name = match.group(1)
        slug = product_name.lower().replace(' ', '-')
        return f'<a href="https://therapisttools.com/go/{slug}" class="affiliate-btn">Try {product_name} free →</a>'
    
    return re.sub(pattern, replace_match, content)

def add_frontmatter(content, title, description, category):
    frontmatter = f'''---
title: "{title}"
description: "{description}"
pubDate: 2025-01-15
category: "{category}"
tags: []
affiliate_products: []
---'''
    
    return frontmatter + '\n\n' + content

def main():
    g = Github(auth=Auth.Token(GITHUB_TOKEN))
    repo = g.get_repo(GITHUB_REPO)
    
    posts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'content', 'posts')
    os.makedirs(posts_dir, exist_ok=True)
    
    imported_count = 0
    
    for i in range(1, 31):
        folder_path = f"posts/post_{i}/draft.md"
        
        try:
            contents = repo.get_contents(folder_path)
            file_content = contents.decoded_content.decode('utf-8')
        except Exception as e:
            print(f"Could not fetch {folder_path}: {e}")
            continue
        
        title = extract_title(file_content)
        if not title:
            print(f"Could not extract title from {folder_path}")
            continue
        
        description = extract_description(file_content)
        category = detect_category(title)
        slug = generate_slug(title)
        
        processed_content = replace_affiliate_links(file_content)
        processed_content = add_frontmatter(processed_content, title, description, category)
        
        output_path = os.path.join(posts_dir, f"{slug}.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        print(f"Imported post {i}: {title} -> {slug}.md")
        imported_count += 1
    
    print(f"\nSuccessfully imported {imported_count} posts")

if __name__ == '__main__':
    main()
