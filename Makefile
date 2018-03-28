DOCKER_IMAGE = fatz/aws-iam-auditing
DOCKER_TAG := $(shell git rev-parse --short HEAD)



init:
	pip install -r requirements.txt

test:
	nosetests tests

docker.build:
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker.push:
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)
