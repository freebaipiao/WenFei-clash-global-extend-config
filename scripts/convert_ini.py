"""Generate Clash Verge / Mihomo merge and script profiles from clashconfig/codex."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPO = "freebaipiao/clashconfig"
SOURCE_BRANCH = "codex"
SOURCE_RAW = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_BRANCH}/"
PROFILES = (
    "config",
    "no_rate_config",
    "no_dns_override",
    "no_dns_override_no_rate",
)
SOURCE_FILES = (
    *(f"{name}.ini" for name in PROFILES),
    "clash-base.yml",
    "steam-download.list",
    "download-process.list",
    "ai-services.list",
    "LICENSE",
)
OPTIONS = {
    "enable_rule_generator",
    "overwrite_original_rules",
    "exclude_remarks",
    "clash_rule_base",
}
RULE_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-REGEX",
    "IP-CIDR", "IP-CIDR6", "GEOIP", "GEOSITE", "PROCESS-NAME",
    "PROCESS-PATH", "PROCESS-NAME-REGEX", "PROCESS-PATH-REGEX",
    "DST-PORT", "SRC-PORT", "NETWORK",
}


def parse_ini(text, filename):
    options, groups, rules = {}, [], []
    section = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith((";", "#")):
            continue
        if line.startswith("["):
            if line != "[custom]":
                raise ValueError(f"{filename}:{number}: unsupported section {line}")
            section = line
            continue
        if section is None or "=" not in line:
            raise ValueError(f"{filename}:{number}: malformed INI entry")
        key, value = (part.strip() for part in line.split("=", 1))
        if key == "custom_proxy_group":
            groups.append(value)
        elif key == "ruleset":
            rules.append(value)
        elif key in OPTIONS and key not in options:
            options[key] = value
        else:
            raise ValueError(f"{filename}:{number}: unsupported or duplicate option {key}")
    for key in ("enable_rule_generator", "overwrite_original_rules"):
        if options.get(key, "").lower() != "true":
            raise ValueError(f"{filename}: {key}=true is required")
    if not groups or not rules:
        raise ValueError(f"{filename}: proxy groups or rules are missing")
    return options, groups, rules


def convert_group(value, exclude):
    parts = value.split("`")
    if len(parts) < 3:
        raise ValueError(f"Malformed proxy group: {value}")
    name, kind, *members = parts
    group = {"name": name, "type": kind}
    if kind in ("url-test", "fallback", "load-balance"):
        if len(members) < 3:
            raise ValueError(f"Missing health check settings: {name}")
        url, timing = members[-2:]
        members = members[:-2]
        if urlparse(url).scheme not in ("http", "https"):
            raise ValueError(f"Unsupported health check URL: {url}")
        interval, *extra = timing.split(",")
        if len(extra) > 2 or int(interval) <= 0:
            raise ValueError(f"Unsupported health check timing: {timing}")
        group.update(url=url, interval=int(interval))
        if extra and extra[0]:
            group["timeout"] = int(extra[0]) * 1000
        if len(extra) == 2 and extra[1] and kind == "url-test":
            group["tolerance"] = int(extra[1])
        if kind == "load-balance":
            group["strategy"] = "consistent-hashing"
    elif kind != "select":
        raise ValueError(f"Unsupported proxy group type: {kind}")

    choices = [member[2:] for member in members if member.startswith("[]")]
    filters = [member for member in members if not member.startswith("[]")]
    if choices:
        group["proxies"] = choices
    if filters:
        for expression in filters:
            re.compile(expression)
        group["include-all"] = True
        group["filter"] = "|".join(f"(?:{expression})" for expression in filters)
        if exclude:
            group["exclude-filter"] = exclude
        group["empty-fallback"] = "DIRECT"
    if not choices and not filters:
        raise ValueError(f"Empty proxy group: {name}")
    return group


def inline_rule(value, policy):
    parts = value.split(",")
    if parts == ["FINAL"] or parts == ["MATCH"]:
        return f"MATCH,{policy}"
    if parts[0] not in RULE_TYPES or len(parts) not in (2, 3):
        raise ValueError(f"Unsupported inline rule: {value}")
    if len(parts) == 3 and parts[2] != "no-resolve":
        raise ValueError(f"Unsupported inline rule option: {value}")
    return ",".join([*parts[:2], policy, *parts[2:]])


def convert_rules(values, inputs):
    rules, providers = [], {}
    for value in values:
        if "," not in value:
            raise ValueError(f"Malformed ruleset: {value}")
        policy, source = value.split(",", 1)
        if source.startswith("[]"):
            rules.append(inline_rule(source[2:], policy))
            continue
        if source.startswith(SOURCE_RAW):
            filename = source[len(SOURCE_RAW):]
            if filename not in inputs or not filename.endswith(".list"):
                raise ValueError(f"Unsupported local ruleset: {source}")
            entries = [line.strip() for line in inputs[filename].splitlines()
                       if line.strip() and not line.lstrip().startswith(("#", ";"))]
            if not entries:
                raise ValueError(f"Empty ruleset: {filename}")
            rules.extend(inline_rule(entry, policy) for entry in entries)
            continue
        parsed = urlparse(source)
        suffix = Path(parsed.path).suffix.lower()
        if parsed.scheme != "https" or suffix not in (".list", ".yaml", ".yml"):
            raise ValueError(f"Unsupported remote ruleset format: {source}")
        digest = hashlib.sha256(source.encode()).hexdigest()[:10]
        name = f"jiahao-{Path(parsed.path).stem}-{digest}"
        providers[name] = {
            "type": "http",
            "behavior": "classical",
            "format": "text" if suffix == ".list" else "yaml",
            "url": source,
            "path": f"./rule-providers/{name}{suffix}",
            "interval": 86400,
        }
        rules.append(f"RULE-SET,{name},{policy}")
    return rules, providers


def build_profile(name, inputs):
    options, group_values, rule_values = parse_ini(inputs[f"{name}.ini"], f"{name}.ini")
    exclude = options.get("exclude_remarks", "")
    if exclude:
        re.compile(exclude)
    extension = {"mode": "rule", "find-process-mode": "strict"}
    base_url = options.get("clash_rule_base")
    if base_url:
        if base_url != SOURCE_RAW + "clash-base.yml":
            raise ValueError(f"Unsupported base template: {base_url}")
        base = yaml.safe_load(inputs["clash-base.yml"])
        if not isinstance(base, dict) or not isinstance(base.get("dns"), dict):
            raise ValueError("The base template must contain a DNS mapping")
        unknown = set(base) - {"mode", "log-level", "dns", "hosts"}
        if unknown:
            raise ValueError(f"Unsupported base template keys: {sorted(unknown)}")
        extension.update(base)
    extension["proxy-groups"] = [convert_group(value, exclude) for value in group_values]
    extension["rules"], extension["rule-providers"] = convert_rules(rule_values, inputs)

    names = [group["name"] for group in extension["proxy-groups"]]
    if len(set(names)) != len(names):
        raise ValueError(f"{name}: duplicate group names")
    allowed = set(names) | {"DIRECT", "REJECT", "REJECT-DROP", "PASS", "COMPATIBLE"}
    for group in extension["proxy-groups"]:
        for member in group.get("proxies", []):
            if member not in allowed:
                raise ValueError(f"{name}: unknown group reference {member}")
    for rule in extension["rules"]:
        parts = rule.split(",")
        policy = parts[-2] if parts[-1] == "no-resolve" else parts[-1]
        if policy not in allowed:
            raise ValueError(f"{name}: unknown rule target {policy}")
    if extension["rules"][-1] != "MATCH,🐟 漏网之鱼":
        raise ValueError(f"{name}: the last rule must be MATCH,🐟 漏网之鱼")
    return extension


def render_script(extension, header):
    data = json.dumps(extension, ensure_ascii=False, indent=2)
    return f"// {header}\n// Generated by scripts/convert_ini.py; edit the converter or upstream INI.\n" + """\nfunction main(config, profileName) {
  if (!config || typeof config !== "object" || Array.isArray(config)) {
    throw new Error("Expected a Clash configuration object");
  }
  // Native Mihomo filters also cover nodes supplied by proxy-providers.
  const extension = """ + data + """;
  const originalHosts = config.hosts || {};
  const originalProviders = config["rule-providers"] || {};
  Object.assign(config, extension);
  config["rule-providers"] = Object.assign({}, originalProviders, extension["rule-providers"]);
  if (extension.hosts) {
    config.hosts = Object.assign({}, originalHosts, extension.hosts);
  }
  return config;
}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=ROOT / "upstream")
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    output = args.output_dir.resolve()
    inputs = {name: (source / name).read_text(encoding="utf-8-sig") for name in SOURCE_FILES}
    actual_ini = {path.name for path in source.glob("*.ini")}
    expected_ini = {f"{name}.ini" for name in PROFILES}
    if actual_ini != expected_ini:
        raise ValueError(f"Expected exactly four INI files, found {sorted(actual_ini)}")
    if (source / ".git").exists():
        sha = subprocess.check_output(
            ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
        ).strip()
    else:
        sha = json.loads((source / "source.json").read_text(encoding="utf-8"))["commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid upstream commit SHA")

    # Build every profile before replacing any of the last successful outputs.
    files = {}
    for name in PROFILES:
        extension = build_profile(name, inputs)
        header = f"Source: {SOURCE_REPO}@{sha} / {name}.ini"
        files[f"{name}.yaml"] = (
            f"# {header}\n# Generated by scripts/convert_ini.py; do not edit manually.\n"
            + yaml.safe_dump(extension, allow_unicode=True, sort_keys=False, width=120)
        )
        files[f"{name}.js"] = render_script(extension, header)
        print(f"{name}: {len(extension['proxy-groups'])} groups, "
              f"{len(extension['rules'])} rules, {len(extension['rule-providers'])} remote rule providers")
    files["Merge.yaml"] = files["config.yaml"]
    files["Script.js"] = files["config.js"]
    for filename, content in inputs.items():
        files[f"upstream/{filename}"] = content
    metadata = {
        "repository": SOURCE_REPO,
        "branch": SOURCE_BRANCH,
        "commit": sha,
        "files": {name: hashlib.sha256(content.encode("utf-8")).hexdigest()
                  for name, content in inputs.items()},
    }
    files["upstream/source.json"] = json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
    for filename, content in files.items():
        path = output / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Generated four YAML/JS pairs and default aliases from {sha}")


if __name__ == "__main__":
    main()
