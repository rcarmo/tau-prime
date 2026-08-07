import { useEffect, useMemo, useState } from "preact/hooks";
import { TauApi } from "../api/tau";
import type { OnboardingState } from "../api/types";

const api = new TauApi();

export function Onboarding() {
  const [state, setState] = useState<OnboardingState | null>(null);
  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [credential, setCredential] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.onboarding().then((next) => {
      setState(next);
      setProvider(next.default_provider);
      setModel(next.default_model);
      setOpen(!next.configured);
    }).catch((reason) => setError(String(reason)));
  }, []);

  const selected = useMemo(
    () => state?.providers.find((item) => item.name === provider),
    [state, provider],
  );

  function chooseProvider(name: string) {
    const next = state?.providers.find((item) => item.name === name);
    setProvider(name);
    setModel(next?.default_model ?? "");
    setCredential("");
    setError("");
  }

  async function submit(event: Event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const next = await api.configureOnboarding({
        provider,
        model,
        ...(credential.trim() ? { credential } : {}),
      });
      setState(next);
      setCredential("");
      setOpen(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setSaving(false);
    }
  }

  if (!state && !error) return null;
  return (
    <>
      <button className="provider-setup-trigger" type="button" onClick={() => setOpen(true)}>
        Provider setup
      </button>
      {open && state ? (
        <div className="onboarding-backdrop" role="presentation">
          <section className="onboarding-dialog" role="dialog" aria-modal="true" aria-labelledby="onboarding-title">
            <h2 id="onboarding-title">Connect a model provider</h2>
            <p>Choose a provider and model. Credentials are stored locally and never returned by this API.</p>
            <form onSubmit={submit}>
              <label>Provider
                <select value={provider} onChange={(event) => chooseProvider(event.currentTarget.value)}>
                  {state.providers.map((item) => <option value={item.name}>{item.name}</option>)}
                </select>
              </label>
              <label>Model
                <select value={model} onChange={(event) => setModel(event.currentTarget.value)}>
                  {(selected?.models ?? []).map((item) => <option value={item}>{item}</option>)}
                </select>
              </label>
              {selected?.credential_name ? (
                <label>API key
                  <input type="password" value={credential} autocomplete="off" onInput={(event) => setCredential(event.currentTarget.value)} placeholder={selected.configured ? "Stored credential (leave blank to keep)" : "Required"} />
                </label>
              ) : null}
              {error ? <p className="onboarding-error" role="alert">{error}</p> : null}
              <div className="onboarding-actions">
                <button type="button" onClick={() => setOpen(false)}>Cancel</button>
                <button type="submit" disabled={saving || !provider || !model || Boolean(selected?.credential_name && !selected.configured && !credential.trim())}>
                  {saving ? "Saving…" : "Save and continue"}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </>
  );
}
