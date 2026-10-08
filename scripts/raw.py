import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from pydantic import ValidationError
from app.config import settings
from app.prompt import render
from app.schema import TenderNotice

client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)



DOC = """
XX市智慧交通建设项目招标公告

招标编号：XZ-2026-0912
采购人：XX市交通运输局
本项目预算金额约 1850 万元，资金来源为市级财政。
投标截止时间为 2026 年 10 月 20 日 9:30。
资格要求：1. 具有独立法人资格；2. 具备电子与智能化工程专业承包二级及以上资质；
3. 近三年无重大违法记录。
联系人：李工  联系电话：0571-8888xxxx
具体技术参数及评分办法详见招标文件附件，本项目不接受联合体投标。
"""
EXAMPLES = [
    {
        "input": "项目名称：XX市政务云平台建设。采购人：XX市大数据局。预算：约1200万元。",
        "output": '{"project_name": "XX市政务云平台建设", "buyer": "XX市大数据局", "budget_wan": 1200.0, "deadline": null, "qualification": [], "contact": {"name": null, "phone": null}, "confidence": 0.9}',
    },
    {
        "input": "招标公告。本项目由某某单位组织，具体事宜详见附件。联系人：张工 电话138xxxx",
        "output": '{"project_name": null, "buyer": null, "budget_wan": null, "deadline": null, "qualification": [], "contact": {"name": "张工", "phone": "138xxxx"}, "confidence": 0.4}',
    },
]


prompt = render(
    "extract",
    schema_json=json.dumps(
        TenderNotice.model_json_schema(), ensure_ascii=False, indent=2
    ),
    examples=EXAMPLES,
    document=DOC,
)



resp = client.chat.completions.create(
    model=settings.deepseek_model,
    messages=[{"role": "system", "content": prompt}],
    response_format={"type": "json_object"},
    temperature=0.0,
    max_tokens=2048,
)

raw = resp.choices[0].message.content

print("=" * 50)
print("模型原文：")
print(raw)
print("=" * 50)
print("token 用量：", resp.usage)
print("prompt 长度：", len(prompt), "字符")

try:
    notice = TenderNotice.model_validate_json(raw)
    print("\n✅ 校验通过")
    print("项目名称：", notice.project_name)
    print("预算(万)：", notice.budget_wan)
    print("联系人：", notice.contact.name)
    print("置信度：", notice.confidence)
except ValidationError as e:
    print("\n❌ 校验失败，具体错在哪：")
    print(e)