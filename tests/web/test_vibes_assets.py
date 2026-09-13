import pytest
from aiohttp import web
from tau_web.routes.vibes_assets import asset_names, asset_response


def test_public_manifest_contains_runtime_not_tooling():
    names = asset_names()
    assert {'dist/app.js', 'dist/app.css', 'js/bootstrap.js'} <= names
    assert not any(name.endswith('.map') or 'node_modules' in name for name in names)
    assert 'build.js' not in names
    for name in names:
        response = asset_response(name)
        assert response.status == 200
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        if name.endswith('.mjs'):
            assert response.content_type == 'application/javascript'


@pytest.mark.parametrize('name', ['../LICENSE', '/etc/passwd', 'dist/app.js.map', 'build.js', 'js/../js/app.js'])
def test_unlisted_and_traversal_assets_rejected(name):
    with pytest.raises(web.HTTPNotFound):
        asset_response(name)
