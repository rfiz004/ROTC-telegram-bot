
import json
import os

import json
import os

def migrate_castle_data():
    """Migrate existing province files to convert castle dictionaries to lists"""
    provinces_dir = "provinces"
    
    if not os.path.exists(provinces_dir):
        print("No provinces directory found.")
        return
    
    migrated_count = 0
    
    for filename in os.listdir(provinces_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(provinces_dir, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if castle is a dictionary
                if isinstance(data.get("castle"), dict):
                    print(f"Migrating {filename}...")
                    
                    # Convert dictionary values to list
                    castle_dict = data["castle"]
                    castle_list = []
                    
                    # Extract values from the dictionary
                    for key, value in castle_dict.items():
                        if value and value.strip():
                            castle_list.append(value)
                    
                    # Replace with list
                    data["castle"] = castle_list
                    
                    # Save updated data
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    migrated_count += 1
                    print(f"✅ Migrated {filename}: {len(castle_list)} castle items")
                
                elif isinstance(data.get("castle"), list):
                    print(f"✓ {filename} already has castle as list")
                
                else:
                    print(f"⚠️ {filename} has invalid castle format, setting to empty list")
                    data["castle"] = []
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    migrated_count += 1
                    
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
    
    print(f"\n🎉 Migration complete! {migrated_count} files processed.") pprocessed.")

if __name__ == "__main__":
    migrate_castle_data()castle_data()
