SHELL := /bin/bash
# NOTE: this should always be the current target version that will be used in making virtualenvs
# we use the Ubuntu binary naming convention since that is our target environment, but this may not work
# in environments where the binary is named differently - such as "python38"
PYTHON := python3.8

ifndef VERBOSE
.SILENT:
endif

#***Static Code Analysis***
analyze_code_with_log: fix_code_format run_mypy_with_log run_flake8_with_log
analyze_code_with_status: run_flake8_with_status run_mypy_with_status

fix_code_format:
	@source venv/bin/activate && autoflake -i -r --remove-unused-variables --remove-all-unused-imports --exclude 'venv,__pycache__' . && echo "autoflake formatter ran successfully."
	@source venv/bin/activate && black -l 120 --force-exclude '/(venv)/' -q . && echo "black formatter ran successfully."
	@source venv/bin/activate && autopep8 --global-config setup.cfg --max-line-length 120 . && echo "autopep8 formatter ran successfully."


define mypy_command
	source venv/bin/activate && mypy . --config-file setup.cfg --no-error-summary
endef

run_mypy_with_log:
	if [ -z "$(shell $(mypy_command) | tee mypy_errors.txt)" ]; then \
		echo -e "\033[32mNo issue was found by mypy.\033[m"; \
		rm mypy_errors.txt; \
	else \
		echo -e "Mypy found some issues. \033[31mPlease check mypy_errors.txt.\033[0m"; \
	fi

define flake8_command
	source venv/bin/activate && flake8 .
endef

run_flake8_with_log:
	if [ -z "$(shell $(flake8_command) | tee flake8_errors.txt)" ]; then \
		echo -e "\033[32mNo issue was found by flake8.\033[m"; \
		rm flake8_errors.txt; \
	else \
		echo -e "Flake8 found some issues. \033[31mPlease check flake8_errors.txt.\033[0m"; \
	fi
