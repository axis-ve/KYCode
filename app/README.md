# KYCode Studio

The companion harness for the Know Your Code skills: talk with your codebase, prove what you learned, and publish it as a mini-podcast episode anyone can hear, verify, tip, and subscribe to.

Anyone can generate a beautiful demo with AI. The skill stays unproven until the builder can talk through the real code. The Studio makes that proof the product: every episode carries a source-verified code path (`file:line` for each hop) and, when the creator takes it, a passed quiz.

## Run

```sh
python3 app/server.py
```

Open `http://127.0.0.1:8765/`. Python 3 standard library only — no installs, no build step. Set `KYC_PORT` to change the port and `KYC_DB` to move the SQLite database (default `app/studio.db`, created on first run).

On first run a clearly labelled demo episode is seeded from a real trace of `evals/fixtures/notes-app`, so Discover is never an empty page.

## The loop

1. **Scan** a project folder (read-only; must be inside this repository or your home folder).
2. **Talk**: ask "What happens when I press Save?" by microphone or text. The agent traces label → handler → functions → stored data, shows reach (other callers), and suggests a check you can run yourself. Interrupt any time; the resume point is kept. Chips cover walkthrough, diagnosis (reproduce before naming a cause), quiz (one question, waits, grades against the trace), and podcast co-host mode.
3. **Record** your voice while you talk (browser `MediaRecorder`; the agent's side stays in the transcript and can be narrated on the episode page — labelled as narration, never passed off as a studio recording).
4. **Publish**: title, show notes, optional price. You get a public episode link (`/e/<id>`), a podcast RSS feed (`/rss/<handle>.xml`), and an embed player (`/embed/<id>`) for your site. Your creator card links your project, so every episode is also marketing.
5. **Earn**: tips, monthly subscriptions, and paid episodes through Stripe (below), with a Revenue view that only ever shows Stripe-confirmed payments.

Voice uses the browser Web Speech API where available (Chrome for speech input). Everything works in text where it is not; the app says so instead of pretending.

## Bring your own key (optional)

Without a key, the built-in local tracer answers from your actual source with citations. With an OpenAI or Anthropic key (Studio → Brain), the model answers using the `know-your-code` skill as its instructions and the verified trace as its only evidence. Keys live in your browser's local storage and are sent per request; the server proxies them once and never stores or logs them. If the provider errors, the Studio falls back to the local tracer and labels the reply.

## Stripe revenue

```sh
STRIPE_SECRET_KEY=your-stripe-secret-key python3 app/server.py
```

Payments use Stripe-hosted Checkout — no card data touches this app. In Revenue, set your tip and subscription prices and paste your Stripe Connect account id (`acct_…`): payouts then land with you via destination charges, with a 10% platform fee. A purchase is recorded only after Stripe confirms the Checkout session as paid. Without `STRIPE_SECRET_KEY`, every buy button explains setup and nothing is charged or faked.

## Rules inherited from the skill

- Read-only on target projects. Exploration never edits.
- Every factual hop is read from source and cited; anything else is labelled inference.
- Checks are suggested, not claimed as run.
- No invented listens, payments, or proof: the badge appears only with a real trace (and quiz, when taken).

## Tests

`tests/test_studio.py` covers scanning, the Save trace against the eval fixture (including not bleeding into neighbouring handlers), quiz waiting/grading, path rejection, the demo seed proof, and Stripe honesty when unconfigured. Run `python3 -m unittest discover -s tests -v` from the repository root.
