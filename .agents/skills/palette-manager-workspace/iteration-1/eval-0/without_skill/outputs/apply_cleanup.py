import os
import json
import re
import shutil

def kebab_case(name):
    name = re.sub(r'[^a-zA-Z0-9\s-]', '', name)
    name = re.sub(r'[\s_]+', '-', name).lower()
    return name.strip('-')

def apply_cleanup():
    terminal_colors_dir = 'palettes/terminal-colors'
    palettes_json_path = 'palettes.json'
    
    if not os.path.exists(palettes_json_path):
        print(f"Error: {palettes_json_path} not found.")
        return

    with open(palettes_json_path, 'r') as f:
        palettes_data = json.load(f)
    
    existing_ids = {p['id'] for p in palettes_data['palettes']}
    new_palettes = []
    
    files = [f for f in os.listdir(terminal_colors_dir) if f.endswith('.json')]
    files.sort()
    
    for filename in files:
        file_path = os.path.join(terminal_colors_dir, filename)
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                display_name = data.get('name', os.path.splitext(filename)[0])
                color_count = len(data.get('colors', []))
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue
            
        new_id = kebab_case(display_name)
        new_filename = f"{new_id}.json"
        new_file_path = os.path.join(terminal_colors_dir, new_filename)
        
        # Rename file
        if filename != new_filename:
            print(f"Renaming: {filename} -> {new_filename}")
            os.rename(file_path, new_file_path)
        
        # Update/Add to index
        if new_id not in existing_ids:
            new_entry = {
                "id": new_id,
                "name": display_name,
                "clr": f"clr/terminal-colors/{display_name}.clr",
                "source": f"palettes/terminal-colors/{new_filename}",
                "source_status": "canonical",
                "color_count": color_count,
                "category": "terminal-colors",
                "notes": f"Canonical source added from palettes/terminal-colors/{new_filename} during cleanup."
            }
            new_palettes.append(new_entry)
            print(f"Adding to index: {new_id}")
        else:
            # Update existing entry source path if it changed
            for p in palettes_data['palettes']:
                if p['id'] == new_id:
                    p['source'] = f"palettes/terminal-colors/{new_filename}"
                    print(f"Updated index entry for: {new_id}")

    # Update palettes.json
    palettes_data['palettes'].extend(new_palettes)
    palettes_data['palettes'].sort(key=lambda x: x['id'])
    
    with open(palettes_json_path, 'w') as f:
        json.dump(palettes_data, f, indent=2)
    
    print("Cleanup applied successfully.")

if __name__ == "__main__":
    # In a real scenario, we might want to backup palettes.json first
    # shutil.copy('palettes.json', 'palettes.json.bak')
    apply_cleanup()
