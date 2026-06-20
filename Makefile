install:
	pip install -r backend/requirements.txt
	npm install --prefix frontend

dev:
	./scripts/dev.sh

build:
	docker build -t rag-backend -f Dockerfile.backend .
	docker build -t rag-frontend -f Dockerfile.frontend .

test:
	pytest backend/tests
	npm test --prefix frontend

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	docker-compose down --volumes --remove-orphans
	rm -rf backend/__pycache__ frontend/.next