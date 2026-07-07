import json
import sys
import re

def extract_entities(text, custom_patterns_file=None, key_fields=None): 
    # Nếu không truyền, mặc định lấy ips và ne_names làm key như quy trình
    if key_fields is None:
        key_fields = ['ips', 'ne_names']

    patterns_config = {
        "ips": {
            "regex": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'group': 0
        },
        "ne_names": {
            # CHUẨN SKILL.MD: Yêu cầu >= 3 đoạn phân tách bằng - hoặc _ (Ví dụ: HNI-CORE-01, SGN_RAN_15)
            # Loại bỏ hoàn toàn các từ đơn viết hoa như NE, DOWN, OSPF...
            "regex": r'\b[A-Z0-9]+(?:[\-_][A-Z0-9]+){2,}\b', 
            'group': 0
        },
        "interfaces": {
            "regex": r'\b[a-zA-Z]+[0-9]+/[0-9]+(?:/[0-9]+)?\b', 
            "group": 0
        }, 
        "cell_ids": {
            "regex": r'\b[A-Za-z0-9]+_[A-Za-z0-9]+\b', 
            "group": 0
        },
        "as_numbers": {
            "regex": r'\bAS\d+\b', 
            "group": 0
        }
    }
    
    if custom_patterns_file:
        try: 
            with open(custom_patterns_file, 'r') as f:
                custom_patterns = json.load(f)
                patterns_config.update(custom_patterns)
        except Exception as e:
            sys.stderr.write(f"Lỗi đọc file patterns: {str(e)}\n")
            return {"extracted": {}, "lookup_keys": []}
    
    extracted = {} 
    lookup_keys = set() # Dùng set để chống trùng lặp tuyệt đối
    
    for key, config in patterns_config.items(): 
        regex = config['regex']
        group = config.get('group', 0)
        
        matches = [] 
        try: 
            for match in re.finditer(regex, text):
                if group < len(match.groups()) + 1:
                    matches.append(match.group(group))
        except re.error:
            continue
        
        if matches: 
            unique_matches = list(set(matches))
            extracted[key] = unique_matches
            
            # Chỉ những trường nằm trong danh sách chỉ định mới được làm khóa tra cứu
            if key in key_fields:
                lookup_keys.update(unique_matches)
    
    return {
        "extracted": extracted,
        "lookup_keys": list(lookup_keys)
    }