import os
import streamlit as st
import requests

st.set_page_config(
    page_title="CodeLens",
    page_icon="🔍",
    layout="wide",
)
# ── Custom CSS — watermark fixed at bottom right ──────────────────────────
st.markdown("""
    <style>
        .watermark {
            position: fixed;
            bottom: 15px;
            right: 20px;
            font-size: 13px;
            color: rgba(255, 255, 255, 0.35);
            z-index: 9999;
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 0.5px;
            pointer-events: none;
        }
        .watermark:hover {
            color: rgba(255, 255, 255, 0.75);
            transition: color 0.3s ease;
        }
    </style>
    <div class="watermark">Made by Alok Kumar Yadav</div>
""", unsafe_allow_html=True)

try:
    API_BASE = st.secrets["BACKEND_URL"]
except (FileNotFoundError, KeyError):
    API_BASE = os.environ.get("BACKEND_URL", "http://localhost:8000/api")


@st.cache_data(ttl=3600)
def get_supported_languages() -> list[str]:
    try:
        r = requests.get(f"{API_BASE}/languages", timeout=5)
        return ["auto"] + r.json().get("languages", [])
    except Exception:
        return ["auto", "python", "javascript", "typescript", "java", "go", "cpp", "rust", "swift"]


if "history" not in st.session_state:
    st.session_state.history = []

st.title("🔍 CodeLens")
st.caption("Paste code → get bugs, improvements & security issues")

with st.sidebar:
    st.header("Settings")
    languages = get_supported_languages()
    selected_language = st.selectbox(
        "Language", options=languages, index=0,
        help="Choose a language or leave as 'auto' to let the AI detect it.",
    )
    st.divider()
    st.markdown(
        "**How it works**\n\n"
        "1. Upload or paste your code — the system reads and understands what it does.\n\n"
        "2. AI analyzes the code for bugs, performance issues, security risks, and best practices.\n\n"
        "3. AI generates a detailed review explaining potential problems and suggesting improvements.\n\n"
        "4. Results are organized into categories:\n"
        "   - 🐞 Bugs & Errors\n"
        "   - ⚡ Performance\n"
        "   - 🔒 Security\n"
        "   - ✨ Code Quality\n"
        "   - 💡 Best Practices\n\n"
        "5. Use the suggestions to make your code cleaner, safer, and more efficient."
    )
    st.divider()
    st.caption(f"Backend: `{API_BASE}`")

    if st.session_state.history:
        st.divider()
        st.subheader("📜 History")
        for i, entry in enumerate(reversed(st.session_state.history)):
            label = f"{entry['language'].capitalize()} — {entry['severity']} — #{len(st.session_state.history) - i}"
            if st.button(label, key=f"history_{i}"):
                st.session_state.selected_history = entry["result"]

code_input = st.text_area(
    label="Paste your code here",
    height=320,
    placeholder="# paste any Python, JS, TypeScript, C++, Java, Go, Rust, Swift … snippet here",
)

review_clicked = st.button(
    "Review Code",
    type="primary",
    disabled=not code_input.strip(),
)

if review_clicked:
    with st.spinner("Analysing with CodeBERT + Groq …"):
        try:
            response = requests.post(
                f"{API_BASE}/review",
                json={"code": code_input, "language": selected_language},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

        except requests.exceptions.ConnectionError:
            st.error(
                f"Cannot reach the backend at `{API_BASE}`.\n\n"
                "Make sure FastAPI is running in the other terminal."
            )
            st.stop()

        except requests.exceptions.HTTPError as exc:
            st.error(f"Backend error {exc.response.status_code}: {exc.response.text}")
            st.stop()

    st.session_state.history.append({
        "code":     code_input[:100] + "...",
        "language": result["language"],
        "severity": result["severity"],
        "result":   result,
    })

    col_lang, col_sev, _ = st.columns([1, 1, 4])
    col_lang.metric("Language", result["language"].capitalize())
    severity_icons = {"low": "🟢", "medium": "🟡", "high": "🔴"}
    icon = severity_icons.get(result["severity"], "⚪")
    col_sev.metric("Severity", f"{icon} {result['severity'].capitalize()}")

    st.divider()
    st.subheader("Summary")
    st.write(result["summary"])
    st.divider()

    col_bugs, col_sec, col_imp = st.columns(3)

    with col_bugs:
        st.subheader(f"🐛 Bugs ({len(result['bugs'])})")
        if result["bugs"]:
            for bug in result["bugs"]:
                if isinstance(bug, dict):
                    line = bug.get("line", "?")
                    desc = bug.get("description", "")
                    st.error(f"**Line {line}:** {desc}")
                else:
                    st.error(bug)
        else:
            st.success("No bugs found!")

    with col_sec:
        st.subheader(f"🔒 Security ({len(result['security_issues'])})")
        if result["security_issues"]:
            for issue in result["security_issues"]:
                st.warning(issue)
        else:
            st.success("No security issues found!")

    with col_imp:
        st.subheader(f"✨ Improvements ({len(result['improvements'])})")
        if result["improvements"]:
            for tip in result["improvements"]:
                st.info(tip)
        else:
            st.success("Code looks great!")

    if result.get("fixes"):
        st.divider()
        st.subheader("🔧 Suggested Fixes")
        for fix in result["fixes"]:
            col_old, col_new = st.columns(2)
            with col_old:
                st.markdown("**Before**")
                st.code(fix["original"], language=result["language"])
            with col_new:
                st.markdown("**After**")
                st.code(fix["suggested"], language=result["language"])

    # ── Performance chart ─────────────────────────────────────────────────
    # FIX: Moved INSIDE `if review_clicked:` — was outside before, which
    #      caused NameError on first load because `result` didn't exist yet.
    scores = result.get("performance_scores", {})
    before = scores.get("before", {})
    after  = scores.get("after",  {})

    if before and after:
        import plotly.graph_objects as go

        categories = ["Readability", "Security", "Performance", "Maintainability", "Best Practices"]
        keys       = ["readability", "security", "performance", "maintainability", "best_practices"]

        before_vals = [before.get(k, 0) for k in keys]
        after_vals  = [after.get(k, 0)  for k in keys]

        st.divider()
        st.subheader("📊 Code Performance: Before vs After")

        fig = go.Figure(data=[
            go.Bar(
                name="Before",
                x=categories,
                y=before_vals,
                marker_color="#ef4444",
                text=before_vals,
                textposition="outside",
            ),
            go.Bar(
                name="After (with fixes)",
                x=categories,
                y=after_vals,
                marker_color="#22c55e",
                text=after_vals,
                textposition="outside",
            ),
        ])

        fig.update_layout(
            barmode="group",
            yaxis=dict(range=[0, 110], title="Score (0-100)"),
            xaxis_title="Category",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=40, b=40),
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3, col4, col5 = st.columns(5)
        for col, cat, key in zip([col1, col2, col3, col4, col5], categories, keys):
            delta = after.get(key, 0) - before.get(key, 0)
            col.metric(
                label=cat,
                value=f"{after.get(key, 0)}/100",
                delta=f"+{delta}" if delta > 0 else str(delta),
            )