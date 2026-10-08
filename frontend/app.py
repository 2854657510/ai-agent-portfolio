import time
import streamlit as st
import api_client

# 页面配置
st.set_page_config(
    page_title="招投标公告结构化抽取",
    page_icon="📄",
    layout="wide",
)




# 侧边栏
with st.sidebar:
    st.header("后端连接")

    base_url = st.text_input(
        "后端地址",
        value=api_client.DEFAULT_BASE_URL,
        help="先启用后端服务",
    )

    # 监测后端状态
    if api_client.check_health(base_url):
        st.success("🟢 后端已连接", icon="✅")
    else:
        st.error("🔴 连不上后端")
        st.caption("运行另一个终端")


    if "doc_text" not in st.session_state:
        st.session_state.doc_text = ""


st.title("结构化抽取")
tab_extract = st.tabs(["结构化抽取"])[0]


with tab_extract:
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("输入")
        document = st.text_area(
            "公告原文",
            key="doc_text",
            height=300,
            placeholder="粘贴招投标公告原文",
        )
        run = st.button(
            "开始抽取", type="primary", use_container_width=True
        )

    with right:
        st.subheader("结果")
        if run:
            if not document.strip():
                st.warning("请先输入公告原文")
            else:
                with st.spinner("正在调模型抽取..."):
                    t0 = time.perf_counter()
                    try:
                        st.session_state.result = api_client.extract(base_url, document)
                        st.session_state.error = None
                    except api_client.BackendDown as e:
                        st.session_state.result = None
                        st.session_state.error = ("连接失败", str(e)[:300])
                    except api_client.BackendError as e:
                        st.session_state.result = None
                        st.session_state.error = (
                            f"抽取失败（HTTP {e.status_code}）",
                            str(e.detail)[:300],
                        )
                    st.session_state.elapsed = time.perf_counter() - t0

        error = st.session_state.get("error")
        result = st.session_state.get("result")

        if error:
            title, detail = error
            st.error(f"**{title}**")
            st.code(detail, language=None)
        elif result:
            conf = float(result.get("confidence") or 0.0)
            elapsed = st.session_state.get("elapsed", 0.0)

           # 文章可信度
            if conf >= 0.8:
                level, color = "高", "🟢"
            elif conf >= 0.5:
                level, color = "中", "🟡"
            else:
                level, color = "低（信息不全，模型如实告知）", "🔴"

            c1, c2 = st.columns(2)
            c1.metric("模型自评置信度", f"{conf:.2f}", help="0-1，模型对自己这次抽取的把握")
            c2.metric("耗时", f"{elapsed:.2f} 秒")

            st.progress(min(max(conf, 0.0), 1.0))
            st.caption(f"{color} 置信度：{level}")

            st.divider()


            st.markdown("##### 核心字段")
            # 处理空值信息
            def show(label: str, value, fallback: str = "—"):
                if value is None or value == "":
                    st.markdown(f"**{label}**：:gray[{fallback}]")
                else:
                    st.markdown(f"**{label}**：{value}")

            show("项目名称", result.get("project_name"))
            show("采购人 / 招标人", result.get("buyer"))

            budget = result.get("budget_wan")
            show("预算金额", f"{budget} 万元" if budget is not None else None)
            show("投标截止时间", result.get("deadline"))

            # 资格要求
            quals = result.get("qualification") or []
            st.markdown("##### 资格要求")
            if quals:
                for i, q in enumerate(quals, 1):
                    st.markdown(f"{i}. {q}")
            else:
                st.markdown(":gray[— 原文未提及]")

            # 联系人
            contact = result.get("contact") or {}
            st.markdown("##### 联系人")
            cc1, cc2 = st.columns(2)
            cc1.markdown(f"**姓名**：{contact.get('name') or ':gray[—]'}")
            cc2.markdown(f"**电话**：{contact.get('phone') or ':gray[—]'}")

            # 原始 JSON
            with st.expander("查看原始 JSON（接口实际返回的内容）"):
                st.json(result)

        else:
            st.info("在左边输入公告原文，点「开始抽取」")


