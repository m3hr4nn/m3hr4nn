#!/usr/bin/env python3
import os
import json
import markdown
import frontmatter
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

def get_git_info(file_path):
    """Get git commit info for a file"""
    try:
        import subprocess
        # Get last commit date for the file
        result = subprocess.run([
            'git', 'log', '-1', '--format=%ci', '--', file_path
        ], capture_output=True, text=True, cwd='til-content')
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return datetime.now().isoformat()
    except:
        return datetime.now().isoformat()

def extract_metadata(content):
    """Extract metadata from markdown content"""
    try:
        post = frontmatter.loads(content)
        return post.metadata, post.content
    except:
        # If no frontmatter, create basic metadata
        lines = content.split('\n')
        title = lines[0].replace('#', '').strip() if lines and lines[0].startswith('#') else 'Untitled'
        return {'title': title}, content

def process_markdown(content):
    """Process markdown content and extract useful info"""
    md = markdown.Markdown(extensions=['codehilite', 'tables', 'toc'])
    html = md.convert(content)
    
    # Extract first paragraph as description
    description = re.search(r'<p>(.*?)</p>', html)
    description = description.group(1) if description else ''
    
    # Clean HTML tags for description
    description = re.sub(r'<[^>]+>', '', description)
    
    return {
        'html': html,
        'description': description[:200] + '...' if len(description) > 200 else description
    }

def categorize_content(file_path):
    """Categorize content based on directory structure"""
    path_parts = Path(file_path).parts
    if len(path_parts) > 1:
        return path_parts[1]  # First subdirectory as category
    return 'general'

def process_til_content():
    """Main function to process TIL content"""
    til_dir = Path('til-content')
    output_file = Path('data/til-posts.json')
    stats_file = Path('data/til-stats.json')
    
    if not til_dir.exists():
        print("TIL directory not found!")
        return
    
    posts = []
    categories = defaultdict(int)
    total_posts = 0
    
    # Process all markdown files
    for md_file in til_dir.rglob('*.md'):
        if md_file.name.lower() == 'readme.md':
            continue
            
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip empty files
            if not content.strip():
                continue
                
            metadata, clean_content = extract_metadata(content)
            processed = process_markdown(clean_content)
            
            # Get relative path from til-content directory
            relative_path = md_file.relative_to(til_dir)
            category = categorize_content(relative_path)
            
            post = {
                'title': metadata.get('title', md_file.stem.replace('-', ' ').title()),
                'slug': md_file.stem,
                'category': category,
                'description': processed['description'],
                'content': clean_content,
                'html': processed['html'],
                'file_path': str(relative_path),
                'url': f"https://github.com/m3hr4nn/TIL/blob/main/{relative_path}",
                'last_modified': get_git_info(str(md_file)),
                'metadata': metadata,
                'word_count': len(clean_content.split()),
                'reading_time': max(1, len(clean_content.split()) // 200) 
            }
            
            posts.append(post)
            categories[category] += 1
            total_posts += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
            continue
    
    # Sort posts by last modified date (newest first)
    posts.sort(key=lambda x: x['last_modified'], reverse=True)
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save posts data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    
    # Save statistics
    stats = {
        'total_posts': total_posts,
        'categories': dict(categories),
        'last_updated': datetime.now().isoformat(),
        'recent_posts': posts[:5]  # Last 5 posts for quick access
    }
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {total_posts} posts across {len(categories)} categories")
    print(f"Categories: {dict(categories)}")

if __name__ == "__main__":
    process_til_content()
