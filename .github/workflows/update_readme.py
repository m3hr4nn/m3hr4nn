#!/usr/bin/env python3
# scripts/update_readme.py

import os
import glob
import re
from datetime import datetime
from pathlib import Path
import frontmatter

def extract_title_and_content(filepath):
    """Extract title and first few lines from markdown file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse frontmatter
        try:
            post = frontmatter.loads(content)
            title = post.metadata.get('title', '')
            body = post.content
            date = post.metadata.get('date', '')
        except:
            body = content
            title = ''
            date = ''
        
        # Extract title from first h1 if not in frontmatter
        if not title:
            title_match = re.search(r'^#\s+(.+)', body, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
            else:
                # Use filename as title
                title = Path(filepath).stem.replace('-', ' ').replace('_', ' ').title()
        
        # Get first 2-3 lines of actual content (skip title and empty lines)
        lines = body.split('\n')
        content_lines = []
        skip_title = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#') and not skip_title:
                skip_title = True
                continue
            if line and not line.startswith('#'):
                content_lines.append(line)
                if len(content_lines) >= 3:
                    break
        
        preview = ' '.join(content_lines[:3])
        if len(preview) > 150:
            preview = preview[:147] + '...'
        
        # Get file modification date if no date in frontmatter
        if not date:
            mtime = os.path.getmtime(filepath)
            date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
        
        return title, preview, date
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None, None, None

def get_all_md_files():
    """Get all .md files in subdirectories, excluding README.md"""
    md_files = []
    
    # Find all .md files in subdirectories
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and root directory
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        if root == '.':
            continue
            
        for file in files:
            if file.endswith('.md') and file.lower() != 'readme.md':
                filepath = os.path.join(root, file)
                md_files.append(filepath)
    
    return md_files

def generate_readme_content():
    """Generate the README.md content"""
    md_files = get_all_md_files()
    
    # Process files and sort by date (newest first)
    entries = []
    for filepath in md_files:
        title, preview, date = extract_title_and_content(filepath)
        if title and preview:
            # Create GitHub URL
            github_url = f"https://github.com/m3hr4nn/TIL/blob/main/{filepath.replace(os.sep, '/')}"
            
            entries.append({
                'title': title,
                'preview': preview,
                'date': date,
                'filepath': filepath,
                'github_url': github_url
            })
    
    # Sort by date (newest first)
    entries.sort(key=lambda x: x['date'], reverse=True)
    
    # Generate README content
    readme_content = """# Today I Learned (TIL)

> A collection of things I learn every day across a variety of languages and technologies.

## Recent Entries

"""
    
    for entry in entries:
        readme_content += f"### {entry['date']} - {entry['title']}\n\n"
        readme_content += f"{entry['preview']}\n\n"
        readme_content += f"[**See more...**]({entry['github_url']})\n\n"
        readme_content += "---\n\n"
    
    # Add footer
    readme_content += f"""
## Stats

- **Total entries:** {len(entries)}
- **Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

_This README is automatically generated from the markdown files in this repository._
"""
    
    return readme_content

def main():
    """Main function to update README.md"""
    print("Updating README.md...")
    
    # Create scripts directory if it doesn't exist
    os.makedirs('scripts', exist_ok=True)
    
    # Generate new README content
    readme_content = generate_readme_content()
    
    # Write to README.md
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("README.md updated successfully!")

if __name__ == "__main__":
    main()
