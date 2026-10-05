"""Chapter index for the Learning Centre popup.

Each entry is ``(title, html)``. The popup renders these in order and shows
them in its sidebar.
"""

import learning_content_net1 as net1
import learning_content_net2 as net2
import learning_content_net3 as net3
import learning_content_net4 as net4
import learning_content_net5 as net5
import learning_content_net6 as net6
import learning_content_net7 as net7
import learning_content_linux as linux
import learning_content_se as se
import learning_content_sysadmin as sysadmin
import learning_content_agile as agile
import learning_content_aws as aws
import learning_content_delivery as delivery
import learning_content_devops as devops
import learning_content_security as security
import learning_content_firewall as firewall
import learning_content_diagrams as diagrams
import learning_content_database as database
import learning_content_observability as observability
import learning_content_sre as sre
import learning_content_cloud as cloud
import learning_content_fintech as fintech
import learning_content_business as business

CHAPTERS = [
    ("Networking Fundamentals", net1.CHAPTER),
    ("IP Addresses", net2.CHAPTER),
    ("Subnetting", net3.CHAPTER),
    ("Ports and Sockets", net4.CHAPTER),
    ("TCP vs UDP", net5.CHAPTER),
    ("Protocols: DNS, HTTP, SSH, TLS", net6.CHAPTER),
    ("Network Devices", net7.CHAPTER),
    ("Linux Command Line", linux.CHAPTER),
    ("Software Engineering", se.CHAPTER),
    ("Sysadmin: Linux and Windows", sysadmin.CHAPTER),
    ("SDLC, Agile and Scrum", agile.CHAPTER),
    ("AWS (2026)", aws.CHAPTER),
    ("Delivery Tooling: CI/CD, Actions, Jenkins, Terraform, Ansible", delivery.CHAPTER),
    ("DevOps and Cloud", devops.CHAPTER),
    ("Security Testing", security.CHAPTER),
    ("Firewalls", firewall.CHAPTER),
    ("Diagrams and Architecture", diagrams.CHAPTER),
    ("Database Management", database.CHAPTER),
    ("Observability and Monitoring", observability.CHAPTER),
    ("Site Reliability Engineering", sre.CHAPTER),
    ("Cloud Engineer Core Concepts", cloud.CHAPTER),
    ("FinTech and Payments", fintech.CHAPTER),
    ("Business Logic and Web Fundamentals", business.CHAPTER),
]

INTRO = """<h2>How to Use This Guide</h2>

<p>This guide is written for someone starting from nothing. Each chapter follows
the same shape, so you always know what comes next:</p>

<table>
<tr><th>Section</th><th>What you get</th></tr>
<tr><td>What it is</td><td>A plain-English analogy with no jargon</td></tr>
<tr><td>How it works</td><td>Step-by-step, with real numbers</td></tr>
<tr><td>How to remember</td><td>A mnemonic or shortcut that actually sticks</td></tr>
<tr><td>Commands</td><td>Real, copy-pasteable commands</td></tr>
<tr><td>Try it yourself</td><td>A short hands-on exercise</td></tr>
<tr><td>Learning vs Production</td><td>What changes when it is real</td></tr>
</table>

<h3>Where to start</h3>
<ul>
<li><strong>Never touched networking?</strong> Chapters 1 to 4, in order. Do the
exercises, they matter more than the reading.</li>
<li><strong>Know the basics, want depth?</strong> Chapters 5 to 7 cover protocols
and devices that most people half-understand.</li>
<li><strong>Learning Linux?</strong> Chapter 8 takes the command line from
navigation through permissions, pipes and services.</li>
<li><strong>New to how teams work?</strong> Chapter 11 covers the SDLC, Agile and
the full Scrum framework.</li>
<li><strong>Learning AWS?</strong> Chapter 12 starts from regions and IAM and
works through to cost control.</li>
<li><strong>Learning the delivery toolchain?</strong> Chapter 13 covers CI/CD,
GitHub Actions, Jenkins, Terraform and Ansible.</li>
<li><strong>Managing Windows servers?</strong> Chapter 10 shows every command
side by side with its Linux equivalent.</li>
<li><strong>Building for the cloud?</strong> Chapter 21 covers VPCs, subnets,
IAM, high availability, disaster recovery and FinOps across AWS, Azure and GCP.</li>
<li><strong>Running things in production?</strong> Chapters 15 to 20 cover security
testing, firewalls, diagrams, databases, observability and SRE. Read them in that
order; each one assumes the one before it.</li>
<li><strong>New to how money and companies work?</strong> Chapters 22 and 23 cover
payments, receipts, invoices, how shops and SaaS work, and the web security
vocabulary every developer is expected to know.</li>
</ul>

<h3>How to actually learn this</h3>
<ul>
<li>Type every command yourself. Reading code is not the same as running it.</li>
<li>Break things on purpose. Seeing a real error teaches more than a success.</li>
<li>Explain each concept out loud in one sentence. If you cannot, reread it.</li>
<li>Spaced repetition beats cramming. Revisit the memory tricks tomorrow.</li>
<li>Build something small. A server on your laptop beats any amount of reading.</li>
</ul>

<h3>A note on the command examples</h3>
<p>Commands are shown for Windows PowerShell and Linux where they differ. Port
scanning, killing processes and DNS lookups are all covered in the Port Manager
category of this app, so you can try them without a second machine.</p>
"""