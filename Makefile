.PHONY: start_dev

start_dev:
	bash -c 'DEBUG=1 PYTHONPATH=src python src/app/main.py'