import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.prompt import render
from app.schema import TenderNotice

EXAMPLES = [
    {
        "input": "项目名称：XX市政务云平台建设。预算：约1200万元。",
        "output": '{"project_name": "XX市政务云平台建设", "budget_wan": 1200.0}',
    }
]

DOCUMENT = "XX市智慧交通建设项目。采购人：XX市交通运输局。"

prompt = render(
    "extract",
    schema_json=json.dumps(
        TenderNotice.model_json_schema(), ensure_ascii=False, indent=2
    ),
    examples=EXAMPLES,
    document=DOCUMENT,
)

print(prompt)
print()
print("=" * 50)
print("prompt 长度：", len(prompt), "字符")

# ---------------------------------------------------------------------------
# 断言1：没有没渲染成功的花括号
#   （原来只打印不判断，看漏了也不知道。改成断言。）
# ---------------------------------------------------------------------------
leftover = prompt.count("{{") + prompt.count("}}")
print("残留的花括号（应为 0）：", leftover)
assert leftover == 0, f"❌ 有 {leftover} 个花括号没渲染成功，检查 render() 的参数！"

# ---------------------------------------------------------------------------
# ★★★ 断言2：必填区块一个都不能少
#
# 【为什么加这条】2026-09-30 踩的坑：模板末尾的「待抽取的公告原文：{{ document }}」
# 被误删了。后果特别隐蔽 —— 模型照样返回合法 JSON，只是全填 null，
# 界面上表现为"置信度 0.00、字段全是灰色破折号"，看起来像模型不行，
# 实际是【根本没把原文发给它】。
#
# 而且 StrictUndefined 拦不住：它管的是"模板用了你没传的变量"，
# 而这次是"你传了变量但模板没用"，属于反向漏检。
# 所以只能靠这里显式检查。
# ---------------------------------------------------------------------------
print()
print("--- 必填区块检查 ---")

# 两个必须原样出现的占位符 —— 少了任何一个，抽取必然失败
for placeholder in ["{{ document }}", "{{ schema_json }}"]:
    ok = placeholder in open(
        Path(__file__).parent.parent / "prompts" / "extract.j2", encoding="utf-8"
    ).read()
    print(f"  模板里有 {placeholder:20} : {'✅' if ok else '❌ 丢了！'}")
    assert ok, f"❌ 模板里缺少 {placeholder} —— 模型会拿不到必要信息，返回全 null"

# 渲染结果里必须能看到原文 —— 这条直接拦"传了但没用"的漏检
print(f"  渲染结果含原文          : {'✅' if DOCUMENT in prompt else '❌ 丢了！'}")
assert DOCUMENT in prompt, (
    "❌ 渲染出来的 prompt 里没有原文！\n"
    "   多半是模板末尾的 `待抽取的公告原文：{{ document }}` 被删了。\n"
    "   后果：模型没东西可抽，会返回全 null（看起来像抽取失败，其实是没给原文）。"
)

# 渲染结果里必须能看到 Schema —— 少了它会抽得乱七八糟
print(f"  渲染结果含 Schema       : {'✅' if 'TenderNotice' in prompt else '❌ 丢了！'}")
assert "TenderNotice" in prompt, "❌ 渲染结果里没有 Schema，检查 {{ schema_json }}"

print("\n✅ 通过")