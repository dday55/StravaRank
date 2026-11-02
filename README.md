# ⏱️ StravaRank · 全球 Strava 会员价格追踪与跨区索引

<div align="center">

![StravaRank Preview](assets/og-image.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/Auto--Update-Daily%2000:00%20UTC-emerald.svg)](.github/workflows/update-pricing.yml)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)
[![OpenTheRank Mode](https://img.shields.io/badge/Style-Neo--Fintech-slate.svg)](#)

**实时追踪全球 27+ 个国家地区的 Strava 官方订阅定价、每日外汇自动折算与国内合规跨区指南**

[功能特性](#-功能特性) • [本地运行](#-本地运行-docker--orbstack) • [自动化架构](#-自动化数据流水线-方案-b) • [目录结构](#-目录结构) • [标价更新](#-各国标价更新指南)

</div>

---

## 🌟 功能特性

- **多币种实时折算**：支持 CNY (¥)、USD ($)、EUR (€)、GBP (£)、JPY (¥) 及各国本币原币一键切换，汇率每日定时自动同步。
- **全周期套餐矩阵**：涵盖「个人年付 (Annual)」、「个人月付 (Monthly)」、「4人家庭拼车 (人均)」、「家庭组 (年总价)」及「学生半价 (50% Off)」。
- **首屏快速测算卡 (Live Estimator)**：首屏即时组装国家与套餐，实时呈现折合年费、月均开销、较美区节省百分比与推荐支付方式。
- **实操门槛与防风控研判**：
  - 🟢 **容易入门**：如日本区（支持国内 JCB 信用卡直刷及正规日区礼品卡）。
  - 🟡 **中等门槛**：如土耳其区（支持土区 Apple ID + 礼品卡充值，个人性价比之王）。
  - 🔴 **严格锁卡**：如尼日利亚、埃及（强校验发卡行本地 BIN 码，拒付外卡，不建议折腾）。
- **家庭组 4 人车队模拟器**：支持 2~4 人动态滑块计算各地区车队人均支出及相比单买美区年费**每年集体立省金额**。
- **Linear 风格全维度抽屉**：点击任意国家行弹出该区支付渠道实测、税费注意事项及三步实操指引。
- **原创合规品牌标识**：采用「竞技配速秒表」原创设计，彻底绝缘官方商标侵权风险。
- **完整 SEO 与 PWA 资产**：内置矢量 Favicon、Apple Touch Icon、1200x630 Open Graph 社交卡片及 Schema.org 结构化数据。

---

## 🚀 自动化数据流水线 (方案 B)

项目采用**分层自动化更新机制**：

```
[ 权威金融外汇源 API ] ──► (每天早 08:00 自动抓取)
          │
          ▼
[ scripts/update_pricing.py ]
          │  1. 覆盖 27+ 币种最新牌价 (USD/CNY/EUR/JPY/TRY...)
          │  2. 自动更新时间戳为当日日期 (YYYY-MM-DD)
          │  3. 重新对齐各国折算价与相对美区的优惠幅度
          ▼
   生成 / 更新 data.json
          │
          ▼
[ 前端页面 (GitHub Pages / Docker) ]
   - 顶部导航栏动态显示:「1 USD ≈ 6.66 CNY · 每日同步于 2026-11-02」
   - 所有折算价格、排行榜名次全部依据最新汇率自动重算
```

### 1. 每日实时汇率 (100% 全自动)
- **调度排期**：GitHub Actions 每日北京时间早 08:00 (UTC 00:00) 准时执行；
- **数据源**：直连全球开放金融外汇接口（`open.er-api.com` / 欧洲央行 ECB 源），零 Key 免配置；
- **效果**：检测到变动自动执行 `git commit` 并推回仓库。

### 2. 各国官方标价更新
- **每周日自动巡检**：工作流每周日凌晨会自动触发 `scripts/scrape_appstore_prices.py`，遍历 Apple 官方 App Store 全球 27 区公开页面，检测标价变动；
- **网页直接编辑**：若知悉某国调价，直接在 GitHub 网页端点击 `data.json` 铅笔图标修改数值并保存即可；
- **手动一键巡检**：在 GitHub 仓库 **Actions -> Auto-update Global Pricing** 点击 **Run workflow** 即可全网深度扫描。

---

## 🛠️ 本地运行 (Docker / OrbStack)

### 方式 1：使用 Docker Compose
```bash
# 启动本地服务
docker compose up -d

# 访问地址
# http://localhost:8088
```

### 方式 2：使用 Makefile 快捷指令
```bash
make update             # 立即拉取全球最新外汇汇率并更新 data.json
make scrape-prices      # 扫描 27 国 App Store 标价变动并试运行检查
make scrape-prices-apply# 扫描并将官方标价变动应用至数据表
make run                # 启动 Docker 容器
make stop               # 停止 Docker 容器
```

---

## 📁 目录结构

```text
strava-pricing-rank/
├── .github/
│   └── workflows/
│       └── update-pricing.yml    # GitHub Actions 每日汇率更新工作流
├── scripts/
│   ├── update_pricing.py         # 每日汇率拉取与排名重算脚本
│   └── scrape_appstore_prices.py # App Store 各国官方标价爬取脚本
├── index.html                    # 前端单页应用 (Neo-Fintech 风格)
├── data.json                     # 核心价格与汇率数据库
├── favicon.svg                   # 矢量品牌图标 (竞技配速秒表)
├── favicon-32x32.png             # 32x32 经典网页图标
├── favicon-16x16.png             # 16x16 标签栏图标
├── favicon.ico                   # 兼容图标
├── apple-touch-icon.png          # iOS Safari 桌面主屏幕图标
├── og-image.png                  # 1200x630 社交分享预览底图
├── site.webmanifest              # PWA 清单文件
├── robots.txt                    # 搜索引擎爬取协议
├── sitemap.xml                   # 站点地图
├── Dockerfile                    # 轻量 Nginx 镜像构建
├── docker-compose.yml            # 容器编排配置
├── Makefile                      # 本地自动化操作指令集
├── LICENSE                       # MIT 开源协议
└── README.md                     # 项目说明文档
```

---

## 🚢 部署上线推荐

本项目为纯静态结构加定时工作流，支持多种免运维免费部署：

1. **GitHub Pages (推荐)**：
   - 仓库设置中开启 **Settings -> Pages**，分支选择 `main`，目录选择 `/ (root)` 即可获得免费 HTTPS 域名。
2. **Cloudflare Pages / Vercel**：
   - 直接导入 GitHub 仓库，构建命令留空，静态目录设为根目录即可享受全球 CDN 加速。
3. **自建 Docker (OrbStack / 云服务器)**：
   - 执行 `docker compose up -d` 即可在指定端口持久化运行。

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源发布。所有第三方商标权归其对应官方持有，仅供耐力运动爱好者参考学习。
