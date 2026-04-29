# Hacker News Launch

## Title
Show HN: Studio - AI agent pipeline that writes market research reports

## Post body:

I built Studio, a multi-agent AI system that takes a topic and produces a structured market research report automatically.

The pipeline runs four agents sequentially:

1. Researcher - uses DuckDuckGo to find 8-12 sources, scrapes them with BeautifulSoup, chunks and embeds the content into a FAISS vector store
2. Planner - reads the research via vector similarity search, builds a structured outline
3. Writer - drafts each section pulling citations from FAISS
4. QA - cross-references claims against the source list

Stack: CrewAI for orchestration, LangChain for tools and embeddings, FastAPI + Celery + Redis for the backend, Next.js on the frontend, Railway for hosting.

The interesting engineering challenge was streaming agent progress to the frontend in real time while the crew runs in a Celery background worker. Solved it with Redis pub/sub and Server-Sent Events - each agent publishes progress events that the SSE endpoint forwards to the browser.

Happy to go deep on any part of the architecture.

Live: https://yourdomain.com
Free plan: 2 reports/month, no card required.
