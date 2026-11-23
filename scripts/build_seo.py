#!/usr/bin/env python3
"""
Generate crawlable SEO content from the live pricing dataset.

The page remains a static GitHub Pages site, but the initial HTML includes
current country prices, FAQs and structured data instead of waiting for
client-side JavaScript to populate them.
"""

import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "data.json")
INDEX_PATH = os.path.join(ROOT, "index.html")
SITEMAP_PATH = os.path.join(ROOT, "sitemap.xml")

BASE_URL = "https://dday55.github.io/StravaRank/"
OG_IMAGE = f"{BASE_URL}assets/og-image.png"


def replace_block(text, name, content):
    start = f"<!-- {name}_START -->"
    end = f"<!-- {name}_END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{content.rstrip()}\n{end}"
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"Missing SEO block markers: {name}")
    return updated


def number(value, decimals=0):
    rounded = round(float(value), decimals)
    if decimals == 0:
        return f"{rounded:,.0f}"
    return f"{rounded:,.{decimals}f}".rstrip("0").rstrip(".")


def local_price(value):
    value = float(value)
    return number(value, 0) if value.is_integer() else number(value, 2)


def percent(value):
    value = float(value)
    if abs(value) < 0.05:
        return "基准"
    return f"{value:+.1f}%"


def rank_badge(rank):
    if rank == 1:
        classes = "bg-amber-100 text-amber-800 border-amber-300"
    elif rank == 2:
        classes = "bg-slate-200 text-slate-800 border-slate-300"
    elif rank == 3:
        classes = "bg-amber-50 text-amber-900 border-amber-200"
    else:
        return f'<span class="text-slate-400 font-mono font-semibold text-xs">#{rank}</span>'
    return (
        f'<span class="w-6 h-6 rounded-md {classes} border inline-flex items-center '
        f'justify-center font-black text-xs font-mono shadow-sm">{rank}</span>'
    )


def render_table(countries):
    rows = []
    for item in countries:
        diff = float(item["savings_pct_calc"])
        diff_class = (
            "badge-diff-neg"
            if diff < -0.1
            else ("badge-diff-pos" if diff > 0.1 else "badge-diff-zero")
        )
        difficulty = item.get("difficulty", "medium")
        dot_class = {
            "easy": "bg-emerald-500",
            "medium": "bg-amber-500",
            "hard": "bg-rose-500",
        }.get(difficulty, "bg-slate-500")
        text_class = {
            "easy": "text-emerald-700",
            "medium": "text-amber-700",
            "hard": "text-rose-700",
        }.get(difficulty, "text-slate-700")
        methods = "".join(
            f'<span class="px-2 py-0.5 rounded bg-slate-50 text-[11px] '
            f'text-slate-600 border border-slate-200">{html.escape(method)}</span>'
            for method in item.get("methods", [])
        )
        baseline_badge = (
            '<span class="text-[9px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 '
            'border border-slate-200 uppercase font-mono">基准</span>'
            if item["id"] == "US"
            else ""
        )
        rows.append(
            f"""
            <tr class="hover:bg-slate-50 transition duration-150">
              <td class="py-4 pl-5 pr-2 text-center">{rank_badge(int(item["rank"]))}</td>
              <td class="py-4 px-3 whitespace-nowrap">
                <div class="flex items-center space-x-2.5">
                  <span class="text-xl leading-none" aria-hidden="true">{item.get("flag", "")}</span>
                  <div>
                    <div class="font-bold text-slate-900 flex items-center gap-1.5">
                      <span>{html.escape(item["country"])}</span>{baseline_badge}
                    </div>
                    <div class="text-[11px] text-slate-400 font-mono">{html.escape(item.get("country_en", ""))} · {html.escape(item["currency"])}</div>
                  </div>
                </div>
              </td>
              <td class="py-4 px-3 font-mono text-xs whitespace-nowrap">
                <div class="font-semibold text-slate-800">{html.escape(item["symbol"])} {local_price(item["annual"])}</div>
                <div class="text-[10px] text-slate-400">年付</div>
              </td>
              <td class="py-4 px-3 text-right whitespace-nowrap">
                <span class="text-base font-black text-slate-900 font-mono tracking-tight">¥{number(item["price_cny_calc"], 1)}</span>
                <span class="text-[10px] text-slate-400 block font-mono">CNY</span>
              </td>
              <td class="py-4 px-3 text-right font-mono text-xs text-slate-600 whitespace-nowrap">
                ¥{number(float(item["price_cny_calc"]) / 12, 1)}<span class="text-[10px] text-slate-400 block">/月</span>
              </td>
              <td class="py-4 px-3 text-center whitespace-nowrap">
                <span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold font-mono {diff_class}">{percent(diff)}</span>
              </td>
              <td class="py-4 px-3 hidden lg:table-cell whitespace-nowrap">
                <div class="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div class="h-full rounded-full {'bg-emerald-500' if diff < 0 else 'bg-rose-500'}" style="width: {max(5, min(100, 100 - abs(diff))):.0f}%"></div>
                </div>
              </td>
              <td class="py-4 px-3 whitespace-nowrap min-w-[110px]">
                <div class="inline-flex items-center space-x-1.5 text-xs font-semibold whitespace-nowrap {text_class}">
                  <span class="w-1.5 h-1.5 rounded-full shrink-0 {dot_class}"></span>
                  <span class="whitespace-nowrap">{html.escape(item.get("difficulty_text", ""))}</span>
                </div>
              </td>
              <td class="py-4 px-3 hidden md:table-cell text-xs text-slate-500">
                <div class="flex flex-wrap gap-1">{methods}</div>
              </td>
              <td class="py-4 pr-5 pl-2 text-right whitespace-nowrap min-w-[76px] w-20">
                <span class="px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-500 inline-flex items-center gap-1 ml-auto whitespace-nowrap shrink-0">详情</span>
              </td>
            </tr>"""
        )
    return "\n".join(rows).strip()


def render_summary(data):
    countries = data["countries"]
    lowest = countries[0]
    turkey = next((item for item in countries if item["id"] == "TR"), lowest)
    japan = next((item for item in countries if item["id"] == "JP"), None)
    us = next((item for item in countries if item["id"] == "US"), None)
    updated = html.escape(data["updated_at"])
    if lowest["id"] == turkey["id"]:
        turkey_line = "该地区也是目前更适合个人实操的低价选择。"
    else:
        turkey_line = (
            f'<strong>{html.escape(turkey["country"])}区</strong>个人年付为 '
            f'{html.escape(turkey["symbol"])}{local_price(turkey["annual"])} {html.escape(turkey["currency"])}，'
            f'折合约 <strong>¥{number(turkey["price_cny_calc"], 1)}</strong>。'
        )
    japan_line = ""
    if japan:
        japan_line = (
            f'重视支付稳定性的用户可关注{html.escape(japan["country"])}区，'
            f'年付约 ¥{number(japan["price_cny_calc"], 1)}。'
        )
    us_line = ""
    if us:
        us_line = (
            f'美国区官方基准为 <strong>${local_price(us["annual"])}/年</strong>'
            f'（约 ¥{number(us["price_cny_calc"], 1)}）。'
        )

    return f"""
<section id="price-insights" aria-labelledby="price-insights-title" class="neo-card rounded-2xl p-5 sm:p-6 scroll-mt-24">
  <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
    <div class="max-w-3xl">
      <p class="text-[11px] font-bold uppercase tracking-[0.16em] text-strava">价格结论 · 数据更新于 <time datetime="{updated}">{updated}</time></p>
      <h2 id="price-insights-title" class="mt-2 text-xl sm:text-2xl font-black tracking-tight text-slate-900">2026 Strava 会员哪个国家最便宜？</h2>
      <p class="mt-3 text-sm leading-7 text-slate-600">
        按个人年付价格折算，当前最低为 <strong>{html.escape(lowest["country"])}</strong>：
        {html.escape(lowest["symbol"])}{local_price(lowest["annual"])} {html.escape(lowest["currency"])}，
        约 <strong>¥{number(lowest["price_cny_calc"], 1)}/年</strong>。{turkey_line}
        {japan_line}{us_line}
      </p>
    </div>
    <div class="shrink-0 rounded-xl border border-orange-200 bg-orange-50 px-4 py-3 text-xs text-orange-950">
      <div class="font-bold">当前最低个人年付</div>
      <div class="mt-1 font-mono text-xl font-black">¥{number(lowest["price_cny_calc"], 1)}</div>
      <div class="mt-1 text-orange-800">较美区基准低 {abs(float(lowest["savings_pct_calc"])):.1f}% · 已覆盖 {len(countries)} 个地区</div>
    </div>
  </div>
  <p class="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs font-semibold">
    <a class="text-strava hover:underline" href="#pricing-ranking">查看完整 {len(countries)} 国价格排行榜</a>
    <a class="text-strava hover:underline" href="#family-calculator">计算家庭组 4 人人均</a>
    <a class="text-strava hover:underline" href="#faq">阅读跨区订阅 FAQ</a>
  </p>
</section>""".strip()


def render_meta_description(data):
    countries = data["countries"]
    lowest = countries[0]
    us = next((item for item in countries if item["id"] == "US"), None)
    us_price = (
        f"美区 ${local_price(us['annual'])}/年，"
        if us
        else ""
    )
    description = (
        f"Strava 会员全球 {len(countries)} 国价格实时对比："
        f"{lowest['country']}区年付约 ¥{number(lowest['price_cny_calc'], 1)}，"
        f"{us_price}涵盖月付、家庭组与学生优惠。"
    )
    return f'<meta name="description" content="{html.escape(description, quote=True)}">'


def render_hero_summary(data):
    countries = data["countries"]
    lowest = countries[0]
    us = next((item for item in countries if item["id"] == "US"), None)
    baseline = (
        f"官方基准（美区）年费为 ${local_price(us['annual'])}"
        f"（约 ¥{number(us['price_cny_calc'], 1)}）。"
        if us
        else ""
    )
    return (
        '<p class="text-sm sm:text-base text-slate-600 leading-relaxed font-normal max-w-2xl">\n'
        f"          {baseline}当前最低为 {html.escape(lowest['country'])}区，"
        f"约 <strong class=\"text-slate-900 font-bold\">¥{number(lowest['price_cny_calc'], 1)}/年</strong>；"
        f"最高价地区约 ¥{number(countries[-1]['price_cny_calc'], 1)}/年。"
        "实时汇率换算、家庭组人均成本与跨区实操门槛每日更新。\n"
        "        </p>"
    )


def faq_entries(data):
    countries = data["countries"]
    lowest = countries[0]
    turkey = next((item for item in countries if item["id"] == "TR"), lowest)
    japan = next((item for item in countries if item["id"] == "JP"), None)
    turkey_text = (
        f'土耳其区个人年付为 {turkey["symbol"]}{local_price(turkey["annual"])} '
        f'{turkey["currency"]}，约 ¥{number(turkey["price_cny_calc"], 1)}/年。'
    )
    lowest_text = (
        "当前最低价正是土耳其区。"
        if lowest["id"] == turkey["id"]
        else turkey_text
    )
    japan_text = (
        f'日本区个人年付约 ¥{number(japan["price_cny_calc"], 1)}，'
        if japan
        else ""
    )
    entries = [
        {
            "question": "Strava 会员多少钱？哪个国家最便宜？",
            "answer_html": (
                f'截至 <time datetime="{html.escape(data["updated_at"])}">{html.escape(data["updated_at"])}</time>，'
                f'个人年付折合人民币最低的是{html.escape(lowest["country"])}区，'
                f'约 <strong>¥{number(lowest["price_cny_calc"], 1)}/年</strong>。{lowest_text}'
                f'美国区官方基准为 $79.99/年；实际扣款以 Apple 结算页和实时汇率为准。'
            ),
            "answer_text": (
                f'截至 {data["updated_at"]}，个人年付折合人民币最低的是{lowest["country"]}区，'
                f'约 ¥{number(lowest["price_cny_calc"], 1)}/年。{lowest_text}'
                f'美国区官方基准为 79.99 美元/年；实际扣款以 Apple 结算页和实时汇率为准。'
            ),
        },
        {
            "question": "中国大陆可以直接订阅 Strava 吗？",
            "answer_html": (
                "Strava 暂未接入中国大陆 App Store 的内购结算。常见做法是使用土耳其、日本或美国等"
                "外区 Apple ID 在 App 内订阅；历史运动记录和现有 Strava 账号通常不受影响。跨区前应确认"
                "礼品卡来源、账号地区与续费方式，避免因支付风控导致自动续费失败。"
            ),
            "answer_text": (
                "Strava 暂未接入中国大陆 App Store 的内购结算。常见做法是使用土耳其、日本或美国等"
                "外区 Apple ID 在 App 内订阅；历史运动记录和现有 Strava 账号通常不受影响。跨区前应确认"
                "礼品卡来源、账号地区与续费方式，避免因支付风控导致自动续费失败。"
            ),
        },
        {
            "question": "土区 vs 日区：个人与家庭订阅该如何选择？",
            "answer_html": (
                f"追求最低个人年费可优先比较土耳其区，目前约 ¥{number(turkey['price_cny_calc'], 1)}；"
                f"{japan_text}日本区通常更容易使用 JCB 信用卡或本地礼品卡，支付稳定性更好。"
                "家庭计划按年收费并最多覆盖 4 个独立账号，可先用页内家庭组计算器比较目标地区人均成本。"
            ),
            "answer_text": (
                f"追求最低个人年费可优先比较土耳其区，目前约 ¥{number(turkey['price_cny_calc'], 1)}；"
                f"{japan_text}日本区通常更容易使用 JCB 信用卡或本地礼品卡，支付稳定性更好。"
                "家庭计划按年收费并最多覆盖 4 个独立账号，可先用页内家庭组计算器比较目标地区人均成本。"
            ),
        },
        {
            "question": "Strava 家庭计划（Family Plan）拼车有哪些规则？",
            "answer_html": (
                "家庭计划最多允许 4 人加入，每位成员使用自己的 Strava 账号，运动历史、心率与隐私数据相互独立。"
                "车主发出邀请后，成员需接受邀请；成员通常需要与车主位于同一国家/地区。计划按年收费，"
                "人员不足 4 人时总价通常不变。"
            ),
            "answer_text": (
                "家庭计划最多允许 4 人加入，每位成员使用自己的 Strava 账号，运动历史、心率与隐私数据相互独立。"
                "车主发出邀请后，成员需接受邀请；成员通常需要与车主位于同一国家/地区。计划按年收费，"
                "人员不足 4 人时总价通常不变。"
            ),
        },
        {
            "question": "为什么不建议只按最低名义价格选择尼日利亚或埃及区？",
            "answer_html": (
                "部分低价区对发卡行 BIN、账号地区和支付方式限制严格，境外银行卡、虚拟卡或礼品卡可能被拒付。"
                "选择地区时应同时比较价格、支付成功率、续费稳定性和退款风险，而不只看名义标价。"
            ),
            "answer_text": (
                "部分低价区对发卡行 BIN、账号地区和支付方式限制严格，境外银行卡、虚拟卡或礼品卡可能被拒付。"
                "选择地区时应同时比较价格、支付成功率、续费稳定性和退款风险，而不只看名义标价。"
            ),
        },
    ]
    return entries


def render_faq(entries):
    blocks = []
    for index, entry in enumerate(entries):
        blocks.append(
            f"""
          <details class="group p-3.5 rounded-xl bg-slate-50 border border-slate-200 open:border-strava/50 transition"{' open' if index == 0 else ''}>
            <summary class="font-bold text-slate-900 cursor-pointer flex items-center justify-between list-none">
              <span class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-strava"></span>
                {html.escape(entry["question"])}
              </span>
              <span class="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
            </summary>
            <p class="text-slate-600 mt-2.5 leading-relaxed pl-4 border-l-2 border-strava">{entry["answer_html"]}</p>
          </details>"""
        )
    return "\n".join(blocks).strip()


def render_schema(data, faq):
    countries = data["countries"]
    lowest = countries[0]
    usd_prices = [
        float(item["annual"]) / float(data["rates"][item["currency"]])
        for item in countries
    ]
    item_list = []
    for item in countries[:10]:
        item_list.append(
            {
                "@type": "ListItem",
                "position": int(item["rank"]),
                "item": {
                    "@type": "Product",
                    "name": f'Strava 会员（{item["country"]}区个人年付）',
                    "brand": {"@type": "Brand", "name": "Strava"},
                    "offers": {
                        "@type": "Offer",
                        "price": f'{float(item["annual"]):.2f}',
                        "priceCurrency": item["currency"],
                        "availability": "https://schema.org/InStock",
                        "url": f"{BASE_URL}#pricing-ranking",
                    },
                },
            }
        )

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}#website",
                "url": BASE_URL,
                "name": "StravaRank",
                "alternateName": "Strava 全球会员价格对比",
                "inLanguage": "zh-CN",
                "description": "追踪全球 Strava 会员官方定价、汇率换算与跨区订阅门槛。",
            },
            {
                "@type": "WebPage",
                "@id": f"{BASE_URL}#webpage",
                "url": BASE_URL,
                "name": "Strava 会员多少钱？2026 全球 27 国价格对比与跨区指南",
                "description": "Strava 会员全球 27 个国家与地区价格实时对比，覆盖个人年付、月付、家庭组和学生优惠。",
                "dateModified": data["updated_at"],
                "inLanguage": "zh-CN",
                "isPartOf": {"@id": f"{BASE_URL}#website"},
                "primaryImageOfPage": {"@id": f"{BASE_URL}#primaryimage"},
                "breadcrumb": {"@id": f"{BASE_URL}#breadcrumb"},
            },
            {
                "@type": "ImageObject",
                "@id": f"{BASE_URL}#primaryimage",
                "url": OG_IMAGE,
                "width": 1200,
                "height": 630,
                "caption": "Strava 会员全球各国价格实时对比看板",
            },
            {
                "@type": "WebApplication",
                "@id": f"{BASE_URL}#webapp",
                "name": "StravaRank - Strava 全球会员价格追踪与比价",
                "url": BASE_URL,
                "applicationCategory": ["SportsApplication", "UtilitiesApplication"],
                "operatingSystem": "Any",
                "browserRequirements": "需要支持 JavaScript",
                "isAccessibleForFree": True,
                "inLanguage": "zh-CN",
                "description": f"实时追踪全球 {len(countries)} 个国家与地区 Strava 官方订阅定价、汇率换算与跨区实操索引。",
                "offers": {
                    "@type": "AggregateOffer",
                    "priceCurrency": "USD",
                    "lowPrice": f"{min(usd_prices):.2f}",
                    "highPrice": f"{max(usd_prices):.2f}",
                    "offerCount": len(countries),
                },
            },
            {
                "@type": "Organization",
                "@id": f"{BASE_URL}#organization",
                "name": "StravaRank",
                "url": BASE_URL,
                "logo": f"{BASE_URL}assets/icons/apple-touch-icon.png",
                "sameAs": ["https://github.com/dday55/StravaRank"],
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{BASE_URL}#breadcrumb",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "首页",
                        "item": BASE_URL,
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Strava 会员全球价格对比",
                        "item": f"{BASE_URL}#pricing-ranking",
                    },
                ],
            },
            {
                "@type": "FAQPage",
                "@id": f"{BASE_URL}#faq-schema",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": entry["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": entry["answer_text"],
                        },
                    }
                    for entry in faq
                ],
            },
            {
                "@type": "ItemList",
                "@id": f"{BASE_URL}#price-list",
                "name": "Strava 个人年付价格最低的 10 个地区",
                "numberOfItems": len(item_list),
                "itemListOrder": "https://schema.org/ItemListOrderAscending",
                "itemListElement": item_list,
            },
        ],
    }
    formatted = json.dumps(schema, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{formatted}\n  </script>'


def render_sitemap(data):
    lastmod = data["updated_at"]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>{BASE_URL}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
    <image:image>
      <image:loc>{OG_IMAGE}</image:loc>
      <image:title>Strava 会员全球各国价格实时对比</image:title>
    </image:image>
  </url>
</urlset>
"""


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)
    with open(INDEX_PATH, "r", encoding="utf-8") as file:
        page = file.read()

    data["countries"] = sorted(data["countries"], key=lambda item: int(item["rank"]))
    faq = faq_entries(data)

    page = replace_block(page, "SEO_HERO_SUMMARY", render_hero_summary(data))
    page = replace_block(page, "SEO_DESCRIPTION", render_meta_description(data))
    page = replace_block(page, "SEO_SUMMARY", render_summary(data))
    page = replace_block(page, "SEO_STATIC_TABLE", render_table(data["countries"]))
    page = replace_block(page, "SEO_FAQ", render_faq(faq))
    page = replace_block(page, "SEO_STRUCTURED_DATA", render_schema(data, faq))

    with open(INDEX_PATH, "w", encoding="utf-8") as file:
        file.write(page)
    with open(SITEMAP_PATH, "w", encoding="utf-8") as file:
        file.write(render_sitemap(data))

    print(
        f"SEO snapshot generated: {len(data['countries'])} countries, "
        f"updated {data['updated_at']}, lowest {data['countries'][0]['country']}."
    )


if __name__ == "__main__":
    main()
