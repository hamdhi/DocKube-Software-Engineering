r"""Chapter 26 - Authentication: JWT, OAuth 2.0, Google Sign-In and how data moves."""

CHAPTER = r"""<h2>1. How Your Data Actually Transfers</h2>

<p>Before any token can be trusted, the wire it travels on has to be safe.
One page load is a chain of handshakes.</p>

<pre>User                    CDN/ISP             DNS             Server
 |                        |                  |                |
 | 1. https://shop.com    |                  |                |
 |------DNS query---------+-----------------&gt;|                |
 |&lt;----shop.com = 93.184.x.x-----------------+                |
 |                        |                  |                |
 | 2. TCP three-way handshake (SYN, SYN-ACK, ACK) ----------&gt;|
 | 3. TLS handshake:                             --------------|
 |    client hello (cipher suites)  ----------&gt;               |
 |    server hello + certificate   &lt;-----------  proves the   |
 |    key exchange (ECDHE)  -------&gt;            server IS shop|
 |    both derive a session key                   |            |
 |    encrypt everything from here on &lt;=========&gt;|            |
 | 4. GET /index.html  (HTTP inside TLS) -------&gt;             |
 |&lt;--- 200 OK + HTML  (encrypted) ---------------             |
</pre>

<table>
<tr><th>Layer</th><th>Job</th><th>Breaks if missing</th></tr>
<tr><td>DNS</td><td>Names the destination IP</td><td>Cache-poisoning sends users to an attacker</td></tr>
<tr><td>TCP</td><td>Reliable, ordered delivery</td><td>Lost or reordered packets</td></tr>
<tr><td>TLS</td><td>Encryption, integrity, server identity</td><td>Anyone on the Wi-Fi reads your password and tokens</td></tr>
<tr><td>HTTP</td><td>The request/response itself</td><td>-</td></tr>
</table>

<p><strong>Memory trick:</strong> DNS finds the house, TCP knocks the door,
TLS agrees on a secret language, HTTP says what you want. HTTPS = HTTP
spoken inside TLS.</p>

<h2>2. Sessions Versus Tokens</h2>

<table>
<tr><th></th><th>Server-side session</th><th>Token (JWT)</th></tr>
<tr><td>Where state lives</td><td>Server memory/database; cookie holds only a session id</td><td>Inside the token itself; server keeps nothing</td></tr>
<tr><td>Scales horizontally</td><td>Needs sticky sessions or shared store (Redis)</td><td>Any server can verify it alone</td></tr>
<tr><td>Logout / revoke</td><td>Instant - delete the session</td><td>Hard - the token stays valid until it expires</td></tr>
<tr><td>Best for</td><td>Classic web apps, admin panels</td><td>APIs, mobile, microservices</td></tr>
</table>

<h2>3. What A JWT Is</h2>

<p>A <strong>JSON Web Token</strong> is three base64url parts joined by dots.
It carries its own claims, is signed (not encrypted by default), and any
holder can verify it without asking the issuer.</p>

<pre>eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 . eyJzdWIiOiI0MiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcz… . SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
|______ header ______| |________________ payload ________________| |_______ signature ______|
 {alg: HS256, typ: JWT}   {sub: 42, role: admin, exp: 173…}          HMAC(server_secret, header.payload)
</pre>

<table>
<tr><th>Part</th><th>Contents</th><th>Protects against</th></tr>
<tr><td>Header</td><td>Algorithm and token type</td><td>Nothing itself - which is why alg must be pinned when verifying</td></tr>
<tr><td>Payload (claims)</td><td>sub (who), exp (expiry), iat (issued), aud (audience), iss (issuer), plus custom data</td><td>Carries identity so the server needs no session lookup</td></tr>
<tr><td>Signature</td><td>HMAC or RSA over header.payload</td><td>Tampering: change one character of the payload and verification fails</td></tr>
</table>

<p><strong>Critical:</strong> base64 is encoding, not encryption. Anyone can
decode the payload. Never put passwords or secrets in a JWT - only what you
are happy to expose.</p>

<h2>4. Signing And Verifying (Real Code)</h2>

<pre># pip install pyjwt
import datetime
import jwt

SECRET = "change-me-in-a-secret-manager"

def issue_token(user_id, role="user"):
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc)
               + datetime.timedelta(minutes=15),
        "iss": "dockeybe-api",
        "aud": "dockeybe-web",
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def verify_token(token: str):
    # algorithms=[...] is mandatory: it stops the alg:none attack where an
    # attacker strips the signature and re-sends the token.
    return jwt.decode(token, SECRET, algorithms=["HS256"],
                      issuer="dockeybe-api", audience="dockeybe-web")

# FastAPI dependency
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

scheme = HTTPBearer()

def current_user(cred = Depends(scheme)):
    try:
        claims = verify_token(cred.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail="invalid or expired token")
    return claims
</pre>

<table>
<tr><th>Threat</th><th>The defence</th></tr>
<tr><td>Tampered payload</td><td>Signature check fails</td></tr>
<tr><td>alg: none (signature stripped)</td><td>Pin algorithms=[...] on verify</td></tr>
<tr><td>Replayed after logout</td><td>Short expiry (5-15 min) + refresh tokens, or a server-side deny list</td></tr>
<tr><td>Stolen secret = forge anything</td><td>RS256/ES256: public key verifies, only the auth server holds the private key</td></tr>
<tr><td>Token from another service</td><td>Check aud and iss on every verify</td></tr>
<tr><td>Long-lived tokens</td><td>exp 15 min + rotating refresh token in an httpOnly cookie</td></tr>
</table>

<p><strong>HS256 vs RS256:</strong> HS256 shares one secret (both sign and
verify) - every service holding the secret can mint tokens. RS256 is
asymmetric: the auth server signs with the private key, everyone else
verifies with the public key, so a compromised API server cannot forge
identity.</p>
<h2>5. OAuth 2.0 - Delegated Authorization</h2>

<p><strong>OAuth 2.0</strong> answers a different question: not "who are you"
but "let this app do one thing on my behalf, without giving it my password".
Four roles:</p>

<table>
<tr><th>Role</th><th>What it is</th><th>Example</th></tr>
<tr><td>Resource owner</td><td>The human who owns the data</td><td>You, your Google Drive</td></tr>
<tr><td>Client</td><td>The app asking for access</td><td>A third-party photo editor</td></tr>
<tr><td>Authorization server</td><td>Issues the tokens after consent</td><td>accounts.google.com</td></tr>
<tr><td>Resource server</td><td>The API holding the data</td><td>www.googleapis.com/drive</td></tr>
</table>

<p>The flow you will actually implement is the <strong>authorization code
flow with PKCE</strong>. OAuth is about <em>authorization</em>; OpenID Connect
(OIDC) is a thin layer on top that adds <em>authentication</em> (who is the
user) via the id_token. Google Sign-In is OIDC.</p>

<pre>Authorization Code Flow (with PKCE)

You (browser)            Your app (FastAPI)          Google (authorization server)
    |                          |                                |
    | 1. click "Sign in"       |                                |
    |-------------------------&gt;|                                |
    | 2. redirect to Google    |                                |
    |    /authorize?client_id=..&amp;redirect_uri=..&amp;state=..      |
    |    &amp;scope=openid email   |                                |
    |    &amp;code_challenge=..    |                                |
    |---------------------------------------------------------&gt;|
    | 3. user logs in and consents (only Google sees the password)
    |&lt;---------------------------------------------------------|
    | 4. redirect back with ?code=ABC&amp;state=xyz                |
    |-------------------------&gt;|                                |
    | 5. POST /token  code=ABC + code_verifier + client_secret  |
    |                          |------------------------------&gt;|
    |                          | 6. {access_token, id_token,    |
    |                          |     refresh_token}             |
    |                          |&lt;------------------------------|
    | 7. set session cookie    |                                |
    |&lt;-------------------------|                                |
    | 8. API calls carry the token (Authorization: Bearer ...)  |
    |-------------------------&gt; resource APIs                   |
</pre>

<table>
<tr><th>Element</th><th>Purpose</th></tr>
<tr><td>client_id / client_secret</td><td>Identifies your app; the secret proves it is really you at /token</td></tr>
<tr><td>redirect_uri</td><td>Must be pre-registered - otherwise codes can be stolen by an open redirect</td></tr>
<tr><td>scope</td><td>Least privilege: "email" not "everything"</td></tr>
<tr><td>state</td><td>Random value round-tripped through the browser; blocks CSRF / login CSRF</td></tr>
<tr><td>PKCE (code_challenge / verifier)</td><td>Saves public clients (SPAs, mobile) from needing a secret: the code is worthless without the verifier</td></tr>
<tr><td>access_token</td><td>Short-lived key to the API (minutes)</td></tr>
<tr><td>refresh_token</td><td>Long-lived, used only at the token endpoint to get new access tokens; rotate it on every use</td></tr>
<tr><td>Authorization code</td><td>Single-use, seconds-lived, TLS-protected stepping stone</td></tr>
</table>

<p><strong>Grant types and when to use them:</strong> authorization code
(humans via browser - the default), client credentials (machine-to-machine,
no user), device code (TVs and CLI tools). Implicit and password grants are
legacy - do not build them.</p>

<h2>6. Google Sign-In (OIDC), End To End</h2>

<pre># pip install google-auth httpx
import httpx

GOOGLE_CLIENT_ID = "...apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "..."
GOOGLE_DISCOVERY = "https://accounts.google.com/.well-known/openid-configuration"

async def exchange_code(code: str, redirect_uri: str, code_verifier: str):
    # Step 6: swap the authorization code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(GOOGLE_DISCOVERY + "/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,      # PKCE
        })
        tokens = token_resp.json()

        # Verify the id_token signature with Google's public keys -- never
        # trust its payload without checking the signature, aud and exp.
        userinfo = await client.get(
            "https://oauth2.googleapis.com/tokeninfo?id_token="
            + tokens["id_token"])
        claims = userinfo.json()
        assert claims["aud"] == GOOGLE_CLIENT_ID
        return claims   # {sub, email, name, picture, ...}
</pre>

<ol>
<li>Front end generates <code>state</code> + <code>code_verifier</code>,
stores them, redirects to Google's /authorize with the code challenge.</li>
<li>Google authenticates the human and asks for consent per scope.</li>
<li>Back at your redirect URI: exchange code + verifier for tokens.</li>
<li>Verify the id_token (signature, aud, exp, iss), then issue
 <strong>your own</strong> session or JWT for your app.</li>
<li>Google's access token is for Google's APIs - keep it server-side if you
need it, never expose your client secret in the browser.</li>
</ol>

<h2>7. Where To Keep The Token</h2>

<table>
<tr><th>Storage</th><th>Pros</th><th>Cons</th></tr>
<tr><td>httpOnly + Secure + SameSite=Lax cookie</td><td>JavaScript cannot read it; SameSite blunts CSRF</td><td>Needs CSRF defence for state-changing requests</td></tr>
<tr><td>localStorage / sessionStorage</td><td>Simple for SPAs</td><td>Any XSS steals the token instantly; no expiry control</td></tr>
<tr><td>In-memory (variable)</td><td>Not persisted at all</td><td>Lost on refresh; still XSS-reachable</td></tr>
</table>

<p><strong>Memory trick:</strong> cookies for web pages, Authorization header
for APIs you call yourself, and always TLS - a token on a plain HTTP connection
is a bearer token anyone on the path can spend.</p>

<h2>8. The Whole Toolkit, Compared</h2>

<table>
<tr><th>Tool</th><th>Answers</th><th>Shape</th></tr>
<tr><td>Password + session</td><td>Who are you, on this site?</td><td>Cookie holds an id; server holds the state</td></tr>
<tr><td>JWT</td><td>Who are you, for any service?</td><td>Signed self-contained token, stateless verification</td></tr>
<tr><td>OAuth 2.0</td><td>What may this app do for me?</td><td>Delegated access with scopes, no password sharing</td></tr>
<tr><td>OIDC / Google Sign-In</td><td>Who is this human, proven by someone I trust?</td><td>OAuth + verified id_token with profile claims</td></tr>
<tr><td>mTLS / API keys</td><td>Which machine is calling?</td><td>Service identity, not human identity</td></tr>
</table>

<h2>9. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Secrets</td><td>Hard-coded in the file</td><td>Secret manager / env vars, rotated, never in git</td></tr>
<tr><td>Token lifetime</td><td>30 days so it never annoys you</td><td>15-minute access tokens, rotating refresh tokens</td></tr>
<tr><td>Revocation</td><td>Ignored</td><td>Deny list or short TTL + refresh revoke</td></tr>
<tr><td>Sign-in</td><td>Your own password table</td><td>OIDC provider (Google, Azure AD) + MFA</td></tr>
<tr><td>CORS</td><td>*</td><td>Exact origins with credentials</td></tr>
<tr><td>HTTPS</td><td>localhost is fine</td><td>TLS everywhere, HSTS, redirect HTTP to HTTPS</td></tr>
</table>

<h2>10. Key Takeaways</h2>
<ul>
<li>DNS finds, TCP connects, TLS protects, HTTP speaks - HTTPS is HTTP
inside TLS.</li>
<li>A JWT is signed, not encrypted: base64 payload is public; sign it, pin
the algorithm, keep exp short.</li>
<li>HS256 shares a secret; RS256 keeps the signing key on the auth server
only.</li>
<li>OAuth 2.0 delegates access with scopes and never shares the password;
OIDC adds verified identity on top - that is Google Sign-In.</li>
<li>state and PKCE are not optional: they are the CSRF and code-theft
defences.</li>
<li>httpOnly cookie for browsers, Authorization header for APIs, TLS
always.</li>
</ul>

<p><strong>Exercise:</strong> decode a JWT at jwt.io, then build the issue
and verify pair from section 4. Tamper with one character of the payload and
watch verification fail.</p>
"""