# Providers

Tau's provider layer lives in `tau_ai`.

Providers translate external model APIs into Tau's provider-neutral event stream.

## OpenAI-compatible provider

Tau currently includes an OpenAI-compatible chat completions adapter.

Set:

```bash
export OPENAI_API_KEY="..."
```

Optionally set a custom compatible endpoint:

```bash
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

Optionally tune the HTTP timeout used by the default OpenAI-compatible provider:

```bash
export OPENAI_TIMEOUT_SECONDS="120"
```

Optionally tune transient request retries:

```bash
export OPENAI_MAX_RETRIES="2"
export OPENAI_MAX_RETRY_DELAY_SECONDS="0.5"
```

The provider uses `/chat/completions` with streaming enabled.

## Durable Provider Config

Tau stores provider metadata in:

```text
~/.tau/providers.json
```

List configured providers:

```bash
tau providers
```

Create or update a provider:

```bash
tau --provider local \
  --base-url http://localhost:11434/v1 \
  --api-key-env LOCAL_API_KEY \
  --timeout-seconds 120 \
  --max-retries 2 \
  --max-retry-delay-seconds 0.5 \
  --model qwen \
  setup
```

Provider entries can also include `headers`, `timeout_seconds`, `max_retries`,
and `max_retry_delay_seconds` in `~/.tau/providers.json`. `headers` must be an
object with string keys and string values. Timeout must be greater than zero;
retry count and retry delay must be zero or greater.

Example:

```json
{
  "name": "huggingface",
  "type": "openai-compatible",
  "base_url": "https://router.huggingface.co/v1",
  "api_key_env": "HF_TOKEN",
  "credential_name": "huggingface",
  "models": ["openai/gpt-oss-120b"],
  "default_model": "openai/gpt-oss-120b",
  "headers": {
    "X-HF-Bill-To": "my-org"
  }
}
```

Run Tau with a configured provider:

```bash
tau --provider local
tau --provider local "summarize this project"
tau --provider local -p "summarize this project"
```

The positional prompt starts the TUI with an initial prompt. The `-p` form runs
non-interactive print mode.

Inside the TUI:

```text
/model
/model qwen
/login
/reload
```

`/model` opens the interactive model picker. The picker includes models from
configured providers, so selecting a model can also switch the active runtime
provider. `/login` adds or refreshes a built-in provider, and `/reload`
refreshes provider settings for future command use.

When Tau loads `~/.tau/providers.json`, it merges the current built-in model
catalog into built-in provider entries such as Hugging Face. Custom models and
headers in the file are preserved.

## Fake provider

Tau also includes `FakeProvider` for deterministic tests. It replays scripted provider events and never makes network requests.

It is used heavily by agent-loop, session, command, and TUI tests.
