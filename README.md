# 功能
自动化完成yaml版规则至js覆写规则的样式转换

# 样例
输入
```
  - DOMAIN-SUFFIX,acl4.ssr,🎯 全球直连
  - DOMAIN-SUFFIX,ip6-localhost,🎯 全球直连
  - DOMAIN-SUFFIX,ip6-loopback,🎯 全球直连
  - DOMAIN-SUFFIX,internal,🎯 全球直连
```

输出
```
  const MyRules = [
    "DOMAIN-SUFFIX,acl4.ssr,🎯 全球直连",
    "DOMAIN-SUFFIX,ip6-localhost,🎯 全球直连",
    "DOMAIN-SUFFIX,ip6-loopback,🎯 全球直连",
    "DOMAIN-SUFFIX,internal,🎯 全球直连"
  ];
```
