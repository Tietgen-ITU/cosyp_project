build-postgres:
	docker build -t cosyp-psql:latest -f Dockerfile.psql . 

interact-postgres:
	docker run -it cosyp-psql:latest bash

spawn-postgres:
	docker run --name cosyp-postgres -p 127.0.0.1:5049:5432 -d cosyp-psql:latest

connect-postgres:
	docker exec -it cosyp-postgres psql -d cosyp -U cosyp-sa

connect-postgres-local:
	psql postgresql://cosyp-sa:123@localhost:5049/cosyp
