excludes = \*~ \*.pyc .cache/\* test_\* __pycache__/\*

TEST_RESULTS_FOLDER ?= ./test_results

.PHONY: clean
clean:
	find . -type f -name "*.pyc" -delete
	rm -fr test_results

.PHONY: test
test:
	mkdir -p ${TEST_RESULTS_FOLDER}
	poetry run pytest --junitxml=${TEST_RESULTS_FOLDER}/xunit.xml --cov=flask_boto3 --cov-report html:${TEST_RESULTS_FOLDER}/html
