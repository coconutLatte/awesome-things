import pytest
import utils.config as config


def test_load_config(mock_config):
    """测试配置加载"""
    cfg = config.load_config()
    assert cfg["platform"] == "windows"
    assert cfg["ai"]["model"] == "test-model"


def test_get_nested_key(mock_config):
    """测试点号路径获取配置"""
    config.load_config()
    assert config.get("ai.model") == "test-model"
    assert config.get("ai.api_key") == "test-key"
    assert config.get("ai.base_url") == "https://api.test.com"


def test_get_default_value(mock_config):
    """测试默认值"""
    config.load_config()
    assert config.get("not.exist", "default") == "default"


def test_user_config_override(mock_config, tmp_path):
    """测试用户配置覆盖"""
    import json

    user_cfg = {"ai": {"model": "overridden-model"}}
    user_file = tmp_path / ".jarvis.json"
    with open(user_file, "w") as f:
        json.dump(user_cfg, f)

    # 重新加载
    config._config = None
    config._user_config = None
    cfg = config.load_config()

    assert cfg["ai"]["model"] == "overridden-model"
    assert cfg["ai"]["api_key"] == "test-key"  # 未覆盖的保持原值
