#!/usr/bin/env python3
"""
Phrase Explainer - Creates phrase explanation markdown files
Usage: python business.py <number_of_phrases>
Example: python business.py 3
"""

import sys
import os
import re
from llm import get_llm


PHRASES_FILE = "pending_phrases.txt"
DONE_FILE = "done_phrases.txt"


def sanitize_filename(phrase):
    """Convert phrase to valid filename format"""
    name = re.sub(r'[^\w\s-]', '', phrase.lower())
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')


def load_phrases(filepath):
    """Load phrases from file, return list of non-empty lines"""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def save_lines(filepath, lines):
    """Write lines to a file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(f"{line}\n")


def get_next_index():
    """Get the next available index number by checking existing files"""
    import glob

    existing_files = glob.glob('[0-9][0-9][0-9]-*.md')
    if not existing_files:
        return 1

    indices = []
    for filename in existing_files:
        match = re.match(r'^(\d{3})-', filename)
        if match:
            indices.append(int(match.group(1)))

    return max(indices) + 1 if indices else 1


def update_index(created_files, phrases):
    """Append newly created phrase files to index.md"""
    index_file = "index.md"

    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = "# Phrase Wiki\n\nAll of our Phrase collection will be coming here\n\n## Phrases :\n\n"

    new_entries = ""
    for filename, phrase in zip(created_files, phrases):
        link = f"  * [{phrase}]({filename})"
        if link not in content:
            new_entries += f"{link}\n"

    if new_entries:
        content = content.rstrip() + "\n" + new_entries + "\n"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📚 Updated index.md with {len(created_files)} new entry(ies)")


def generate_explanation(llm, phrase):
    """Generate a phrase explanation using LLM"""

    prompt = f"""Explain the phrase "{phrase}" in detail using this EXACT markdown format.
Do NOT include any text before or after the markdown. Output ONLY the markdown.

/ [Home](index.md)

## "{phrase}" [relevant emoji]

**Meaning:** [One or two sentence meaning of the phrase]

---

### Origin
[Brief origin/history of the phrase in 2-3 sentences]

---

### Real-Time Example

[Write a vivid, relatable real-time scenario (3-5 sentences) where someone would use this phrase.
Make it modern, practical, and engaging. Include a quoted usage of the phrase in context using blockquote format.]

---

### Other Everyday Contexts

| Situation | Usage |
|---|---|
| [Situation 1] | *"[Usage with the phrase]"* |
| [Situation 2] | *"[Usage with the phrase]"* |
| [Situation 3] | *"[Usage with the phrase]"* |

---

**In short:** [One punchy sentence summarizing the phrase]
"""

    try:
        print(f"📝 Generating explanation for: {phrase}")
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"❌ Error generating explanation for '{phrase}': {e}")
        return None


def main():
    """Main function to generate phrase explanations"""

    if len(sys.argv) != 2:
        print("Usage: python business.py <number_of_phrases>")
        print("Example: python business.py 3")
        sys.exit(1)

    try:
        num = int(sys.argv[1])
        if num <= 0:
            raise ValueError()
    except ValueError:
        print("❌ Please provide a valid positive number")
        sys.exit(1)

    # Load pending phrases
    pending = load_phrases(PHRASES_FILE)
    if not pending:
        print("❌ No phrases found in pending_phrases.txt")
        sys.exit(1)

    # Load already done phrases
    done = load_phrases(DONE_FILE)

    # Filter out already done phrases (case-insensitive)
    done_lower = [d.lower() for d in done]
    remaining = [p for p in pending if p.lower() not in done_lower]

    if not remaining:
        print("✅ All phrases have already been processed.")
        sys.exit(0)

    # Take only N phrases
    batch = remaining[:num]

    print("=" * 60)
    print(f"📖 Phrase Explainer - Processing {len(batch)} phrase(s)")
    print("=" * 60)
    print()

    # Initialize LLM
    try:
        llm = get_llm()
        print()
    except Exception as e:
        print(f"❌ Error initializing LLM: {e}")
        sys.exit(1)

    next_index = get_next_index()
    created_files = []

    for phrase in batch:
        content = generate_explanation(llm, phrase)
        if content:
            filename = f"{next_index:03d}-{sanitize_filename(phrase)}.md"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Created: {filename}")
                created_files.append(filename)
                done.append(phrase)
                next_index += 1
            except Exception as e:
                print(f"❌ Error saving {filename}: {e}")
        print()

    # Update index.md with new entries
    if created_files:
        update_index(created_files, batch)

    # Update done_phrases.txt
    save_lines(DONE_FILE, done)

    # Remove processed phrases from pending
    remaining_after = [p for p in pending if p.lower() not in [d.lower() for d in done]]
    save_lines(PHRASES_FILE, remaining_after)

    # Summary
    print("=" * 60)
    print(f"✨ Created {len(created_files)} file(s):")
    for f in created_files:
        print(f"   📄 {f}")
    print(f"📋 Remaining phrases: {len(remaining_after)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
