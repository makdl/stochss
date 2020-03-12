
include .env
include jupyterhub/.env

.DEFAULT_GOAL=build_and_run

network:
	@docker network inspect $(DOCKER_NETWORK_NAME) >/dev/null 2>&1 || docker network create $(DOCKER_NETWORK_NAME)

volumes:
	@docker volume inspect $(DATA_VOLUME_HOST) >/dev/null 2>&1 || docker volume create --name $(DATA_VOLUME_HOST)
	@docker volume inspect $(DB_VOLUME_HOST) >/dev/null 2>&1 || docker volume create --name $(DB_VOLUME_HOST)

jupyterhub/secrets/oauth.env:
	@echo "Need oauth.env file in secrets with Google parameters"
	@echo "Using an empty file for now..."
	@echo "OAUTH_CALLBACK_URL=''" >> $@

jupyterhub/secrets/jupyterhub.crt:
	@echo "Need an SSL certificate in secrets/jupyterhub.crt"
	@exit 1

jupyterhub/secrets/jupyterhub.key:
	@echo "Need an SSL key in secrets/jupyterhub.key"
	@exit 1

check-cert: jupyterhub/secrets/jupyterhub.key jupyterhub/secrets/jupyterhub.crt

jupyterhub/secrets/postgres.env:
	@echo "Generating postgres password in $@"
	@echo "POSTGRES_PASSWORD=$(shell openssl rand -hex 32)" > $@

userlist:
	@echo "Add usernames, one per line, to ./userlist, such as:"
	@echo "    zoe admin"
	@echo "    wash"
	@exit 1

check-files: jupyterhub/userlist cert jupyterhub/secrets/oauth.env jupyterhub/secrets/postgres.env

cert:
	@echo "Generating certificate..."
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $(SSL_KEY) -out $(SSL_CERT)

webpack:
	npm run webpack

watch:
	npm run watch

deps:
	pip install -U pip pipenv
	npm install
	pipenv install

build_home_page:
	npm run build-home

hub: build_home_page check-files network volumes
	export AUTH_CLASS='' && \
	cd ./jupyterhub && docker-compose build

run_hub:
	export AUTH_CLASS='jupyterhub.auth.DummyAuthenticator' && \
	cd ./jupyterhub && docker-compose up

run_hub_gh:
	export AUTH_CLASS=oauthenticator.GitHubOAuthenticator && \
	cd ./jupyterhub && docker-compose up

build:  webpack
	pipenv lock -r > requirements.txt
	docker build -t $(DOCKER_STOCHSS_IMAGE):latest .

run:    
	docker run --rm \
		--name $(DOCKER_STOCHSS_IMAGE) \
		--env-file .env \
		-v $(PWD):/stochss \
		-p 8888:8888 \
		$(DOCKER_STOCHSS_IMAGE):latest

build_and_run: build run

run_bash:
	docker run -it --rm \
		--name $(DOCKER_STOCHSS_IMAGE) \
		--env-file .env \
		-v $(PWD):/stochss \
		-p 8888:8888 \
		$(DOCKER_STOCHSS_IMAGE):latest \
		/bin/bash


update:
	docker exec -it $(DOCKER_STOCHSS_IMAGE) python -m pip install -e /stochss


.PHONY: network volumes check-files pull notebook_image build
