Know Your Code website

This static website was reconstructed from the public site's HTML, CSS, and
assets, then extended with article 002 and its interactive save experiment.
The original deployment source was not present in this checkout. The website
is now versioned here; this repository has no website deployment workflow.

From the repository root:
python3 -m http.server 4321 --bind 127.0.0.1 --directory website

Open:
http://localhost:4321/
http://localhost:4321/blog/
http://localhost:4321/blog/hello-world/
http://localhost:4321/blog/finding-the-write/

Article source: blog/finding-the-write/index.html
Companion model: example/
Check the companion: python3 -B website/example/demo.py

No build step or backend is needed. Stop the preview with Ctrl+C.
The source and downloadable bundles are listed in release-files.txt. Generated
browser screenshots and reports in review/ stay local and are gitignored.

Article 002 includes a browser editor experiment. Its store is in memory;
the companion Python model still uses real SQLite. Scenarios restart with
the reader's paragraph and a queued "Earlier draft" at revision 0. Nothing
is written to a backend or kept after a page refresh. The reverse-order
conflict offers explicit choices rather than automatic retries or merging.

Browser review screenshots and the latest check results are in review/.
The original voice-orb.js bundle is preserved; perlin-noise.png restores
its missing texture from the public site.

The landing page now leads with a project-scoped Skills CLI command. Choosing
Codex, Cursor, or Claude Code updates the agent flag and the starting prompt.
The command requires Node.js 22.20+ and Git; native app installation options
remain linked from GitHub. The ZIP and directory instructions are available
under manual installation. Without JavaScript, the main install link opens
the repository's installation instructions.

The provider badge measures each visible label and resizes its container.
Rotation pauses on hover, focus, open explanations or dialogs, and hidden tabs.
Reduced motion shows a static group of app icons. A no-JavaScript view uses
the first label, with all three apps named in the accessible description.

Each app has a colour theme, set by data-theme on the html element: blue for
Codex, dark grey for Cursor, orange for Claude Code. The page switches theme
as the badge rotates. Choosing an app in the install dialog keeps its theme
and stops the rotation. The Claude orange (#b4532f) is darker than the brand
shade so white body text meets WCAG AA contrast.

Icons on the landing page are inline SVG. Characters such as ↗︎ and ✳︎ are
missing from the site's fonts, and phones substitute colour emoji for them.
Where the blog uses those characters, each is followed by U+FE0E to request
text presentation.

Screenshots and checks for these refinements are in review/refinement/.
The Skills CLI installation was checked with all three agents in a temporary
project using the real public repository. No global installation was made.

The install dialog keeps its close control visible while the instructions
scroll on short screens. The dialog and popovers support keyboard dismissal.
The article includes reduced-motion and no-JavaScript reading fallbacks.
