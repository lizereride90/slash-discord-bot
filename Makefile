install:
	python3 -m pip install -r requirements.txt

check:
	python3 -m py_compile bot.py config.py core/*.py services/*.py utils/*.py api/*.py cogs/**/*.py
	python3 scripts/verify.py
	python3 scripts/quality_report.py

run:
	python3 bot.py

deploy:
	python3 deploy.py
