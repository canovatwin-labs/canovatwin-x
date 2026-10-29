import pytest

from canovatwin.api import panel


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    root = tmp_path / "bundle"
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text(
        '<!doctype html><html lang="tr"><head><title>CanovaTwin X</title>'
        '<script type="module" src="/panel/assets/index-test.js"></script>'
        '</head><body><div id="root"></div></body></html>'
    )
    (root / "assets/index-test.js").write_text('document.title = "CanovaTwin X";')
    (root / "assets/index-test.css").write_text("body { color: black; }")
    monkeypatch.setattr(panel, "WEB_ROOT", root)
    return root


@pytest.mark.parametrize("role", ["reader", "writer"])
def test_session_reports_server_verified_role(api, request, role):
    response = api.get("/api/v1/session", headers=request.getfixturevalue(role))
    assert response.status_code == 200
    assert response.json() == {"role": role, "actor": f"api-{role}"}
    assert response.headers["cache-control"] == "no-store"


def test_session_rejects_missing_and_invalid_keys(api):
    for headers in ({}, {"Authorization": "Bearer invalid"}):
        response = api.get("/api/v1/session", headers=headers)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
        assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_public_panel_redirect_and_security_headers(api, bundle):
    redirect = api.get("/panel", follow_redirects=False)
    assert redirect.status_code == 308
    assert redirect.headers["location"] == "/panel/"
    response = api.get("/panel/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"
    csp = response.headers["content-security-policy"]
    assert "script-src 'self'" in csp and "style-src 'self'" in csp
    assert "connect-src 'self'" in csp and "frame-ancestors 'none'" in csp
    assert "unsafe-inline" not in csp and "unsafe-eval" not in csp
    assert "CanovaTwin X" in response.text
    # Public assets do not make the history public.
    assert api.get("/api/v1/incidents").status_code == 401


@pytest.mark.parametrize(
    ("filename", "media_type"), [("index-test.js", "text/javascript"), ("index-test.css", "text/css")]
)
def test_assets_and_head_are_served_with_correct_types(api, bundle, filename, media_type):
    response = api.get(f"/panel/assets/{filename}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(media_type)
    assert response.headers["content-security-policy"]
    head = api.head(f"/panel/assets/{filename}")
    assert head.status_code == 200
    assert head.content == b""
    assert int(head.headers["content-length"]) == len(response.content)
    assert api.head("/panel/").content == b""


@pytest.mark.parametrize(
    "resource",
    [
        "/panel/assets/missing.js",
        "/panel/assets/index-test.js.map",
        "/panel/assets/config.json",
        "/panel/assets/.env",
        "/panel/assets/subdir/index-test.js",
        "/panel/assets/%2e%2e%2fprivate.js",
        "/panel/assets/%252e%252e%252fprivate.js",
        "/panel/assets/%2e%2e%5cprivate.js",
        "/panel/assets/%00index-test.js",
        "/panel/index.html",
        "/panel/config.json",
        "/panel/.local/api-config.json",
        "/panel/src/App.tsx",
    ],
)
def test_assets_do_not_expose_sources_maps_or_other_files(api, bundle, resource):
    (bundle / "private.js").write_text("PRIVATE")
    (bundle / "assets/index-test.js.map").write_text("PRIVATE")
    (bundle / "assets/config.json").write_text("PRIVATE")
    response = api.get(resource)
    assert response.status_code == 404
    assert "PRIVATE" not in response.text
    assert str(bundle) not in response.text


def test_missing_bundle_returns_actionable_safe_error(api, tmp_path, monkeypatch):
    missing = tmp_path / "private-unbuilt-directory"
    monkeypatch.setattr(panel, "WEB_ROOT", missing)
    response = api.get("/panel/")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PANEL_NOT_BUILT"
    assert "content-security-policy" in response.headers
    assert str(missing) not in response.text
    assert not missing.exists()
    assert api.get("/health").status_code == 200


@pytest.mark.parametrize("asset", [False, True])
def test_symlinks_cannot_serve_files_outside_bundle(api, bundle, tmp_path, asset):
    private = tmp_path / "private.html"
    private.write_text("PRIVATE")
    file = bundle / ("assets/outside.js" if asset else "index.html")
    file.unlink(missing_ok=True)
    file.symlink_to(private)
    response = api.get("/panel/assets/outside.js" if asset else "/panel/")
    assert response.status_code == (404 if asset else 503)
    assert "PRIVATE" not in response.text


def test_symlinked_asset_directory_cannot_escape_bundle(api, bundle, tmp_path):
    for file in (bundle / "assets").iterdir():
        file.unlink()
    (bundle / "assets").rmdir()
    outside = tmp_path / "private-assets"
    outside.mkdir()
    (outside / "outside.js").write_text("PRIVATE")
    (bundle / "assets").symlink_to(outside)
    response = api.get("/panel/assets/outside.js")
    assert response.status_code == 404
    assert "PRIVATE" not in response.text


def test_panel_is_excluded_from_openapi_but_session_is_protected(api):
    schema = api.get("/openapi.json").json()
    assert not any(path.startswith("/panel") for path in schema["paths"])
    session = schema["paths"]["/api/v1/session"]["get"]
    assert session["security"] == [{"LocalBearer": []}]
    assert session["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/Principal"
    }
