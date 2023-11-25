all: clean prepare build start delay10s test

delay10s:
	sleep 10

sys-packages:
	# sudo apt install -y docker-compose
	sudo apt install python3-pip -y
	sudo pip3 install pipenv

pipenv:
	pipenv install -r requirements-dev.txt

prepare: clean sys-packages pipenv build

build:
	docker-compose build

rebuild:
	docker-compose build --force-rm

run:
	docker-compose up -d

start: run

restart:
	docker-compose restart

run-atm:
	pipenv run python atm/atm.py

run-fps:
	pipenv run python fps/fps.py

run-drone:
	pipenv run python drone/drone.py

logs:
	docker-compose logs -f --tail 100

test:
	pipenv run pytest -sv

stop:
	docker-compose stop

restart: stop start

clean:
	@pipenv --rm || echo no environment to remove
	@rm -rf Pipfile* || no pipfiles to remove
	@docker-compose down || echo no containers to remove	