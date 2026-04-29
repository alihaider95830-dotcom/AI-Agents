# Twitter/X Launch Thread

Tweet 1 (the hook):
I spent 3 hours writing a market research report last month.

So I spent 3 weeks building something that does it in 90 seconds.

Introducing Studio 🧵

Tweet 2 (the problem):
Market research is painful:

- Find sources (30 min)
- Read and summarise them (60 min)
- Write a structured report (60 min)
- Fact-check your own work (30 min)

That's 3 hours of work that follows the same pattern every time. Patterns are automatable.

Tweet 3 (the solution):
Studio uses 4 AI agents, each with one job:

🔍 Researcher - searches 12 live sources
📋 Planner - builds the outline
✍️ Writer - drafts the report
✅ QA - fact-checks every claim

They run in sequence. You get a PDF.

Tweet 4 (the tech):
The fun engineering part:

Agents run in a Celery background worker.

Each agent publishes progress events to Redis pub/sub.

A FastAPI SSE endpoint subscribes and streams events to the browser in real time.

The user watches their report get written, agent by agent.

Tweet 5 (the CTA):
Free plan: 2 reports/month, no credit card.

Try it -> yourdomain.com

Would love your feedback - what topics should I test it on?
