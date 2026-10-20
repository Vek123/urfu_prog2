.PHONY: run-server run-rest run-service1 run-service2

run-server:
	python ./src/manage.py runserver

run-rest:
	python ./src/manage.py runserver 127.0.0.1:8082

run-service1:
	python ./src/manage.py runserver 127.0.0.1:8082

run-service2:
	python ./service2/src/manage.py runserver 127.0.0.1:8084
