r"""Chapter 39 - Machine learning and neural networks: from data to trained model."""

CHAPTER = r"""<h2>1. What Machine Learning Actually Is</h2>

<p>Traditional programming: rules + data -&gt; answers. Machine learning:
answers + data -&gt; rules. You define a loss (how wrong the model is) and an
optimiser that adjusts the parameters to reduce it. That is the whole
idea; everything else is variants.</p>

<table>
<tr><th>Type</th><th>You give it</th><th>It learns</th><th>Examples</th></tr>
<tr><td>Supervised - regression</td><td>Inputs + continuous labels</td><td>A number</td><td>House price from size/location</td></tr>
<tr><td>Supervised - classification</td><td>Inputs + class labels</td><td>A category</td><td>Spam or not spam, fraud or legit</td></tr>
<tr><td>Unsupervised</td><td>Inputs only</td><td>Structure</td><td>Customer segments, anomaly clusters</td></tr>
<tr><td>Reinforcement</td><td>Rewards from an environment</td><td>A policy</td><td>Game playing, robotics, tuning</td></tr>
<tr><td>Self-supervised</td><td>Raw data, labels generated from it</td><td>Representations</td><td>Next-word prediction = how LLMs train</td></tr>
</table>

<p><strong>Memory trick:</strong> does each row have the right answer
attached? Supervised. No answers? Unsupervised. A reward signal over time?
Reinforcement.</p>

<h2>2. The Standard Supervised Workflow</h2>

<pre>1. Collect + clean      missing values, duplicates, wrong types, leakage
2. Explore (EDA)        distributions, class balance, correlations
3. Split                train (70%) / validation (15%) / test (15%)
                        NEVER let test data influence any decision
4. Features             encode categories, scale numerics, text -&gt; vectors
5. Train                fit the model on train, evaluate on validation
6. Tune                 try models/hyperparameters on validation only
7. Final check          ONE run on the held-out test set
8. Ship + monitor       data drift and metric decay in production

from sklearn.model_selection import train_test_split
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                          stratify=y, random_state=42)
</pre>

<h2>3. Classic Models And When To Use Them</h2>

<table>
<tr><th>Model</th><th>Good at</th><th>Watch out for</th></tr>
<tr><td>Linear / logistic regression</td><td>Baseline, interpretability (coefficients = importance)</td><td>Assumes linear relationships</td></tr>
<tr><td>Decision tree</td><td>Rules you can explain to a manager</td><td>Overfits unless pruned/depth-limited</td></tr>
<tr><td>Random forest / XGBoost</td><td>Tabular data - usually the best default (wins Kaggle tabular)</td><td>Many trees = slower inference, needs tuning</td></tr>
<tr><td>k-NN</td><td>Small data, no training phase</td><td>Predicts slowly as data grows; sensitive to scaling</td></tr>
<tr><td>SVM</td><td>High-dimensional, small datasets (text)</td><td>Does not scale to huge data without kernels</td></tr>
<tr><td>K-means / DBSCAN</td><td>Segmentation, anomaly hints</td><td>You must choose k; density assumptions</td></tr>
</table>

<pre>from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X_tr, y_tr)
pred = model.predict(X_te)
print(classification_report(y_te, pred))
print(confusion_matrix(y_te, pred))
# Feature importance tells you what actually drives the decision:
for name, imp in sorted(zip(X.columns, model.feature_importances_),
                        key=lambda kv: -kv[1])[:10]:
    print(f"{name:24s} {imp:.3f}")
</pre>

<h2>4. Metrics That Matter</h2>

<table>
<tr><th>Metric</th><th>Question</th><th>Formula intuition</th></tr>
<tr><td>Accuracy</td><td>Overall right?</td><td>Misleading on 99% imbalanced data</td></tr>
<tr><td>Precision</td><td>When it says yes, is it right?</td><td>TP / (TP + FP) - spam filter marking real mail as spam</td></tr>
<tr><td>Recall</td><td>Did it catch all the yeses?</td><td>TP / (TP + FN) - fraud/medical: missing a positive is costly</td></tr>
<tr><td>F1</td><td>Balance of the two</td><td>Harmonic mean - use when classes are imbalanced</td></tr>
<tr><td>ROC-AUC</td><td>Ranking quality across thresholds</td><td>0.5 = random, 1.0 = perfect</td></tr>
<tr><td>MAE / RMSE</td><td>How far off are predictions?</td><td>Regression; RMSE punishes big misses</td></tr>
</table>

<p><strong>Memory trick:</strong> pick the metric from the COST of errors:
missing fraud (recall) vs annoying customers with false alarms (precision).
Decide before you train.</p>

<h2>5. Overfitting And How To Fight It</h2>

<pre>Overfit = memorised the training data, fails on new data
  signs:  train score 0.99, validation 0.72, gap growing with model size
Underfit = too simple to capture the pattern
  signs:  both scores poor; adding data or features barely helps

Fixes, in order of effort:
  1. More data (the most reliable fix)
  2. Regularisation - L1 (lasso, sparsity), L2 (ridge, shrinkage)
  3. Dropout (neural nets), early stopping on validation loss
  4. Simpler model / fewer features / pruning
  5. Cross-validation: k=5 folds - train 5 times, average, trust the spread

from sklearn.model_selection import cross_val_score
print(cross_val_score(model, X, y, cv=5, scoring="f1").mean())

# Data leakage checklist: was any future info, target-derived value, or
# test-set statistic present during training? Then your score is a lie.
</pre>

<h2>6. Neural Networks From Scratch (Conceptually)</h2>

<pre>neuron:  output = activation( dot(weights, inputs) + bias )
network: layers of neurons; each layer learns features of the layer below
         input -&gt; [hidden 1] -&gt; [hidden 2] -&gt; output

training loop (the same for EVERY network):
1. forward pass     predictions from current weights
2. loss             compare with truth (cross-entropy, MSE)
3. backward pass    backpropagation: gradient of loss wrt each weight
4. update           weights -= learning_rate * gradient   (SGD/Adam)
   repeat thousands of times over mini-batches

activation choices:
  ReLU (default hidden), sigmoid/softmax (output for probabilities),
  tanh (older hidden layers)
optimisers: SGD, Adam (adaptive - the default), AdamW (weight decay)

import torch.nn as nn
model = nn.Sequential(
    nn.Linear(20, 64), nn.ReLU(), nn.Dropout(0.2),
    nn.Linear(64, 32), nn.ReLU(),
    nn.Linear(32, 2), nn.Softmax(dim=1))
loss_fn = nn.CrossEntropyLoss()
optim   = torch.optim.Adam(model.parameters(), lr=1e-3)
for Xb, yb in loader:                 # mini-batch loop
    pred = model(Xb)
    loss = loss_fn(pred, yb)
    optim.zero_grad(); loss.backward(); optim.step()   # the four-line ritual
</pre>

<table>
<tr><th>Architecture</th><th>Shape</th><th>Best for</th></tr>
<tr><td>Feed-forward (MLP)</td><td>Dense layers</td><td>Structured/tabular inputs</td></tr>
<tr><td>CNN</td><td>Convolution + pooling kernels sliding over grids</td><td>Images, audio spectrograms - local patterns</td></tr>
<tr><td>RNN / LSTM</td><td>Hidden state carried through a sequence</td><td>Time series, older NLP - struggles with long range</td></tr>
<tr><td>Transformer</td><td>Self-attention over the whole sequence at once</td><td>NLP, now vision/audio too - the LLM backbone</td></tr>
<tr><td>Autoencoder</td><td>Compress then reconstruct</td><td>Anomaly detection, denoising, embeddings</td></tr>
<tr><td>GAN / Diffusion</td><td>Generator vs discriminator / iterative denoising</td><td>Image generation (Stable Diffusion, DALL-E)</td></tr>
</table>

<h2>7. MLOps - Keeping Models Alive</h2>

<pre>Training:   notebooks -&gt; versioned pipeline (MLflow, Kubeflow)
Data:       version the dataset (DVC), validate schema (great expectations)
Registry:   stage -&gt; production with the metrics attached (MLflow registry)
Serving:    REST/gRPC endpoint, or batch job; pin model version, canary 5%
Monitor:    data drift (input distribution shifted), concept drift
            (input-&gt;output relation shifted), latency, cost
Retrain:    scheduled or drift-triggered, never silently online-learning

Drift alarms you actually need:
  - input distribution PSI/KL over threshold
  - proxy metric in production (e.g. click-through) dropping vs holdout
  - latency p95 and error rate of the endpoint
</pre>

<h2>8. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Data</td><td>Titanic.csv from a tutorial</td><td>Pipeline with validation, PII handling, versioned snapshots</td></tr>
<tr><td>Evaluation</td><td>Accuracy on one split</td><td>Right metric for the cost, cross-validated, business KPI A/B tested</td></tr>
<tr><td>Model</td><td>Best notebook score</td><td>Versioned, reproducible, with model card and owner</td></tr>
<tr><td>Serving</td><td>predict() in the notebook</td><td>Batched endpoint, timeout, fallback to rules, load tested</td></tr>
<tr><td>After launch</td><td>Done</td><td>Drift monitoring, alerting, retraining policy, rollback to last good</td></tr>
</table>

<h2>9. Key Takeaways</h2>
<ul>
<li>ML inverts programming: data + answers -&gt; rules, driven by a loss
function and an optimiser.</li>
<li>Train/val/test discipline and leakage checks matter more than model
choice.</li>
<li>XGBoost wins tabular; neural nets win perceptual data (images, speech,
text).</li>
<li>Pick the metric from the cost of mistakes before training.</li>
<li>Backprop + gradient descent is one four-line ritual repeated
everywhere.</li>
<li>Production ML is mostly data pipelines and monitoring, not
modelling.</li>
</ul>

<p><strong>Exercise:</strong> take any CSV with a binary label, run
train/test split, fit logistic regression and random forest, print both
classification reports, and explain in one sentence why the better F1 one
can still be the wrong model for the business.</p>
"""