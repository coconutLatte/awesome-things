import json
from pathlib import Path
import yaml
from loguru import logger

_config = None
_user_config = None
_config_dir = Path(__file__).parent.parent / "config"
_user_config_path = Path.home() / ".jarvis.json"


def _load_user_config() -> dict:
    """加载用户目录下的 .jarvis.json"""
    global _user_config
    if _user_config is not None:
        return _user_config

    if _user_config_path.exists():
        with open(_user_config_path, "r", encoding="utf-8") as f:
            _user_config = json.load(f)
        logger.info(f"已加载用户配置: {_user_config_path}")
    else:
        _user_config = {}

    return _user_config


def _save_user_config(data: dict):
    """保存用户配置到 .jarvis.json"""
    global _user_config
    _user_config = data
    with open(_user_config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"已保存用户配置: {_user_config_path}")


def load_config(profile: str = "default") -> dict:
    global _config
    if _config is not None:
        return _config

    # 加载内置默认配置
    config_file = _config_dir / f"{profile}.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")

    with open(config_file, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f)

    # 合并用户配置（用户配置优先）
    user = _load_user_config()
    if user:
        _deep_merge(_config, user)

    return _config


def _deep_merge(base: dict, override: dict):
    """递归合并字典，override 优先"""
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def get(key: str, default=None):
    """获取配置项，支持点号分隔的路径，如 'ai.model'"""
    config = load_config()
    keys = key.split(".")
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value


def setup_wizard():
    """首次运行配置向导，生成 ~/.jarvis.json"""
    if _user_config_path.exists():
        return

    print("=" * 40)
    print("  Jarvis 首次配置")
    print("=" * 40)

    api_key = input("请输入 ANTHROPIC_API_KEY: ").strip()
    base_url = input("API Base URL (回车默认 https://api.anthropic.com): ").strip()
    model = input("模型名称 (回车默认 claude-sonnet-4-20250514): ").strip()

    user_cfg = {"ai": {"api_key": api_key}}
    if base_url:
        user_cfg["ai"]["base_url"] = base_url
    if model:
        user_cfg["ai"]["model"] = model

    _save_user_config(user_cfg)
    print(f"\n配置已保存到 {_user_config_path}")
