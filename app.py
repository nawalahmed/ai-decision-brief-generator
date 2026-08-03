import streamlit as st
import pandas as pd
import plotly.express as px

st.title("AI Decision Brief Generator")

# ---- Provider + API key, supplied by the user, kept in-session only ----
st.sidebar.header("AI settings")
provider = st.sidebar.selectbox("Model provider", ["Gemini", "OpenAI"])
api_key = st.sidebar.text_input(f"{provider} API key", type="password")
st.sidebar.caption(
    "Your key is used only for this session and is never stored, logged, "
    "or sent anywhere besides the provider's API."
)
if provider == "Gemini":
    st.sidebar.caption("Get a free key: aistudio.google.com/apikey")
else:
    st.sidebar.caption("Get a key: platform.openai.com/api-keys")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, thousands=",")
    df.columns = [c.strip().upper() for c in df.columns]

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    st.subheader("Quick Stats")
    st.write(f"Rows: {len(df)}")
    st.write(f"Columns: {len(df.columns)}")

    # ---- 1. Compute the real numbers first ----
    total_views = df["PAGE VIEWS"].sum()

    by_site = (
        df.groupby("WEBSITE")["PAGE VIEWS"].sum().sort_values(ascending=False)
    )
    by_site_pct = (by_site / total_views * 100).round(1)

    top5 = df.sort_values("PAGE VIEWS", ascending=False).head(5).copy()
    top5["% OF TOTAL"] = (top5["PAGE VIEWS"] / total_views * 100).round(1)

    top3_share = round(
        df.sort_values("PAGE VIEWS", ascending=False).head(3)["PAGE VIEWS"].sum()
        / total_views * 100, 1
    )

    high_bounce = df[
        (df["BOUNCE RATE (%)"] > 0.70) & (df["ENTRANCES"] > 1000)
    ].sort_values("ENTRANCES", ascending=False)

    low_time_high_views = df[
        (df["AVERAGE TIME ON PAGE (SECONDS)"] < 5) & (df["PAGE VIEWS"] > 10000)
    ].sort_values("PAGE VIEWS", ascending=False)

    df["PV_UV_RATIO"] = df["PAGE VIEWS"] / df["UNIQUE VIEWS"].replace(0, 1)
    refresh_loops = df[df["PV_UV_RATIO"] > 10].sort_values(
        "PV_UV_RATIO", ascending=False
    )

    corr = df["AVERAGE TIME ON PAGE (SECONDS)"].corr(df["BOUNCE RATE (%)"])

    # ---- 2. Charts straight from pandas, not the LLM ----
    st.subheader("Top 10 pages by page views")
    top10 = df.sort_values("PAGE VIEWS", ascending=False).head(10)
    fig1 = px.bar(
        top10, x="PAGE VIEWS", y="PAGE PATH", orientation="h",
        text=top10["PAGE VIEWS"].apply(lambda v: f"{v:,}")
    )
    fig1.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Top 10 pages by bounce rate (entrances > 1,000)")
    top_bounce = high_bounce.sort_values("BOUNCE RATE (%)", ascending=False).head(10)
    fig2 = px.bar(
        top_bounce, x="BOUNCE RATE (%)", y="PAGE PATH", orientation="h",
        text=top_bounce["BOUNCE RATE (%)"].apply(lambda v: f"{v*100:.0f}%")
    )
    fig2.update_layout(yaxis=dict(autorange="reversed"), xaxis_range=[0, 1])
    st.plotly_chart(fig2, use_container_width=True)

    # ---- 3. Build the prompt with computed numbers embedded ----
    def fmt_rows(sub_df, cols):
        return "\n".join(
            f"- {r['WEBSITE']} {r['PAGE PATH']}: " +
            ", ".join(f"{c}={r[c]}" for c in cols)
            for _, r in sub_df.iterrows()
        )

    prompt = f"""
You are a data analyst. Write a report using ONLY the numbers below — do not
invent or round differently than what is given. Do not use vague qualifiers
like "some pages" or "significantly" — always name the page and cite the number.

COMPUTED METRICS
- Total page views: {total_views:,}
- Page views by site (% of total):
{by_site_pct.to_string()}
- Top 5 pages by views:
{fmt_rows(top5, ['PAGE VIEWS', '% OF TOTAL', 'BOUNCE RATE (%)', 'AVERAGE TIME ON PAGE (SECONDS)'])}
- Top 3 pages = {top3_share}% of total traffic (long-tail concentration)
- Pages with bounce rate > 70% AND entrances > 1,000 (showing top 10 by entrances):
{fmt_rows(high_bounce.head(10), ['BOUNCE RATE (%)', 'ENTRANCES', 'PAGE VIEWS'])}
- Pages with avg time on page < 5s despite > 10,000 views (likely bot/embed anomalies):
{fmt_rows(low_time_high_views, ['PAGE VIEWS', 'AVERAGE TIME ON PAGE (SECONDS)', 'BOUNCE RATE (%)'])}
- Pages where page views are 10x+ unique views (possible refresh loops):
{fmt_rows(refresh_loops.head(8), ['PAGE VIEWS', 'UNIQUE VIEWS', 'PV_UV_RATIO'])}
- Correlation between avg time on page and bounce rate: {corr:.3f}

Write:
## Executive Summary
2-3 sentences citing the total traffic figure, top site by volume, and the single
most important number-backed finding.

## Top Insights
Each insight must state the specific numbers behind it.

## Recommended Actions
Each action must reference the specific page(s) or metric that justifies it.
"""

    if st.button("Generate Brief"):
        if not api_key:
            st.error(f"Enter your {provider} API key in the sidebar first.")
        else:
            with st.spinner("Analyzing..."):
                try:
                    if provider == "Gemini":
                        from google import genai
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt,
                        )
                        brief = response.text
                    else:
                        from openai import OpenAI
                        client = OpenAI(api_key=api_key)
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                        )
                        brief = response.choices[0].message.content
                except Exception as e:
                    st.error(f"Request failed: {e}")
                    brief = None
            if brief:
                st.markdown(brief)