"""Chapter 6 - The protocols you use every day."""

CHAPTER = """<h2>1. DNS - The Phone Book of the Internet</h2>

<p>People remember <code>google.com</code>, not 142.250.185.78. DNS translates
names into addresses. It is the first thing that happens when you press Enter in
a browser.</p>

<p><strong>Analogy:</strong> you know a friend's name, not their phone number. DNS
is you opening the phone book, finding the entry and dialling.</p>

<h3>The full resolution journey</h3>
<p>Type <code>www.example.com</code> and the following happens:</p>

<table>
<tr><th>Step</th><th>Who is asked</th><th>What they say</th></tr>
<tr><td>1</td><td>Your OS resolver</td><td>"Do I already know this?" Usually from cache</td></tr>
<tr><td>2</td><td>Recursive resolver</td><td>Your ISP or a public resolver like 1.1.1.1</td></tr>
<tr><td>3</td><td>Root server</td><td>"Ask the .com server" (a.root-servers.net)</td></tr>
<tr><td>4</td><td>.com TLD server</td><td>"Ask the example.com server"</td></tr>
<tr><td>5</td><td>Authoritative server</td><td>"It is 93.184.216.34"</td></tr>
<tr><td>6</td><td>Back up the chain</td><td>Resolver caches it, then you get the answer</td></tr>
</table>

<p><strong>Memory trick:</strong> Root, TLD, Authoritative - in that order, and
each one narrows the search. The resolver does all the walking; your machine
only ever asks the resolver.</p>

<h3>Record types</h3>

<table>
<tr><th>Type</th><th>Purpose</th><th>Example</th></tr>
<tr><td>A</td><td>Name to IPv4 address</td><td>example.com A 93.184.216.34</td></tr>
<tr><td>AAAA</td><td>Name to IPv6 address</td><td>example.com AAAA 2606:2800:220::1</td></tr>
<tr><td>CNAME</td><td>Alias to another name</td><td>www.example.com CNAME example.com</td></tr>
<tr><td>MX</td><td>Mail server</td><td>example.com MX 10 mail.example.com</td></tr>
<tr><td>TXT</td><td>Free text, used for SPF and domain verification</td><td>example.com TXT "v=spf1 -all"</td></tr>
<tr><td>NS</td><td>Which DNS server is authoritative</td><td>example.com NS ns1.provider.com</td></tr>
<tr><td>PTR</td><td>Address back to name, the reverse lookup</td><td>34.216.184.93 PTR example.com</td></tr>
</table>

<h3>The hosts file</h3>
<p>DNS caching can get in the way while testing. Add an entry to the hosts file to
override it. On Windows that file is
<code>C:\\Windows\\System32\\drivers\\etc\\hosts</code>.</p>

<pre>93.184.216.34  example.com
127.0.0.1     myapp.local</pre>

<h2>2. HTTP and HTTPS</h2>

<p>HTTP is a request and response conversation over TCP. The client asks, the
server answers, and they are done. HTTP is stateless, meaning each request
stands alone and the server remembers nothing between them.</p>

<h3>Methods</h3>

<table>
<tr><th>Method</th><th>Meaning</th><th>Safe</th><th>Repeats</th></tr>
<tr><td>GET</td><td>Read something</td><td>Yes</td><td>Yes</td></tr>
<tr><td>POST</td><td>Create or submit</td><td>No</td><td>No</td></tr>
<tr><td>PUT</td><td>Replace entirely</td><td>No</td><td>Yes</td></tr>
<tr><td>PATCH</td><td>Partially update</td><td>No</td><td>Yes</td></tr>
<tr><td>DELETE</td><td>Remove</td><td>No</td><td>Yes</td></tr>
</table>

<p><strong>Memory trick:</strong> Safe methods never change anything, so a browser
may retry them. POST and DELETE change things, so they must never be retried
automatically.</p>

<h3>Status codes grouped by first digit</h3>

<table>
<tr><th>Range</th><th>Meaning</th><th>Common codes</th></tr>
<tr><td>1xx</td><td>Informational, still working</td><td>100 Continue, 101 Switching Protocols</td></tr>
<tr><td>2xx</td><td>Success</td><td>200 OK, 201 Created, 202 Accepted, 204 No Content</td></tr>
<tr><td>3xx</td><td>Redirection</td><td>301 Moved Permanently, 302 Found, 304 Not Modified</td></tr>
<tr><td>4xx</td><td>Client error, your fault</td><td>400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found</td></tr>
<tr><td>5xx</td><td>Server error, our fault</td><td>500 Internal Server Error, 502 Bad Gateway, 503 Unavailable, 504 Timeout</td></tr>
</table>

<p><strong>Memory trick:</strong> <b>4xx is you</b> to fix, <b>5xx is the server</b>.
On call, a flood of 5xx means the service is broken, not that users mistyped.</p>

<h2>3. TLS and SSL - Encryption on the Wire</h2>

<p>SSL is the obsolete name; the modern standard is TLS. They encrypt data so
that anyone in the middle sees only gibberish, and they prove the server is who
it claims to be.</p>

<p><strong>Analogy:</strong> posting a letter in a locked box, with a wax seal.
The seal proves the sender is genuine and the box prevents reading en route.</p>

<h3>The TLS handshake, simplified</h3>

<pre>Client                                 Server
  | --- ClientHello: version, ciphers ---> |
  | <-- ServerHello + certificate ------- |   Here is my identity
  |     Client verifies the certificate    |   Issued by a CA I trust?
  | --- ClientKeyExchange ----------------> |   Here is the shared secret
  | --- Finished -------------------------> |
  | <== All later traffic is encrypted ===></pre>

<ul>
<li><strong>Asymmetric</strong> encryption (public and private keys) agrees on a
shared secret without ever sending it.</li>
<li>The <strong>certificate</strong> binds a public key to a domain, signed by a
Certificate Authority the browser already trusts.</li>
<li><strong>Symmetric</strong> encryption (AES) is then used for the actual data,
because it is far faster.</li>
</ul>

<p><strong>Memory trick:</strong> public key opens, private key proves. Public keys
are fine to hand out, private keys must never leave your machine.</p>

<h3>What HTTPS does not protect</h3>
<p>Encryption hides the content. It does not hide the fact that you visited a
site, it does not stop a phishing page that has its own valid certificate, and it
does not make a slow site fast.</p>

<h2>4. SSH - Encrypted Remote Access</h2>

<p>SSH gives you an encrypted terminal on another machine over port 22. It
replaced Telnet, which sent passwords in plain text.</p>

<p>Authentication is either a password or, far better, a key pair. Your private
key stays on your machine and the public key is copied to the server's
authorized_keys file. The server sends a challenge, you sign it with the private
key, and it verifies against the public key it already holds. The private key is
never sent.</p>

<pre>ssh user@10.0.0.5
ssh -p 2222 user@host          # non-standard port
ssh -i ~/.ssh/id_ed25519 user@host
scp file.txt user@host:/tmp/   # encrypted copy
rsync -avz ./dist user@host:/var/www  # efficient sync
</pre>

<h2>5. Other Protocols You Will Meet</h2>

<table>
<tr><th>Protocol</th><th>Port</th><th>Purpose</th></tr>
<tr><td>ICMP</td><td>none</td><td>ping and traceroute, no ports because it does not use TCP or UDP</td></tr>
<tr><td>DHCP</td><td>UDP 67 and 68</td><td>Automatically hands out IP addresses to devices joining the network</td></tr>
<tr><td>NTP</td><td>UDP 123</td><td>Keeps clocks synchronised, which logs and certificates depend on</td></tr>
<tr><td>FTP</td><td>TCP 20 and 21</td><td>File transfer, unencrypted and now discouraged</td></tr>
<tr><td>SFTP</td><td>TCP 22</td><td>File transfer tunnelled inside SSH, encrypted</td></tr>
<tr><td>SMTP</td><td>TCP 25</td><td>Sending email between mail servers</td></tr>
<tr><td>IMAP</td><td>TCP 143 or 993</td><td>Reading mail on a server</td></tr>
<tr><td>POP3</td><td>TCP 110 or 995</td><td>Older way of downloading mail</td></tr>
<tr><td>LDAP</td><td>TCP 389 or 636</td><td>Directories, also used by Kubernetes for authentication</td></tr>
<tr><td>Syslog</td><td>UDP 514</td><td>Sending logs to a central collector</td></tr>
</table>

<h2>6. Commands</h2>
<pre># DNS
nslookup example.com
dig example.com A
dig example.com MX
dig +short example.com

# Connectivity
ping 8.8.8.8
tracert example.com
Test-NetConnection example.com -Port 443

# TLS inspection
openssl s_client -connect example.com:443 -servername example.com
curl -v https://example.com
</pre>

<h2>7. Try It Yourself (20 minutes)</h2>
<ul>
<li>Run <code>dig example.com</code> and read the ANSWER SECTION for the A record.</li>
<li>Run <code>dig example.com MX</code> to find where its mail is handled.</li>
<li>Run <code>curl -v https://example.com</code> and find the TLS version and certificate issuer.</li>
<li>Add <code>127.0.0.1 myapp.local</code> to your hosts file and see a browser honour it.</li>
<li>Compare <code>ping example.com</code> with <code>ping 93.184.216.34</code>.</li>
</ul>

<h2>8. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>DNS</td><td>Local machine, hosts file overrides</td><td>Managed resolvers, health checks, TTLs tuned for failover</td></tr>
<tr><td>TLS</td><td>Self-signed and clicked through</td><td>Automated renewal, short-lived certs, TLS everywhere</td></tr>
<tr><td>HTTP</td><td>http://localhost:3000</td><td>HTTPS only, HTTP redirected, HSTS enabled</td></tr>
<tr><td>SSH</td><td>Password login to a box</td><td>Key only, no root, bastion host, session logging</td></tr>
<tr><td>Certificates</td><td>Hand-installed, long lived</td><td>ACME automation with alerting on expiry</td></tr>
<tr><td>Secrets</td><td>In a file next to the code</td><td>Secret manager, rotated regularly</td></tr>
<tr><td>Protocol choice</td><td>Whatever installs quickly</td><td>Deliberate, reviewed, version pinned</td></tr>
</table>

<h2>9. Key Takeaways</h2>
<ul>
<li>DNS walks Root, TLD, Authoritative, and the resolver caches the answer.</li>
<li>4xx status codes are the client's fault; 5xx are the server's.</li>
<li>TLS uses asymmetric keys to agree, then symmetric AES for the data.</li>
<li>Public keys can be shared; private keys must never leave the machine.</li>
<li>SSH key authentication never transmits your private key.</li>
<li>In production, TLS is automated and SSH is key-only through a bastion.</li>
</ul>
"""