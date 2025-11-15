from pathlib import Path

from affinity_cli.config import ConfigLoader


def test_config_defaults(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    loader = ConfigLoader(config_file=config_file)
    cfg = loader.load()
    assert cfg.installers_path.name == "affinity-installers"
    assert cfg.wine_prefix.name == ".wine-affinity"
    assert cfg.default_version == "v2"


def test_config_env_override(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    loader = ConfigLoader(config_file=config_file)
    monkeypatch.setenv("AFFINITY_INSTALLERS_PATH", str(tmp_path / "custom"))
    monkeypatch.setenv("AFFINITY_WINE_PREFIX", str(tmp_path / "prefix"))
    monkeypatch.setenv("AFFINITY_DEFAULT_VERSION", "v1")
    cfg = loader.load()
    assert cfg.installers_path == tmp_path / "custom"
    assert cfg.wine_prefix == tmp_path / "prefix"
    assert cfg.default_version == "v1"
