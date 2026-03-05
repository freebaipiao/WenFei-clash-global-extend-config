def convert_rules(input_path, output_path):
    rules = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            # 只处理以 - 开头的规则
            if line.startswith("-"):
                rule = line.lstrip("-").strip()
                rules.append(rule)

    if not rules:
        print("未找到有效规则")
        return

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("  const MyRules = [\n")

        for i, rule in enumerate(rules):
            if i == len(rules) - 1:
                f.write(f'    "{rule}"\n')
            else:
                f.write(f'    "{rule}",\n')

        f.write("  ];\n")

    print(f"转换完成，共 {len(rules)} 条规则")
    print(f"输出文件：{output_path}")


if __name__ == "__main__":
    input_file = "raw.txt"
    output_file = "rules.js"

    convert_rules(input_file, output_file)
