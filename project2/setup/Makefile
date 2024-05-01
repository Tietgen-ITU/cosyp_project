build-postgres:
	docker buildx build --push --platform linux/amd64,linux/arm64 -t arne4545/cosyp-psql:latest -f Dockerfile.psql .

interact-postgres:
	docker run -it arne4545/cosyp-psql:latest bash

build-elastic:
	docker buildx build --push --platform linux/amd64,linux/arm64 -t arne4545/cosyp-elastic:latest -f Dockerfile.elastic .

interact-elastic:
	docker run -it arne4545/cosyp-elastic:latest bash

spawn-postgres:
	docker run --name cosyp-postgres -p 127.0.0.1:5049:5432 -d cosyp-psql:latest

connect-postgres:
	docker exec -it cosyp-postgres psql -d cosyp -U cosyp-sa

connect-postgres-local:
	psql postgresql://cosyp-sa:123@localhost:5049/cosyp

build-elasticsearch:
	docker build -t cosyp-elastic:latest -f Dockerfile.elastic .

spawn-elasticsearch:
	docker run --name cosyp-elastic -p 127.0.0.1:9200:9200 -p 127.0.0.1:9300:9300 -d cosyp-elastic:latest
