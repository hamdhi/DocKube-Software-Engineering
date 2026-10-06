r"""Chapter 30 - Sending email from FastAPI: SMTP, templates and the mail APIs."""

CHAPTER = r"""<h2>1. The Three Ways To Send Mail</h2>

<table>
<tr><th>Way</th><th>How</th><th>Use when</th></tr>
<tr><td>SMTP relay</td><td>Your code speaks SMTP to a server (yours or a provider's)</td><td>You already have mail infrastructure</td></tr>
<tr><td>HTTP mail API</td><td>POST JSON to SendGrid/Mailgun/Resend/etc with an API key</td><td>The default today: better deliverability, dashboards, webhooks</td></tr>
<tr><td>Local sendmail</td><td>Hand the message to /usr/sbin/sendmail</td><td>Containers and legacy boxes, rarely on Windows</td></tr>
</table>

<p><strong>Memory trick:</strong> SMTP is how servers talk to each other;
mail APIs are how YOUR app talks to a provider that then speaks SMTP for you.
Home ISPs and cloud providers block port 25 - you almost always need a
provider anyway.</p>

<h2>2. Sending Over SMTP - Standard Library</h2>

<pre>import smtplib
from email.message import EmailMessage
from email.utils import make_msgid

def send_welcome(to: str, name: str):
    msg = EmailMessage()
    msg["From"] = "DocKube &lt;no-reply@dockeybe.dev&gt;"
    msg["To"] = to
    msg["Subject"] = "Welcome to DocKube"
    msg.set_content(f"Hi {name},\n\nYour account is ready.\n-- The team")
    html = f"&lt;h1&gt;Welcome, {name}!&lt;/h1&gt;"
    html += "&lt;p&gt;Your account is ready.&lt;/p&gt;"
    msg.add_alternative(html, subtype="html")

    # host, port, username, password, TLS
    with smtplib.SMTP_SSL("smtp.example.com", 465, timeout=10) as smtp:
        smtp.login("apikey-or-user", "secret")
        smtp.send_message(msg)

# StartTLS variant: smtplib.SMTP(host, 587) then smtp.starttls() then login.
</pre>

<pre># Async version for FastAPI - blocking SMTP in a coroutine freezes the loop
import asyncio
from concurrent.futures import ThreadPoolExecutor
_executor = ThreadPoolExecutor(max_workers=4)

@app.post("/notifications/welcome")
async def welcome(to: EmailStr):
    # run_in_executor wraps the blocking send like any other thread task
    await asyncio.get_running_loop().run_in_executor(
        _executor, send_welcome, to, "friend")
    return {"queued": True}
</pre>

<h2>3. HTML Mail, Templates And Attachments</h2>

<pre>from email.message import EmailMessage

def send_invoice(to: str, pdf: bytes, rows: list):
    msg = EmailMessage()
    msg["Subject"] = "Your invoice"
    # Inline styles only: Gmail and friends strip &lt;style&gt; blocks.
    rows_html = "".join(
        f"&lt;tr&gt;&lt;td&gt;{r['item']}&lt;/td&gt;&lt;td align='right'&gt;{r['price']:.2f}&lt;/td&gt;&lt;/tr&gt;"
        for r in rows)
    msg.add_alternative(
        f"&lt;table cellpadding='6' style='border-collapse:collapse'&gt;{rows_html}&lt;/table&gt;",
        subtype="html")
    msg.add_attachment(pdf, maintype="application", subtype="pdf",
                       filename="invoice.pdf")
    return msg

# Templates: keep the subject/body in files (Jinja2) so writers can edit
# them without a deploy: env.render("welcome", name=name)
</pre>

<table>
<tr><th>Rule</th><th>Why</th></tr>
<tr><td>multipart/alternative (text + html)</td><td>Some clients only render text</td></tr>
<tr><td>Inline CSS</td><td>Major clients strip style tags</td></tr>
<tr><td>One-click unsubscribe + List-Unsubscribe header</td><td>Spam law (CAN-SPAM, GDPR) and inbox placement</td></tr>
<tr><td>Never interpolate user input into raw HTML</td><td>HTML injection / phishing via your domain</td></tr>
<tr><td>Send async and return 202</td><td>A slow SMTP server must not hold the request open</td></tr>
</table>
<h2>4. The Mail APIs Compared</h2>

<table>
<tr><th>Provider</th><th>How you call it</th><th>Free tier</th><th>Known for</th></tr>
<tr><td>SMTP + any relay</td><td>smtplib to port 465/587</td><td>Varies</td><td>No dashboard, no webhooks</td></tr>
<tr><td>SendGrid</td><td>POST /v3/mail/send + Bearer key</td><td>100 emails/day</td><td>Templates, analytics, industry default</td></tr>
<tr><td>Mailgun</td><td>POST /v3/.../messages (API or SMTP)</td><td>1000/month (trial)</td><td>Developer ergonomics, receiving mail</td></tr>
<tr><td>AWS SES</td><td>POST via SigV4, or SMTP creds</td><td>3000/month from EC2</td><td>Cheapest at scale, AWS-native</td></tr>
<tr><td>Postmark</td><td>POST /email</td><td>100/month (trial)</td><td>Transactional speed and deliverability</td></tr>
<tr><td>Resend</td><td>POST /emails + React Email templates</td><td>3000/month</td><td>Modern DX, loved by Next.js apps</td></tr>
<tr><td>Brevo (ex-Sendinblue)</td><td>POST /v3/smtp/email</td><td>300/day</td><td>Cheap bulk + marketing</td></tr>
<tr><td>SMTP2GO</td><td>API or SMTP</td><td>1000/month</td><td>Deliverability reporting</td></tr>
</table>

<h2>5. Calling A Mail API From FastAPI</h2>

<pre># pip install httpx
import httpx
from fastapi import BackgroundTasks

SENDGRID_KEY = settings.sendgrid_key
SENDGRID_FROM = "DocKube &lt;no-reply@dockeybe.dev&gt;"

async def sendgrid_send(to: str, subject: str, html: str):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {SENDGRID_KEY}"},
            json={
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": "no-reply@dockeybe.dev"},
                "subject": subject,
                "content": [{"type": "text/html", "value": html}],
            },
        )
        r.raise_for_status()          # 202 Accepted means queued
        return r.status_code

@app.post("/notifications/reset")
async def reset_email(body: ResetIn, tasks: BackgroundTasks):
    # Fire after the response: the user never waits on a mail provider.
    tasks.add_task(sendgrid_send, body.email,
                   "Reset your password", render_reset(body.token))
    return {"queued": True}          # always 202, never leak if an account exists
</pre>

<table>
<tr><th>Concept</th><th>Meaning</th></tr>
<tr><td>Transactional vs bulk</td><td>Password resets (immediate, low volume) vs campaigns (batched, throttled)</td></tr>
<tr><td>SPF</td><td>DNS record listing which servers may send as your domain</td></tr>
<tr><td>DKIM</td><td>Cryptographic signature on the message, verified against DNS</td></tr>
<tr><td>DMARC</td><td>Policy telling receivers what to do when SPF/DKIM fail (none -&gt; quarantine -&gt; reject)</td></tr>
<tr><td>Webhooks</td><td>Provider POSTs delivery, bounce and open events back to your endpoint</td></tr>
<tr><td>Suppression list</td><td>Bounced or complained addresses you must stop mailing</td></tr>
</table>

<p><strong>Memory trick:</strong> without SPF + DKIM + DMARC your perfect
email lands in spam. Set the three records before you send your first
message, then warm up the volume gradually.</p>

<h2>6. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Provider</td><td>Mailtrap / Ethereal (fake inbox)</td><td>SendGrid or SES with dedicated IP warm-up</td></tr>
<tr><td>Sending</td><td>Inline in the request - slow, and retried twice = two mails</td><td>Background task or queue with idempotency key + retries</td></tr>
<tr><td>Failures</td><td>Exception bubbles to the user</td><td>Queued, retried with backoff, dead-lettered, alerted</td></tr>
<tr><td>Secrets</td><td>Key in the source</td><td>Environment / secret manager, scoped, rotatable</td></tr>
<tr><td>Tracking</td><td>None</td><td>Webhooks for delivered/bounced/complained, suppression honoured</td></tr>
<tr><td>Content</td><td>f-strings in code</td><td>Versioned templates with a preview and review</td></tr>
</table>

<h2>7. Key Takeaways</h2>
<ul>
<li>SMTP for server-to-server, HTTP mail APIs for your app - port 25 is
blocked almost everywhere.</li>
<li>Never block the event loop on SMTP: BackgroundTasks or a thread
executor.</li>
<li>multipart text + HTML, inline styles, unsubscribe header, escape user
input.</li>
<li>SPF, DKIM and DMARC are the difference between the inbox and the spam
folder.</li>
<li>Send asynchronously, retry idempotently, honour bounces.</li>
</ul>

<p><strong>Exercise:</strong> wire a /notifications endpoint that queues a
SendGrid (or Mailtrap) send with BackgroundTasks, then check the provider
dashboard shows a 202 and a delivered event.</p>
"""