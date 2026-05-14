import sys
import os
import pytest

# 确保可以导入项目模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    """创建临时配置文件"""
    import yaml

    config_dir = tmp_path / "config"
    config_dir.mkdir()

    config_data = {
        "platform": "windows",
        "ai": {
            "api_key": "test-key",
            "base_url": "https://api.test.com",
            "model": "test-model",
            "max_tokens": 100,
            "system_prompt": "你是测试助手",
        },
    }

    config_file = config_dir / "default.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    # 重置配置缓存
    import utils.config
    utils.config._config = None
    utils.config._user_config = None
    monkeypatch.setattr(utils.config, "_config_dir", config_dir)
    monkeypatch.setattr(utils.config, "_user_config_path", tmp_path / ".jarvis.json")

    return config_data
