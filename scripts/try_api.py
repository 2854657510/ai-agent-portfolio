"""命令行测抽取接口：不碰引号、不碰编码。

【新建文件 2026-09-29】
为什么不给 curl 命令：PowerShell 里 curl 是 Invoke-WebRequest 的假别名，
参数完全不一样，真 curl 要写 curl.exe；而且实测 Invoke-RestMethod 发中文
body 会乱码（服务端收到 35 个字符而不是 11 个）。用这个纯 Python 脚本，
一次绕开全部坑。

先启动服务：
    uvicorn app.main:app --reload

用法：
    python scripts/try_api.py                       # 跑内置的两个用例
    python scripts/try_api.py "你自己的文本"         # 测一段自定义文本
"""
import json
import sys
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8000/api/extract"

CASES = [
    (
        "正常公告",
        "XX市智慧交通建设项目。采购人：XX市交通运输局。预算约1850万元。"
        "联系人：李工 电话0571-8888xxxx。资格要求：具有独立法人资格。",
    ),
    ("不是公告（应走降级）", "明天多云转晴，最高气温 26 度，东南风 3 级。"),
]


def call(document: str) -> None:
    """打一次接口，把状态码和返回体都打出来。"""
    body = json.dumps({"document": document}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        URL, data=body, headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            print("状态码:", resp.status)
            data = json.loads(resp.read())
            print("返回体:", json.dumps(data, ensure_ascii=False, indent=2))
    except urllib.error.HTTPError as e:
        # 422 走这里 —— 不是程序出错，是我们主动要看的降级结果
        print("状态码:", e.code, "（降级路径）")
        detail = json.loads(e.read()).get("detail")
        print("detail:", json.dumps(detail, ensure_ascii=False, indent=2)[:400])
    except urllib.error.URLError as e:
        print("❌ 连不上服务 —— uvicorn 起了吗？", e.reason)


if __name__ == "__main__":
    cases = [("自定义文本", sys.argv[1])] if len(sys.argv) > 1 else CASES

    for name, doc in cases:
        print(f"\n===== {name} =====")
        print("输入:", doc[:40] + ("..." if len(doc) > 40 else ""))
        call(doc)
