
import re

def parse_shop_message(text, photo=None, message_id=None):
    """Parse a shop message and extract item data"""
    try:
        if "──────⊱◈Shop◈⊰──────" not in text:
            return None
        
        # Extract item name
        name_match = re.search(r"✦ Item Name\s*:\s*(.+)", text)
        item_name = name_match.group(1).strip() if name_match else "Unknown"
        
        # Extract item type/category (handle both with and without #)
        type_match = re.search(r"✧ Item Type\s*:\s*#?(.+)", text)
        item_type = type_match.group(1).strip() if type_match else "Misc"
        
        # Extract country (handle both with and without #)
        country_match = re.search(r"✦ Country\s*:\s*#?(.+)", text)
        country = country_match.group(1).strip() if country_match else "All"
        
        # Extract description (everything between Description and Price & Materials)
        desc_match = re.search(r"✧ Description\s*:\s*\n(.*?)(?=\n✦ Price & Materials|$)", text, re.DOTALL)
        description = ""
        if desc_match:
            desc_text = desc_match.group(1).strip()
            # Clean up description - remove bullet points and extra whitespace
            desc_lines = [line.strip().lstrip('•').strip() for line in desc_text.split('\n') if line.strip()]
            description = ' '.join(desc_lines)
        
        # Extract price and materials
        price_match = re.search(r"✦ Price & Materials\s*:\s*\n(.*?)(?=\n✧ Owner ID|$)", text, re.DOTALL)
        price = 0
        materials = {}
        
        if price_match:
            price_text = price_match.group(1).strip()
            # Remove bullet points
            price_text = price_text.lstrip('•').strip()
            
            # Parse price and materials from format like "32000, Jewel:32"
            if ',' in price_text:
                parts = price_text.split(',')
                # First part is usually the price
                try:
                    price = int(parts[0].strip())
                except:
                    pass
                
                # Rest are materials
                for part in parts[1:]:
                    part = part.strip()
                    if ':' in part:
                        mat_match = re.search(r'(\w+):(\d+)', part)
                        if mat_match:
                            materials[mat_match.group(1)] = int(mat_match.group(2))
            else:
                # Only price, no materials
                price_only = re.search(r'(\d+)', price_text)
                if price_only:
                    price = int(price_only.group(1))
        
        # Extract owner ID
        owner_match = re.search(r"✧ Owner ID\s*:\s*(.+)", text)
        owner_id = owner_match.group(1).strip() if owner_match else ""
        
        # Extract hashtags
        hashtags = re.findall(r'#\w+', text)
        
        return {
            "name": item_name,
            "type": item_type,
            "country": country,
            "description": description,
            "price": price,
            "materials": materials,
            "owner_id": owner_id,
            "hashtags": hashtags,
            "photo_file_id": photo[0].file_id if photo else None,
            "message_id": message_id
        }
        
    except Exception as e:
        print(f"Error parsing shop message: {e}")
        return None

# Test with your example
test_caption = """──────⊱◈Shop◈⊰──────  
✦ Item Name : Ninsathbkh  
✧ Item Type : Army  
✦ Country : Alpyr  
#Army  
#Alpyr  
✧ Description :  
• Sample description text  
✦ Price & Materials :  
• 32000, Jewel:32  
✧ Owner ID : @sdfgyhuiop  
──────⊹⊱✫⊰⊹──────  
https://t.me/R_O_T_C  
https://t.me/R_O_T_C_Shop"""

if __name__ == "__main__":
    result = parse_shop_message(test_caption)
    print("Parsed result:")
    for key, value in result.items():
        print(f"{key}: {value}")
