.PHONY: update scrape-prices run stop restart

# 1. 每日更新：拉取全球最新外汇汇率并重新折算排名
update:
	python3 scripts/update_pricing.py

# 2. 深度扫描：爬取 27 国 Apple App Store 官方内购标价变动 (试运行)
scrape-prices:
	python3 scripts/scrape_appstore_prices.py --dry-run

# 3. 深度扫描并直接应用标价变动
scrape-prices-apply:
	python3 scripts/scrape_appstore_prices.py
	python3 scripts/update_pricing.py

# 启动 Docker 容器服务 (OrbStack)
run:
	docker compose up -d

# 重启容器
restart:
	docker compose restart

# 停止容器
stop:
	docker compose down
