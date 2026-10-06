r"""Chapter 31 - Encryption, hashing, bcrypt, salting, random numbers and UUIDs."""

CHAPTER = r"""<h2>1. Four Words People Mix Up</h2>

<table>
<tr><th>Term</th><th>Does</th><th>Reversible?</th><th>Examples</th></tr>
<tr><td>Encoding</td><td>Represents data in another format</td><td>Yes, trivially</td><td>base64, UTF-8, URL encoding</td></tr>
<tr><td>Hashing</td><td>One-way fingerprint of any length -&gt; fixed digest</td><td>No (by design)</td><td>SHA-256, bcrypt, Argon2</td></tr>
<tr><td>Encryption</td><td>Two-way scrambling with a key</td><td>Yes, with the key</td><td>AES-GCM, Fernet, RSA, ChaCha20</td></tr>
<tr><td>Tokenisation</td><td>Replaces a value with a random reference</td><td>Only via the mapping store</td><td>Payment tokens, session ids</td></tr>
</table>

<p><strong>Memory trick:</strong> hashing is a <em>fingerprint</em> (cannot be
reversed, proves equality), encryption is a <em>locked box</em> (the key opens
it). Passwords get hashed, card numbers in a database get tokenised, data on
the wire gets encrypted.</p>

<h2>2. Symmetric Encryption - One Key Both Ways</h2>

<pre># pip install cryptography
from cryptography.fernet import Fernet

key = Fernet.generate_key()              # store in a secret manager, never in git
cipher = Fernet(key)

token  = cipher.encrypt(b"card 4242 4242 4242 4242")
plain  = cipher.decrypt(token)            # b'card 4242...'

# Fernet also authenticates: tampered ciphertext raises InvalidToken.
# Envelope encryption: encrypt the data with a random data key, then
# encrypt the data key with the master key (KMS) - so you rotate rarely.
</pre>

<pre># AES-GCM (what most APIs use - authenticated encryption)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

aes_key = AESGCM.generate_key(bit_length=256)
aes     = AESGCM(aes_key)
nonce   = os.urandom(12)                 # never reuse a nonce with a key!
cipher  = aes.encrypt(nonce, b"payload", b"aad-header")
plain   = aes.decrypt(nonce, cipher, b"aad-header")
</pre>

<h2>3. Asymmetric Encryption - Two Keys</h2>

<pre>from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public  = private.public_key()

from cryptography.hazmat.primitives import hashes

blob = public.encrypt(b"session-key",
    padding.OAEP(mgf=padding.MGF1(hashes.SHA256),
                 algorithm=hashes.SHA256, label=None))
plain = private.decrypt(blob,
    padding.OAEP(mgf=padding.MGF1(hashes.SHA256),
                 algorithm=hashes.SHA256, label=None))
# Anything public-encrypted can only be private-decrypted, so a server
# encrypts a random session key with the CLIENT's public key.
# Signatures: private.sign(data) - anyone with the public key verifies.
# TLS certificates, JWT RS256 and SSH keys are all this pattern.
</pre>

<table>
<tr><th></th><th>Symmetric</th><th>Asymmetric</th></tr>
<tr><td>Keys</td><td>One shared secret</td><td>Public + private pair</td></tr>
<tr><td>Speed</td><td>Fast (100x+)</td><td>Slow - used to exchange keys, not bulk data</td></tr>
<tr><td>Distribution</td><td>Hard: how do you share it?</td><td>Easy: publish the public key</td></tr>
<tr><td>Used for</td><td>Database fields, file storage, TLS bulk data</td><td>TLS handshake, code signing, JWT RS256, PGP</td></tr>
</table>
<h2>4. Passwords - Hashing, Salting And bcrypt</h2>

<p>Never store a password, never encrypt it, never hash it with SHA-256
alone. Store a <strong>slow hash with a unique salt</strong>.</p>

<table>
<tr><th>Ingredient</th><th>What it is</th><th>What it defeats</th></tr>
<tr><td>Slow hash (bcrypt/Argon2)</td><td>Designed to take ~100ms per guess</td><td>Brute force and guessing speed</td></tr>
<tr><td>Salt</td><td>Random 16+ bytes, unique per user, stored beside the hash</td><td>Precomputed rainbow tables and "same password = same hash" leaks</td></tr>
<tr><td>Pepper</td><td>Secret value kept OUTSIDE the database (env/secret manager)</td><td>A stolen database alone is no longer enough</td></tr>
<tr><td>Work factor</td><td>Cost parameter (bcrypt rounds)</td><td>Hardware gets faster - raise the cost over time</td></tr>
</table>

<pre># pip install bcrypt passlib[bcrypt]
import bcrypt, os

def hash_password(plain: str, pepper: str = os.environ["PASSWORD_PEPPER"]) -&gt; str:
    salt = bcrypt.gensalt(rounds=12)          # 12 = ~250ms on modern CPU
    # bcrypt caps input at 72 bytes - pre-hash long passwords with SHA-256.
    return bcrypt.hashpw(plain.encode() + pepper.encode(), salt).decode()

def verify_password(plain: str, stored: str, pepper: str = ...) -&gt; bool:
    # compare_digest: constant time - never use == on secrets
    import hmac
    return hmac.compare_digest(
        bcrypt.hashpw(plain.encode() + pepper.encode(),
                      stored.encode()),
        stored.encode())

# Argon2id is the modern recommendation (memory-hard):
# from argon2 import PasswordHasher
# ph = PasswordHasher(time_cost=3, memory_size=65536, parallelism=4)
# hash = ph.hash(plain); ph.verify(hash, plain + pepper)

# Login flow: dummy-hash BEFORE "user not found" so timing does not
# reveal which accounts exist:
verify_password(plain, DUMMY_HASH)
</pre>

<p><strong>Memory trick:</strong> salt is <em>public and per-user</em> (stops
databases of precomputed hashes), pepper is <em>secret and global</em> (stops
a stolen database). You need both; only salt is stored with the hash.</p>

<h2>5. Random Numbers And Tokens - secrets, Not random</h2>

<pre>import random          # NO for anything security-relevant - it is guessable
import secrets         # cryptographic randomness (os.urandom under the hood)
import uuid

# Passwords / tokens / session ids: ALWAYS secrets
reset_token = secrets.token_urlsafe(32)     # 43 URL-safe chars, 256 bits
api_key     = secrets.token_hex(20)         # 40 hex chars
csrf        = secrets.choice(options)      # random element
rand_int    = secrets.randbelow(1_000_000)  # 0..999999 inclusive
salt        = secrets.token_bytes(16)

# random is fine for games, shuffles, sampling, simulation:
random.shuffle(deck)
sample = random.sample(population, k=10)
probability = random.random()               # 0.0 &lt;= x &lt; 1.0

# UUIDs
uuid.uuid4()      # random - tokens, ids you generate yourself
uuid.uuid7()      # time-ordered (Python 3.13+ or uuid7 pkg) - sortable DB keys
uuid.uuid1()      # time + MAC - leaks hardware, avoid for public ids

# UUID4 is 122 random bits: fine as an identifier, but use secrets for
# anything an attacker must NOT be able to guess (password resets, CSRF).
# Database advice: BIGINT autoincrement internally, uuid7 publicly.
</pre>

<table>
<tr><th>Need</th><th>Use</th><th>Avoid</th></tr>
<tr><td>Password hashing</td><td>bcrypt (12+ rounds) or Argon2id</td><td>MD5, SHA-1, SHA-256 alone, anything fast</td></tr>
<tr><td>Reset / API tokens</td><td>secrets.token_urlsafe(32)</td><td>random.random(), uuid4 for high-security tokens, timestamps</td></tr>
<tr><td>Database primary keys</td><td>uuid7 or BIGINT</td><td>uuid1 (MAC leak), sequential public ids (enumeration)</td></tr>
<tr><td>Encryption at rest</td><td>AES-GCM / Fernet with keys in a KMS</td><td>Rolling your own cipher mode</td></tr>
<tr><td>Comparing secrets</td><td>hmac.compare_digest</td><td>== (timing side channel)</td></tr>
</table>

<h2>6. Encryption At Rest And In Transit - A Practical Policy</h2>

<pre>in transit   : TLS 1.2+ everywhere (HSTS, redirect HTTP -&gt; HTTPS)
database     : disk-level encryption (LUKS/BitLocker/EBS) + field-level
               AES-GCM for PII (national id, card number)
passwords    : bcrypt/Argon2 + salt + pepper (never encryption)
backups      : encrypted with a key separate from the data
secrets      : secret manager (Vault, AWS SM, .env excluded from git)
keys         : rotate on schedule AND on suspected compromise;
               envelope encryption so rotating the master key is cheap
</pre>

<h2>7. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Passwords</td><td>plaintext or SHA-256 in the users table</td><td>bcrypt/Argon2, pepper in a manager, dummy-hash on unknown users</td></tr>
<tr><td>Randomness</td><td>random.randint for tokens</td><td>secrets only, 128+ bits, single-use with expiry</td></tr>
<tr><td>Keys</td><td>In the source code</td><td>KMS/Vault, rotated, access-audited, never logged</td></tr>
<tr><td>HTTPS</td><td>Optional on localhost</td><td>Mandatory, HSTS preloaded, certs auto-renewed</td></tr>
<tr><td>Session</td><td>Cookie with no expiry</td><td>httpOnly+Secure+SameSite, short TTL, rotating refresh</td></tr>
</table>

<h2>8. Key Takeaways</h2>
<ul>
<li>Encoding is reversible, hashing is one-way, encryption needs a key -
pick by whether you must get the data back.</li>
<li>Passwords: slow hash + unique salt + secret pepper + constant-time
verify. Never encrypt them, never MD5/SHA them.</li>
<li>secrets for security, random for games; uuid4 for ids, uuid7 for sorted
keys.</li>
<li>Compare secrets with hmac.compare_digest, and dummy-hash on unknown
accounts.</li>
<li>Encrypt in transit (TLS), at rest (AES-GCM/disk), and keep keys
outside the data.</li>
</ul>

<p><strong>Exercise:</strong> implement register/login with bcrypt (rounds
12) and a pepper from the environment; then prove salt works by registering
the same password twice and comparing the two stored hashes.</p>
"""