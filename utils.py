import re



pattern_proxy = re.compile(r'^https?:\/\/[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+@\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:(6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0)$')

pattern_group_vk = re.compile(r"^https?://vk\.com/[a-zA-Z0-9_]+$")

