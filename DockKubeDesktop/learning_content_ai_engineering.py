r"""Chapter 41 - AI engineering: prompting, RAG, agents, evals and shipping LLM apps."""

CHAPTER = r"""<h2>1. Prompt Engineering Is Software Design</h2>

<table>
<tr><th>Technique</th><th>What it is</th><th>Example</th></tr>
<tr><td>Role (system prompt)</td><td>Fixes persona, scope and rules for every call</td><td>You are a support assistant for DocKube. Only answer from the provided context.</td></tr>
<tr><td>Structured output</td><td>Schema the reply must obey (JSON mode / tool call)</td><td>{"verdict": ..., "confidence": ..., "evidence": [...]}</td></tr>
<tr><td>Few-shot</td><td>2-5 worked examples = fastest quality boost</td><td>Input -&gt; perfect output, repeated in the prompt</td></tr>
<tr><td>Step-by-step</td><td>Ask for reasoning before the answer for hard problems</td><td>Think through it, then output only the final JSON</td></tr>
<tr><td>Constraints</td><td>Explicit don\'ts and limits beat vibes</td><td>Max 3 bullets. Never invent citations. If unsure, say "not in context".</td></tr>
<tr><td>Separation</td><td>Instructions vs data in distinct blocks</td><td>&lt;&lt;CONTEXT&gt;&gt; ... &lt;&lt;/CONTEXT&gt;&gt; then the question</td></tr>
</table>

<pre>SYSTEM: You extract invoices. Rules: return JSON only, no markdown,
missing field = null, dates ISO-8601. If the document is not an invoice,
return {"error": "not_an_invoice"}.

USER: Extract from this text: "Invoice #8841, 3 Jan 2026, ACME Ltd, total 420.00"

# Version your prompts like code: prompts/invoice_v3.md in git, eval suite
# runs on every change (see section 5). Prompt changes ARE releases.
</pre>

<h2>2. Function Calling And Tool Use</h2>

<pre>import json, httpx
from openai import OpenAI

client = OpenAI()
TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_order_status",
        "description": "Look up a customer order by id",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
}]

resp = client.chat.completions.create(
    model="gpt-4o-mini", messages=messages, tools=TOOLS, temperature=0)
msg = resp.choices[0].message
if msg.tool_calls:                       # the model ASKS you to run something
    for call in msg.tool_calls:
        args = json.loads(call.function.arguments)
        result = orders_api(args["order_id"])   # YOUR code does the real work
        messages.append({"role": "tool", "tool_call_id": call.id,
                         "content": json.dumps(result)})
    # feed results back - the model writes the natural-language answer
</pre>

<p><strong>Memory trick:</strong> the model never touches your system - it
calls <em>tools</em> and your code executes them. That boundary is where you
put auth, validation and rate limits.</p>

<h2>3. RAG - Retrieval Augmented Generation</h2>

<p>LLMs do not know your docs, your policies, or last week's changes.
<strong>RAG</strong> retrieves the relevant passages and puts them in the
prompt, so answers are grounded and citable.</p>

<pre>INGEST (offline)                          QUERY (online)
1. load documents (pdf, md, html, tickets)
2. chunk: 300-800 tokens, 10-20% overlap
   (respect headings; never split mid-table)
3. embed each chunk -&gt; vector            1. embed the question
4. store {vector, text, source, meta}    2. top-k similarity search (k=5..20)
   in a vector DB                        3. optional reranker on top 20 -&gt; top 5
                                          4. build prompt: context + question
                                          5. generate with citations
                                          6. return answer + sources
</pre>

<pre># Full minimal RAG in Python (pip install openai chromadb tiktoken)
from openai import OpenAI
import chromadb

client = OpenAI()
DB = chromadb.PersistentClient(path="./vector_store")
col = DB.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})

def chunks_of(path: str, size: int = 700, overlap: int = 100):
    text = open(path, encoding="utf-8").read()
    return [text[i:i + size] for i in range(0, len(text), size - overlap)]

def ingest(path: str):
    for n, chunk in enumerate(chunks_of(path)):
        vec = client.embeddings.create(model="text-embedding-3-small",
                                       input=chunk).data[0].embedding
        col.add(ids=[f"{path}#{n}"], embeddings=[vec],
                documents=[chunk], metadatas=[{"source": path, "chunk": n}])

def rag(question: str, k: int = 6) -&gt; dict:
    qvec = client.embeddings.create(model="text-embedding-3-small",
                                    input=question).data[0].embedding
    hits = col.query(query_embeddings=[qvec], n_results=k)
    context = "\n\n---\n\n".join(hits["documents"][0])
    sources = [m["source"] for m in hits["metadatas"][0]]

    out = client.chat.completions.create(
        model="gpt-4o-mini", temperature=0,
        messages=[
            {"role": "system", "content":
             "Answer ONLY from the context. Quote the source filename after "
             "each claim. If the context does not cover it, say "
             "'not in context'."},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\nQ: {question}"},
        ])
    return {"answer": out.choices[0].message.content,
            "sources": sorted(set(sources))}
</pre>

<table>
<tr><th>Vector DB</th><th>Shape</th><th>Choose when</th></tr>
<tr><td>Chroma / FAISS</td><td>Embedded library</td><td>Local, single app, millions of vectors</td></tr>
<tr><td>pgvector</td><td>Postgres extension</td><td>You already run Postgres - one system less</td></tr>
<tr><td>Qdrant / Milvus</td><td>Vector server</td><td>Large scale, filters, hybrid search</td></tr>
<tr><td>Pinecone / Weaviate cloud</td><td>Managed</td><td>No ops budget</td></tr>
<tr><td>Elasticsearch / OpenSearch</td><td>Keyword + vector hybrid</td><td>You need BM25 AND semantic together</td></tr>
</table>

<p><strong>Retrieval quality beats model quality.</strong> Fix in this order:
better chunking (headers, semantic), hybrid search (keyword + vector),
reranker, metadata filters, query rewriting - then worry about the LLM.</p>

<h2>4. Agents - Models With A Loop</h2>

<pre>plan  -&gt; choose tool  -&gt; execute  -&gt; observe result  -&gt; repeat until done

Rules that keep agents alive in production:
- max iterations (10) and a hard timeout - loops cost money
- every tool validated server-side (the model can pass ANY argument)
- idempotent tools: retries will happen
- keep a full trace of every step for debugging and billing
- prefer deterministic workflows; use agents only where steps cannot be known
</pre>
<h2>5. Evals - The Test Suite For LLM Features</h2>

<pre>Three layers, cheapest first:
1. PROMPT regression set   50-200 real cases with expected properties
   - deterministic (temperature 0), runs in CI on every prompt/model change
2. RAG retrieval metrics   hit@k, MRR, context precision - did the right
   chunks even reach the prompt?
3. LLM-as-judge            a big model scores style/consistency on a rubric
   (cheap for tone; never the sole judge of correctness)

# A tiny eval harness
import json, statistics

def run_eval(cases, prompt_fn, model="gpt-4o-mini"):
    rows = []
    for case in cases:
        got = prompt_fn(case["input"])             # temperature=0
        rows.append({
            "id": case["id"],
            "exact":  got.strip() == case["expected"].strip(),
            "contains": case["must_contain"].lower() in got.lower(),
            "output": got,
        })
    score = sum(r["exact"] or r["contains"] for r in rows) / len(rows)
    return score, rows                             # gate merges at e.g. &gt;= 0.9

# Regression case format:
{"id": "refund-3", "input": "Can I refund order 77?",
 "expected": "Refunds allowed within 30 days", "must_contain": "30 days"}
</pre>

<table>
<tr><th>Failure mode</th><th>Eval catches it</th><th>Fix</th></tr>
<tr><td>Answer changed after prompt edit</td><td>Regression set score drops</td><td>Revert or update cases deliberately</td></tr>
<tr><td>Wrong chunks retrieved</td><td>hit@k falls</td><td>Chunking, hybrid search, rerank</td></tr>
<tr><td>Format drift (markdown in JSON)</td><td>Schema validation fails</td><td>Structured outputs / tool calls</td></tr>
<tr><td>Hallucinated facts</td><td>Citation checks + judge</td><td>Stricter grounding prompt, refuse policy</td></tr>
<tr><td>Cost or latency regression</td><td>Token/latency dashboards</td><td>Shorter prompts, caching, routing</td></tr>
</table>

<h2>6. Guardrails, Safety And Privacy</h2>

<pre>Input side (before the model):
  - PII detection + redaction (names, cards, emails) before any external API
  - prompt-injection scan: user text is DATA, never instructions
    ("ignore previous instructions" must be neutralised by system-prompt
     separation + tool allow-lists)
  - allow-listed topics; jailbreak pattern matching

Output side (after the model):
  - schema validation (JSON, enums, lengths)
  - citation check: every claim must map to a retrieved chunk
  - toxicity / secret scanning (the model may echo training data)
  - never render model output as HTML/JS unescaped; never let it issue
    privileged actions without an approval step

Operational:
  - rate limits per user, budget caps per feature, kill switch
  - log inputs/outputs with retention limits; audit trail for tool calls
  - content policy + a human review queue for high-risk categories
</pre>

<p><strong>Memory trick:</strong> the model is the least trustworthy
component in the pipeline - validate everything that crosses its mouth, and
validate everything that enters it.</p>

<h2>7. Fine-Tune Or RAG Or Prompt? Decide In This Order</h2>

<table>
<tr><th>Situation</th><th>Right tool</th><th>Why</th></tr>
<tr><td>Model lacks a format or persona</td><td>Prompt + few-shot</td><td>Minutes of work, no data needed</td></tr>
<tr><td>Model lacks YOUR facts</td><td>RAG</td><td>Grounded, citable, updates without retraining</td></tr>
<tr><td>Model is right but slow/pricey</td><td>Distil/route: small model for easy cases</td><td>Cheapest lever is usually routing</td></tr>
<tr><td>Model must output a strict style/schema at scale</td><td>Fine-tune (SFT/LoRA)</td><td>Shorter prompts, consistent format, cheaper inference</td></tr>
<tr><td>Domain jargon, classification, code style</td><td>Fine-tune small model</td><td>100s-1000s of examples beat a big general model</td></tr>
<tr><td>Need knowledge freshness</td><td>RAG over the source, never fine-tune for facts</td><td>Fine-tuning bakes facts in untraceably</td></tr>
</table>

<h2>8. Shipping LLM Apps In FastAPI</h2>

<pre># app/routers/ai.py - streaming RAG endpoint
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json, asyncio

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/ask")
async def ask(body: AskIn, user = Depends(get_current_user),
              svc = Depends(get_rag_service)):
    await enforce_quota(user["sub"], cost=body)
    sources = await svc.retrieve(body.question, k=6)
    if not sources:
        return {"answer": "not in context", "sources": []}

    async def stream():
        # Server-Sent Events: first token in &lt;500ms, tokens as they arrive
        stream = await svc.client.chat.completions.create(
            model="gpt-4o-mini", temperature=0, stream=True,
            messages=build_messages(body.question, sources))
        async for event in stream:
            delta = event.choices[0].delta.content or ""
            yield f"data: {json.dumps({'t': delta})}\n\n"
        yield f"data: {json.dumps({'sources': [s.source for s in sources]})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

# Also wire: request-id middleware, per-user token budget in Redis,
# timeouts on the provider call, and a circuit breaker so a provider
# outage degrades to "classical search results" instead of a 500.
</pre>

<pre># What production LLM ops monitors (LLMOps):
metric                 alert when
-----                  ----------
p50/p95 latency        p95 &gt; 2s for streaming first token
tokens per request     +30% vs baseline (prompt bloat or injection)
cost per feature/day   budget burn rate
eval score             &lt; gate on each deploy (prompts ship like code)
refusal / no-answer %  rising = retrieval or policy broke
tool error rate        tool schema drift or upstream failure
groundedness (judge)   claims without supporting chunks
</pre>

<h2>9. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Prompt</td><td>Typed fresh in the playground</td><td>Versioned file, eval-gated, feature-flagged</td></tr>
<tr><td>Context</td><td>Paste the doc in by hand</td><td>Ingestion pipeline, chunk versioning, retrieval metrics</td></tr>
<tr><td>API key</td><td>In the script</td><td>Secret manager, per-service keys, spend limits</td></tr>
<tr><td>Output</td><td>Printed and trusted</td><td>Schema-validated, citation-checked, rate-limited, logged</td></tr>
<tr><td>Failure</td><td>Exception in the notebook</td><td>Timeout + fallback + circuit breaker + user-visible degraded mode</td></tr>
<tr><td>Data</td><td>Anything goes</td><td>Redaction, retention limits, regional endpoints, DPA with provider</td></tr>
</table>

<h2>10. Key Takeaways</h2>
<ul>
<li>Prompt = code: version it, test it, ship it behind flags.</li>
<li>Function calling is a boundary: the model proposes, your code disposes
(auth, validation, idempotency live on your side).</li>
<li>RAG grounds answers: chunk carefully, hybrid search + rerank, cite
everything; retrieval quality beats model choice.</li>
<li>Agents need iteration limits, validated tools and full traces -
prefer deterministic workflows where steps are known.</li>
<li>Eval sets in CI are the only thing that makes LLM changes safe.</li>
<li>Guardrails on both sides of the model; the model is untrusted in
both directions.</li>
</ul>

<p><strong>Exercise:</strong> build the ingest + query RAG pair from
section 3 over five of your own documents, then break retrieval on purpose
(wrong chunk size) and watch the eval score drop before you touch the
model.</p>
"""