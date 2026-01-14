import yaml


def load_yaml_config(file_path):
    """
    加载 YAML 配置文件并返回配置内容。

    :param file_path: 配置文件路径
    :return: 配置内容（dict）
    """
    with open(file_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config
