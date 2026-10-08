"""验收 app/config.py：不管从哪个目录运行，都必须读到 .env 里的值。

【新建文件 2026-09-29】
这正是"404 / APIConnectionError"的验收项 —— 那两个错的根因都是 .env 没被读到。

用法（三次输出必须完全一样）：
    cd "C:\\Users\\Firebat\\Desktop\\ai-agent-portfolio"; python scripts\\check_config.py
    cd C:\\; python "C:\\Users\\Firebat\\Desktop\\ai-agent-portfolio\\scripts\\check_config.py"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR, settings

print("BASE_DIR =", BASE_DIR)
print("base_url =", settings.deepseek_base_url)
print("model    =", settings.deepseek_model)

# 断言1：base_url 必须是完整 URL
assert settings.deepseek_base_url.startswith(("http://", "https://")), (
    f"❌ base_url 不是完整 URL：{settings.deepseek_base_url!r}"
)

# 断言2：绝不能掉回那个不存在的域名
assert settings.deepseek_base_url != "https://deepseek.com", (
    "❌ 掉回默认域名了 —— .env 没读到，检查 config.py 的 env_file 是不是绝对路径"
)

# 断言3：BASE_DIR 必须指向项目根
assert (BASE_DIR / "app").is_dir(), f"❌ BASE_DIR 算错了：{BASE_DIR}"
assert (BASE_DIR / ".env").is_file(), f"❌ {BASE_DIR / '.env'} 不存在"

print("\n✅ 通过 —— .env 被正确读到了")
