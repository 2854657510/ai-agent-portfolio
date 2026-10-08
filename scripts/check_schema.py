import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.schema import TenderNotice

schema = TenderNotice.model_json_schema()
print("顶层字段：", list(schema["properties"].keys()))
print()
print(json.dumps(schema, ensure_ascii=False, indent=2))
