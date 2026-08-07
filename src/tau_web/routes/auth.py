"""Provider credential and first-run onboarding routes for Tau Web."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from aiohttp import web

from tau_coding.credentials import CredentialStoreError, FileCredentialStore
from tau_coding.paths import TauPaths
from tau_coding.provider_config import (
    ProviderConfigError,
    load_provider_settings,
    provider_has_usable_credentials,
    save_provider_settings,
)
from tau_web.routes.common import (
    config_for,
    json_response,
    optional_non_empty_text,
    require_json_body,
)


def _paths(request: web.Request) -> TauPaths:
    database_path = config_for(request).database_path
    assert database_path is not None
    return TauPaths(home=database_path.parent)


def _state(request: web.Request) -> dict[str, object]:
    paths = _paths(request)
    settings = load_provider_settings(paths)
    credentials = FileCredentialStore(paths.home / "credentials.json")
    providers = []
    for provider in settings.providers:
        providers.append(
            {
                "name": provider.name,
                "models": list(provider.models),
                "default_model": provider.default_model,
                "credential_name": provider.credential_name,
                "configured": provider_has_usable_credentials(
                    provider, credential_reader=credentials
                ),
            }
        )
    selected = settings.get_provider()
    return {
        "configured": provider_has_usable_credentials(
            selected, credential_reader=credentials
        ),
        "default_provider": settings.default_provider,
        "default_model": selected.default_model,
        "providers": providers,
    }


async def get_onboarding(request: web.Request) -> web.Response:
    """Return provider choices and redacted credential status."""
    return json_response(_state(request))


async def configure_onboarding(request: web.Request) -> web.Response:
    """Persist a provider credential and default provider/model selection."""
    body = await require_json_body(
        request,
        required_fields=("provider", "model"),
        optional_fields=("credential",),
    )
    provider_name = optional_non_empty_text(body, "provider")
    model = optional_non_empty_text(body, "model")
    credential = optional_non_empty_text(body, "credential")
    assert provider_name is not None and model is not None

    paths = _paths(request)
    settings = load_provider_settings(paths)
    try:
        provider = settings.get_provider(provider_name)
    except ProviderConfigError as exc:
        raise web.HTTPBadRequest(reason=str(exc)) from exc
    if model not in provider.models:
        raise web.HTTPBadRequest(reason=f"Unknown model for {provider_name}: {model}")
    if credential is not None and provider.credential_name is None:
        raise web.HTTPBadRequest(reason=f"Provider {provider_name} does not accept credentials")

    selected_provider = replace(provider, default_model=model)
    updated_providers = tuple(
        selected_provider if item.name == provider_name else item for item in settings.providers
    )
    updated_settings = replace(
        settings,
        default_provider=provider_name,
        providers=updated_providers,
    )
    if credential is not None:
        assert provider.credential_name is not None
        try:
            FileCredentialStore(paths.home / "credentials.json").set(
                provider.credential_name, credential
            )
        except CredentialStoreError as exc:
            raise web.HTTPBadRequest(reason=str(exc)) from exc
    save_provider_settings(updated_settings, paths)
    return json_response(_state(request))


def setup_routes(app: Any) -> None:
    app.router.add_get("/api/onboarding", get_onboarding)
    app.router.add_put("/api/onboarding", configure_onboarding)
