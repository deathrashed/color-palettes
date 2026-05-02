import os
import json
import re

def kebab_case(name):
    name = re.sub(r'[^a-zA-Z0-9\s-]', '', name)
    name = re.sub(r'[\s_]+', '-', name).lower()
    return name.strip('-')

def cleanup():
    terminal_colors_dir = 'palettes/terminal-colors'
    palettes_json_path = 'palettes.json'
    output_dir = 'palette-manager-workspace/iteration-1/eval-0/without_skill/outputs'
    
    with open(palettes_json_path, 'r') as f:
        palettes_data = json.load(f)
    
    existing_ids = {p['id'] for p in palettes_data['palettes']}
    
    dry_run_report = []
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
            dry_run_report.append(f"Error reading {filename}: {e}")
            continue
            
        new_id = kebab_case(display_name)
        new_filename = f"{new_id}.json"
        
        if filename != new_filename:
            dry_run_report.append(f"Rename: {filename} -> {new_filename} (Name: {display_name})")
        else:
            dry_run_report.append(f"Keep: {filename} (Name: {display_name})")
            
        # Check if it needs to be added to palettes.json
        if new_id not in existing_ids:
            new_entry = {
                "id": new_id,
                "name": display_name,
                "clr": f"clr/terminal-colors/{display_name}.clr", # Hypothetical .clr path based on existing pattern
                "source": f"palettes/terminal-colors/{new_filename}",
                "source_status": "canonical",
                "color_count": color_count,
                "category": "terminal-colors",
                "notes": f"Canonical source added from palettes/terminal-colors/{new_filename} during cleanup."
            }
            new_palettes.append(new_entry)
            dry_run_report.append(f"Index: Add {new_id} to palettes.json")
        else:
            # Update existing entry if needed (e.g., source path change)
            for p in palettes_data['palettes']:
                if p['id'] == new_id:
                    if p.get('source') != f"palettes/terminal-colors/{new_filename}":
                        dry_run_report.append(f"Update: Index source for {new_id} to palettes/terminal-colors/{new_filename}")
            
    # Prepare the updated palettes.json content (in memory for dry-run)
    updated_palettes = palettes_data['palettes'] + new_palettes
    # Sort by ID for consistency
    updated_palettes.sort(key=lambda x: x['id'])
    palettes_data['palettes'] = updated_palettes
    
    # Save dry-run report
    with open(os.path.join(output_dir, 'dry_run_report.txt'), 'w') as f:
        f.write("\n".join(dry_run_report))
        
    # Save the proposed palettes.json
    with open(os.path.join(output_dir, 'proposed_palettes.json'), 'w') as f:
        json.dump(palettes_data, f, indent=2)
        
    print(f"Dry-run report saved to {os.path.join(output_dir, 'dry_run_report.txt')}")
    print(f"Proposed palettes.json saved to {os.path.join(output_dir, 'proposed_palettes.json')}")

if __name__ == "__main__":
    cleanup()
