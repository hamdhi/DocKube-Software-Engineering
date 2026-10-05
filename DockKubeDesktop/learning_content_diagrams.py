"""Chapter - Diagrams: what each one is for, and when in a project to draw it."""

CHAPTER = """<h2>1. Why Draw A Diagram?</h2>

<p>A diagram is a picture of something that is genuinely hard to hold in your
head. Systems have too many parts, and prose describing them either leaves out
detail or becomes unreadable. A diagram carries both at once.</p>

<p>Three reasons that actually matter:</p>

<ul>
<li><strong>It finds gaps.</strong> You cannot draw a system you have not
understood. The moment you sit down to draw it, the missing piece becomes obvious.</li>
<li><strong>It settles arguments faster.</strong> Two people arguing in text about
how requests flow will resolve the moment they draw it.</li>
<li><strong>It is the only honest onboarding document.</strong> Documentation
describes what was intended. A current diagram describes what exists.</li>
</ul>

<p><strong>Memory trick:</strong> if a diagram takes longer to explain than the
system takes to build, it is the wrong diagram. Delete it and draw a smaller one.</p>

<h2>2. The Diagrams That Matter, And What Each Is For</h2>

<table>
<tr><th>Diagram</th><th>What it shows</th><th>What question it answers</th></tr>
<tr><td>Context</td><td>The whole system as one box, and its users</td><td>What does this system do, and for whom?</td></tr>
<tr><td>Container</td><td>Applications, databases and services inside it</td><td>What are the moving parts, and how do they talk?</td></tr>
<tr><td>Component</td><td>The internals of one application</td><td>How is this service built inside?</td></tr>
<tr><td>Deployment</td><td>Which component runs on which machine or node</td><td>Where does this actually run?</td></tr>
<tr><td>Sequence</td><td>Messages between actors, in order</td><td>What happens when this request is made?</td></tr>
<tr><td>Use case</td><td>What a user can do, and who can do it</td><td>What are the features and the roles?</td></tr>
<tr><td>Class</td><td>Types, their fields, methods and relationships</td><td>How is the code structured?</td></tr>
<tr><td>Entity relationship</td><td>Tables, their columns and how they relate</td><td>How is the data stored and joined?</td></tr>
<tr><td>State</td><td>One object's states and the moves between them</td><td>What can happen to an order over its life?</td></tr>
<tr><td>Activity or flow</td><td>A process or decision with branches</td><td>What are the steps, and where does it branch?</td></tr>
<tr><td>Data flow</td><td>How data moves and transforms between systems</td><td>Where does this field come from and go?</td></tr>
<tr><td>Threat model</td><td>Trust boundaries and what crosses them</td><td>Where can an attacker get in?</td></tr>
</table>

<h2>3. Which Phase Of A Project Draws What</h2>

<table>
<tr><th>Phase</th><th>Draw these</th><th>Why now</th></tr>
<tr><td>Discovery</td><td>Context diagram</td><td>Agree on scope before anyone writes code</td></tr>
<tr><td>Requirements</td><td>Use case, activity, domain entity relationship</td><td>Agree on what the business does, in its language</td></tr>
<tr><td>Design</td><td>Container, component, sequence, class</td><td>Work out the shape while it is still cheap to change</td></tr>
<tr><td>Threat modelling</td><td>Data flow and trust boundaries</td><td>Security holes are cheapest to fix on paper</td></tr>
<tr><td>Implementation</td><td>Class diagram as it settles, schema diagram</td><td>Keep the model honest as the code appears</td></tr>
<tr><td>Testing</td><td>State and sequence for the awkward flows</td><td>Shows the gap where a test case is missing</td></tr>
<tr><td>Deployment</td><td>Deployment diagram</td><td>Catches "it works on my machine" before release</td></tr>
<tr><td>Run and maintain</td><td>Keep updating the container diagram</td><td>The one diagram that must never go stale</td></tr>
</table>

<p><strong>Memory trick:</strong> draw the diagram while the change is cheap.
A diagram produced at the end documents the system; a diagram produced during
design shapes it.</p>

<h2>4. Drawing Them From Text</h2>

<p>Diagrams stored as text in version control beat binary images in every way
that matters: they diff, they merge, they are reviewable, and a reviewer can
see that one line changed the database port.</p>

<pre># PlantUML - architecture, UML, sequence, class, state, ER
plantuml -tpng architecture.puml
plantuml -checkonly architecture.puml     # fails if it will not parse

# Graphviz - graph layout, dependency and flow graphs
dot -Tsvg dependencies.dot -o dependencies.svg

# Mermaid - diagrams that live inside Markdown documentation
mmdc -i diagram.mmd -o diagram.svg

# dbdiagram.io - database schemas, and it generates SQL too
dbml-renderer schema.dbml
dbml2sql schema.dbml &gt; schema.sql</pre>

<p>Check the source into git alongside the code, and regenerate the image in the
build. The text is the source of truth, never the picture.</p>

<h2>5. The Three Diagrams You Will Draw Most</h2>

<h3>The sequence diagram</h3>
<p>Shows one request from start to finish, with each message in order. This is
the diagram that answers "what actually happens when I click submit?" and it is
the one that most often exposes a missing step nobody noticed.</p>
<p>Use it whenever there is a conversation between more than two parts, and
especially for payments, authentication, and anything with retries.</p>

<h3>The entity relationship diagram</h3>
<p>Shows every table, its columns, and how they connect. Draw it before you
normalise anything, because normalisation only makes sense once you can see the
relationships in front of you.</p>
<p>Every relationship has a cardinality, and this is where most schema bugs
start: one customer to many orders, one order to many lines, but exactly one
customer per order.</p>

<h3>The container diagram</h3>
<p>Shows the applications, the databases and the queues inside one running
system. Draw it whenever you hand work to another team, because it is the
shortest possible answer to "what do you actually run?"</p>

<h2>6. UML - The Parts Worth Knowing</h2>

<p>UML is a large language and almost nobody uses all of it. These are the
diagrams that earn their place in real work:</p>

<table>
<tr><th>Diagram</th><th>Use it for</th></tr>
<tr><td>Class</td><td>The code's structure: types, members, and how they relate</td></tr>
<tr><td>Sequence</td><td>Messages between objects, in time order</td></tr>
<tr><td>Use case</td><td>What actors can do, and which role can do what</td></tr>
<tr><td>Activity</td><td>A workflow with decisions and parallel steps</td></tr>
<tr><td>State machine</td><td>One object's lifecycle, such as an order moving from pending to paid to shipped</td></tr>
<tr><td>Component or package</td><td>How a codebase is laid out</td></tr>
</table>

<p>The state machine is the one beginners skip and experienced people draw most,
because most bugs live in the transitions between states rather than in the
states themselves. An order that is paid can be cancelled by one screen and not
by another is a state machine bug.</p>

<h2>7. The C4 Model For Architecture</h2>

<p>C4 is a simpler alternative to heavyweight UML for system diagrams. It
defines four zoom levels, and you name them after the level:</p>

<table>
<tr><th>Level</th><th>Shows</th><th>Audience</th></tr>
<tr><td>Context</td><td>One box for the whole system, plus users and external systems</td><td>Executives and new joiners</td></tr>
<tr><td>Container</td><td>The applications, databases and services within it</td><td>Developers and architects</td></tr>
<tr><td>Component</td><td>The parts inside one container</td><td>Developers working on it</td></tr>
<tr><td>Code</td><td>Classes and functions</td><td>The person in that codebase</td></tr>
</table>

<p><strong>Memory trick:</strong> the first two levels are the ones worth keeping
current. The third and fourth are better served by reading the code, because they
go stale within a week.</p>

<h2>8. Drawing Good Diagrams And Avoiding Bad Ones</h2>

<table>
<tr><th>Do this</th><th>Not this</th></tr>
<tr><td>One diagram, one question</td><td>One diagram trying to answer five questions</td></tr>
<tr><td>Readable at a glance</td><td>A poster-sized A0 nobody can see on a laptop</td></tr>
<tr><td>Consistent direction, so flow reads the same way everywhere</td><td>Arrows pointing every which way</td></tr>
<tr><td>Show the real names your team uses</td><td>Generic boxes called "Module A" and "Service B"</td></tr>
<tr><td>Delete it when it is no longer true</td><td>Leaving six diagrams, five of them wrong</td></tr>
<tr><td>Regenerate from source in the build</td><td>Editing a PNG and losing the changes next commit</td></tr>
</table>

<p>The test for whether a diagram is worth keeping: would a new engineer learn
something from it in thirty seconds? If not, delete it rather than updating it.</p>

<h2>9. Where Diagrams Fit Into Database Work</h2>

<p>The entity relationship diagram is a database tool before it is a design tool.
The sequence in practice is:</p>

<ul>
<li>Draw the entities and relationships from how the business talks.</li>
<li>Decide each relationship's cardinality: one to one, one to many, many to
many.</li>
<li>Normalise, which usually means turning a many-to-many relationship into a
third table with two foreign keys.</li>
<li>Redraw. The normalised version is usually simpler than the one you started
with, which is the proof you did it right.</li>
<li>Generate the SQL from the diagram so the two cannot disagree.</li>
</ul>

<p>The Databases chapter works through normalisation step by step and shows the
entity relationship diagrams that go with it.</p>

<p><strong>Try it yourself:</strong> draw the entity relationship diagram for
something you know well, such as a library or a food shop. Then try drawing the
sequence for a single purchase. Most people find they disagree about the steps,
which is exactly the point of drawing them.</p>

<p><strong>Learning vs production:</strong> in a small project, one context
diagram and one entity relationship diagram are plenty. As teams grow, diagrams
become the only shared view of a system nobody can hold in their head, and they
have to live in version control next to the code or they will quietly rot.</p>"""
