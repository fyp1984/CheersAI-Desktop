import glob
import re

revs = set()
downs = set()
for f in glob.glob("migrations/versions/*.py"):
    c = open(f).read()
    r = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", c)
    if r: revs.add(r.group(1))
    
    d_match = re.search(r"down_revision\s*=\s*(\([^\)]+\)|['\"][^'\"]+['\"])", c)
    if d_match:
        val = d_match.group(1)
        import ast
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, str):
                downs.add(parsed)
            else:
                downs.update(parsed)
        except:
            pass
print("Heads:", revs - downs)
