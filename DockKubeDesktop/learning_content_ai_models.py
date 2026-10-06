r"""Chapter 40 - AI models: transformers, attention, and every model family explained."""

CHAPTER = r"""<h2>1. The One Idea Behind Modern AI: Tokens And Prediction</h2>

<p>Every large language model is doing one thing: given a sequence of
tokens, predict the next token - a probability distribution over the whole
vocabulary. Chat is sampling from that distribution billions of times.</p>

<pre>Your text  -&gt; tokenizer  -&gt; [5023, 891, 17, 4471, ...]  -&gt; model  -&gt; P(next token)
                              "The cat sat on the"              sample -&gt; " mat"

BPE tokenizer: merges frequent character pairs into tokens, so vocabulary
is ~50k words/pieces - unknown words are spelled from subwords.
Context window: how many tokens the model can attend to at once
  (4k -&gt; 128k -&gt; 1M). Everything beyond it is invisible to the model.
</pre>

<h2>2. The Transformer And Self-Attention</h2>

<p>Attention answers: <em>for each token, which other tokens matter most
right now?</em> Every token emits a Query (what I seek), a Key (what I
offer), and a Value (what I will pass on).</p>

<pre>Attention(Q,K,V) = softmax( Q * K^T / sqrt(d_k) ) * V

"The bank raised the river bank"
 token "bank" #2 attends strongly to "river" - context resolves meaning

Multi-head: several attention patterns in parallel (syntax here, coreference
there), concatenated and projected. Stack N of these blocks (GPT: 96+)
with feed-forward layers between them - that is a transformer.

Why it beat RNNs: full parallelism in training (GPU friendly) and direct
long-range connections - token 1 can influence token 4000 in one step.
</pre>

<h2>3. How A Model Gets Smart: Training Stages</h2>

<table>
<tr><th>Stage</th><th>What happens</th><th>Data</th><th>Cost</th></tr>
<tr><td>Pretraining</td><td>Next-token prediction on the internet</td><td>Tens of TB of text</td><td>Thousands of GPUs, millions of dollars</td></tr>
<tr><td>SFT (fine-tuning)</td><td>Learn to follow instructions / chat format</td><td>~10k-1M high-quality Q&amp;A</td><td>Dozens of GPUs</td></tr>
<tr><td>RLHF / DPO</td><td>Align with human preference: helpful, harmless, honest</td><td>Preference rankings</td><td>Reinforcement loop</td></tr>
<tr><td>Quantisation</td><td>Shrink weights (fp16 -&gt; int8 -&gt; int4)</td><td>Same model</td><td>Cheap - enables local running</td></tr>
<tr><td>Distillation</td><td>Train a small model to mimic a big one</td><td>Big-model outputs</td><td>Moderate</td></tr>
<tr><td>LoRA / QLoRA</td><td>Train small adapter matrices, freeze the base</td><td>Your dataset</td><td>1 GPU feasible</td></tr>
</table>

<h2>4. The Model Families</h2>

<table>
<tr><th>Family</th><th>How it works</th><th>Representatives</th><th>Use for</th></tr>
<tr><td>Decoder-only LLM</td><td>Predict next token, bidirectional-free (causal)</td><td>GPT-4/4o, Llama 3, Mistral, Qwen, DeepSeek</td><td>Chat, code, agents, RAG</td></tr>
<tr><td>Encoder-only</td><td>Bidirectional understanding, no generation</td><td>BERT, RoBERTa, DeBERTa</td><td>Classification, search ranking, NER</td></tr>
<tr><td>Encoder-decoder</td><td>Read whole input, then generate output</td><td>T5, BART, Flan-T5</td><td>Translation, summarisation</td></tr>
<tr><td>Multimodal</td><td>Attention over images + text (+audio) together</td><td>GPT-4o, Gemini, Claude 3.x, LLaVA</td><td>Vision QA, document understanding</td></tr>
<tr><td>Diffusion</td><td>Iteratively denoise random pixels into an image</td><td>Stable Diffusion, DALL-E, Midjourney</td><td>Image generation/editing</td></tr>
<tr><td>Speech</td><td>Spectrograms -&gt; text and back</td><td>Whisper, ElevenLabs</td><td>Transcription, TTS</td></tr>
<tr><td>Embedding models</td><td>Text -&gt; vector, cosine similarity = meaning</td><td>OpenAI text-embedding-3, bge, e5, Cohere</td><td>RAG, search, clustering</td></tr>
<tr><td>Rerankers</td><td>Score query-document pairs precisely</td><td>Cohere rerank, bge-reranker</td><td>Improve RAG retrieval top-k</td></tr>
<tr><td>Small / on-device</td><td>Quantised, runs locally</td><td>Llama 3.2 3B, Phi-3, Gemma 2B, GPT-OSS-mini</td><td>Offline, cheap, private</td></tr>
</table>

<h2>5. Vision And Sequence Models Before Transformers</h2>

<table>
<tr><th>Model</th><th>Mechanism</th><th>Where it still lives</th></tr>
<tr><td>CNN</td><td>Convolution kernels detect edges/textures then shapes</td><td>Image classification, medical imaging, real-time vision</td></tr>
<tr><td>RNN / LSTM / GRU</td><td>Hidden state walks the sequence step by step</td><td>Legacy time-series; replaced by Transformers</td></tr>
<tr><td>Autoencoder / VAE</td><td>Compress then reconstruct; sample the latent space</td><td>Anomaly detection, compression</td></tr>
<tr><td>GAN</td><td>Generator fools a discriminator</td><td>Older image synthesis, data augmentation</td></tr>
<tr><td>Tree models</td><td>Gradient-boosted decision trees</td><td>Tabular data - still usually unbeaten</td></tr>
</table>

<h2>6. Inference: What You Pay For</h2>

<pre>latency  = queue + prefill (processing your prompt) + decode (tokens out)
cost     = input tokens * rate_in  +  output tokens * rate_out
           (output tokens are usually 3-4x the price - be terse)
context  = prompt + history + retrieved docs; all billed every call

Levers:
  - trim history / summarise old turns
  - smaller model for easy steps, big model for hard steps (routing)
  - cache: prompt caching (OpenAI/Anthropic) and semantic caching
  - stream tokens so the user sees first bytes instantly (TTFB)
  - batch non-urgent calls (batch APIs are ~50% cheaper)
  - temperature: 0 for extraction/code, 0.7+ for brainstorming
</pre>

<p><strong>Memory trick:</strong> models do not "look things up" - they
regurgitate patterns from training. That is why they hallucinate citations
and why RAG (Chapter 41) exists: put real documents in the context and make
the model quote them.</p>

<h2>7. Choosing A Model In Practice</h2>

<pre>Need                         Look at
-----                        --------
Just starting / cheap        GPT-4o-mini class or Llama 3.1 8B local
Hard reasoning / code        Frontier: GPT-4.1/5 class, Claude Opus/Sonnet,
                             Gemini Pro - benchmark on YOUR tasks
Fully private / offline       Llama/Qwen/Gemma 3-14B quantised via ollama
Vision + text                GPT-4o, Gemini, Claude
RAG retrieval                Dedicated embedding model + reranker
Classification at scale      Fine-tuned small encoder (BERT) - beats LLMs
                             on cost and latency
Speech                       Whisper large-v3 (ASR), TTS vendor or Piper

Evaluation beats vibes: build a 50-200 case eval set from your real
questions, run every candidate model through it, compare accuracy AND cost
AND latency.
</pre>

<h2>8. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Where it runs</td><td>Chat UI in a browser</td><td>API from your backend, keys in a secret manager, no client-side keys</td></tr>
<tr><td>Prompt</td><td>Same chat window, hand-typed</td><td>Versioned templates, evals in CI, A/B on prompts</td></tr>
<tr><td>Hallucination</td><td>Fun anecdote</td><td>RAG + citation checks + refusal policy + human review for high stakes</td></tr>
<tr><td>Cost</td><td>Free tier</td><td>Budgets, per-feature cost tracking, cache and route</td></tr>
<tr><td>Data</td><td>Paste anything</td><td>PII redaction, retention policy, regional endpoints</td></tr>
</table>

<h2>9. Key Takeaways</h2>
<ul>
<li>LLMs predict the next token with attention - everything else is
training stages and sampling settings.</li>
<li>Pretrain -&gt; SFT -&gt; RLHF -&gt; quantise: where the capability and the cost
come from.</li>
<li>Decoder-only for generation, encoder-only for classification, enc-dec
for transduction; diffusion for images.</li>
<li>Context window, latency, price per 1M tokens - the three numbers to
check before choosing a model.</li>
<li>Benchmark on YOUR eval set; vibes are not evaluation.</li>
<li>Models generate plausible text - ground them with RAG before trusting
their facts.</li>
</ul>

<p><strong>Exercise:</strong> take five real questions from your domain, run
them through two different models at temperature 0, and build a tiny eval
sheet - accuracy, latency, cost per answer. That sheet is your model
selection process.</p>
"""