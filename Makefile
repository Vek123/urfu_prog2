.PHONY: run-server run-rest

run-server:
	python ./src/manage.py runserver

run-rest:
	python ./src/manage.py runserver 127.0.0.1:8082
