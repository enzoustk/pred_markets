import ast

def safe_divide(num, den):
    try: return num/den
    except: return None

def to_list(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            v = ast.literal_eval(x)
            return v if isinstance(v, list) else []
        except:
            return []
    return []