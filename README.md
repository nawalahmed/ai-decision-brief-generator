# AI Decision Brief Generator

A Streamlit app that turns a raw web analytics CSV export into a data-grounded
decision brief, using Gemini or OpenAI.

## Why this approach

Most LLM-generated summaries read like this: *"traffic is concentrated on a
small number of pages"* — true, but useless, because it names no page and no
number.

This app avoids that by splitting the work into two stages instead of one:

1. **Compute first.** Pandas calculates the real numbers up front — traffic
   share by page and by site, long-tail concentration, bounce-rate outliers,
   and anomaly flags (e.g. pages where view counts vastly exceed unique
   visitors, suggesting bot traffic or embedded widgets rather than genuine
   engagement).
2. **Summarize second.** Only those computed numbers are passed into the
   prompt. The model's job is to write clear prose around numbers that are
   already correct — not to estimate them from scratch, which is where most
   AI-generated reports go vague or get facts wrong.

Charts are rendered directly from the pandas output (Plotly), not from the
LLM, so they're accurate and don't depend on the API call succeeding.

## Bring your own API key

Rather than hardcoding a single provider's key into the app, the sidebar lets
each user pick their model (Gemini or OpenAI) and enter their own API key.
The key is used only for that session's request and is never stored, logged,
or written to disk — this keeps the deployed demo from depending on (or
draining) the developer's own quota when someone else tries it.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install streamlit pandas plotly google-genai openai
```

Get a free Gemini key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
(no billing required for the free tier), or an OpenAI key at
[platform.openai.com/api-keys](https://platform.openai.com/api-keys).

No `secrets.toml` or config file is needed — you'll enter your key directly
in the app's sidebar each time you run it.

## Run

```bash
python3 -m streamlit run app.py
```

In the sidebar, choose a provider and paste in your API key. Then upload a
CSV with columns: `WEBSITE, YEAR, PAGE PATH, PAGE URL, PAGE VIEWS,
UNIQUE VIEWS, AVERAGE TIME ON PAGE (SECONDS), ENTRANCES, BOUNCE RATE (%),
EXIT RATE (%)`, and click **Generate Brief**.

SAMPLE CSV FILE TO UPLOAD CAN BE FOUND HERE: https://data.brla.gov/api/v3/views/n9u7-h9i7/export.csv?accessType=DOWNLOAD


## What it outputs

- Two charts: top 10 pages by page views, and top 10 pages by bounce rate
  (filtered to pages with meaningful traffic, so low-volume noise doesn't
  dominate the ranking).
- A written brief with an Executive Summary, Top Insights, and Recommended
  Actions — every claim traceable to a specific page and number.