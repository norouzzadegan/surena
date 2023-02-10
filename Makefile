.PHONY: test

test:
	py.test test

check_pep:
	flake8 .

check_imports_order:
	isort -c .

sort_imports:
	isort .

install_develop:
	pip3 install -e .[dev]

uninstall_develop:
	pip3 uninstall -y "$$(python3 setup.py --name)"

install:
	pip3 install .[dev]

uninstall:
	pip3 uninstall -y "$$(python3 setup.py --name)"

clean:
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist