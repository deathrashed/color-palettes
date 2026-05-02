import os
import json
import re

def pascal_case(s):
    # Remove file extension
    name = os.path.splitext(s)[0]
    # Replace underscores and hyphens with spaces
    name = re.sub(r'[_-]', ' ', name)
    # Split by spaces
    words = name.split()
    new_words = []
    for word in words:
        # If it's something like iTerm, preserve it
        if word.lower().startswith('iterm'):
             # If it's already iTerm... or iterm...
             if word.lower() == 'iterm2':
                 new_words.append('iTerm2')
             else:
                 new_words.append(word)
        elif word.islower():
            new_words.append(word.capitalize())
        else:
            new_words.append(word)
    
    # If the first word was something like "ayu", it might be lowercase
    if new_words and new_words[0][0].islower() and not new_words[0].startswith('i'):
        new_words[0] = new_words[0][0].upper() + new_words[0][1:]

    return ' '.join(new_words) + '.json'

def clean_palettes(terminal_colors_dir, palettes_json_path, dry_run=True):
    changes = []
    
    # 1. Standardize filenames in terminal-colors
    files = os.listdir(terminal_colors_dir)
    rename_map = {}
    
    for filename in files:
        if not filename.endswith('.json'):
            continue
            
        new_filename = pascal_case(filename)
        # Handle cases like iTerm2 -> Iterm2
        if filename.startswith('iTerm'):
             # Preserve iTerm capitalization if possible, but let's stick to a rule
             # Looking at existing: "iTerm2 Dark Background.json"
             # If it already looks okay, maybe skip?
             # But the goal is standardization.
             pass

        if new_filename != filename:
            rename_map[filename] = new_filename
            changes.append(f"Rename: {filename} -> {new_filename}")

    # 2. Update palettes.json
    with open(palettes_json_path, 'r') as f:
        palettes_data = json.load(f)

    indexed_sources = {p.get('source') for p in palettes_data['palettes'] if p.get('source')}
    
    new_palettes = []
    # Check for missing terminal colors in palettes.json
    for filename in files:
        if not filename.endswith('.json'):
            continue
        
        current_name = filename
        target_name = rename_map.get(filename, filename)
        source_path = os.path.join('palettes/terminal-colors', target_name)
        
        # Check if this source is already indexed (using target name to be safe)
        if source_path not in indexed_sources:
             # Create new entry
             palette_id = os.path.splitext(target_name)[0].lower().replace(' ', '-')
             # Clean up id
             palette_id = re.sub(r'[^a-z0-9-]', '', palette_id)
             
             new_entry = {
                 "id": palette_id,
                 "name": os.path.splitext(target_name)[0],
                 "clr": f"clr/terminal-colors/{os.path.splitext(target_name)[0]}.clr", # Guessing clr path
                 "source": source_path,
                 "source_status": "canonical",
                 "color_count": None,
                 "category": "terminal-colors",
                 "notes": f"Automatically indexed from {terminal_colors_dir}"
             }
             new_palettes.append(new_entry)
             changes.append(f"Index: Add {target_name} to palettes.json")

    if new_palettes:
        palettes_data['palettes'].extend(new_palettes)

    # Update existing entries if they were renamed
    for palette in palettes_data['palettes']:
        source = palette.get('source')
        if source and source.startswith('palettes/terminal-colors/'):
            filename = os.path.basename(source)
            if filename in rename_map:
                new_source = os.path.join('palettes/terminal-colors', rename_map[filename])
                palette['source'] = new_source
                # Also update clr if it matched
                if palette.get('clr') and filename.replace('.json', '.clr') in palette['clr']:
                     palette['clr'] = palette['clr'].replace(filename.replace('.json', ''), rename_map[filename].replace('.json', ''))
                changes.append(f"Update: Index for {filename} -> {rename_map[filename]}")

    return changes, palettes_data, rename_map

if __name__ == "__main__":
    TERMINAL_COLORS_DIR = "/Users/rd/Documents/Color Palettes/palettes/terminal-colors"
    PALETTES_JSON_PATH = "/Users/rd/Documents/Color Palettes/palettes.json"
    
    changes, updated_json, rename_map = clean_palettes(TERMINAL_COLORS_DIR, PALETTES_JSON_PATH)
    
    output_dir = "/Users/rd/Documents/Color Palettes/palette-manager-workspace/iteration-1/eval-0/with_skill/outputs"
    
    with open(os.path.join(output_dir, "dry_run_output.txt"), "w") as f:
        f.write("\n".join(changes))
    
    with open(os.path.join(output_dir, "updated_palettes.json"), "w") as f:
        json.dump(updated_json, f, indent=2)
        
    print(f"Dry run complete. {len(changes)} changes proposed.")
    print(f"Results saved to {output_dir}")
