REPONAME=digital-crimes/dcumiddleware
BUILDROOT=$(HOME)/dockerbuild/$(REPONAME)
DOCKERREPO=docker-dcu-local.artifactory.secureserver.net/dcumiddleware
DATE=$(shell date)
COMMIT=
BUILD_BRANCH=origin/main

define deploy_k3s
	docker build -t $(DOCKERREPO):$(2) .
	docker push $(DOCKERREPO):$(2)
	cd k8s/$(1) && kustomize edit set image $$(docker inspect --format='{{index .RepoDigests 0}}' $(DOCKERREPO):$(2))
	kubectl --context $(1)-cset apply -k k8s/$(1)
	cd k8s/$(1) && kustomize edit set image $(DOCKERREPO):$(1)
endef

.PHONY: init
init:
	@command -v tartufo >/dev/null || pipx install tartufo
	@command -v pre-commit >/dev/null || pipx install pre-commit
	@pre-commit install --install-hooks
	@poetry install

.PHONY: lint
lint:
	@poetry run isort dcumiddleware/
	@poetry run flake8 dcumiddleware/

.PHONY: unit-test
unit-test:
	@echo "----- Running tests -----"
	@poetry run python -m unittest discover tests "*_tests.py"

.PHONY: testcov
testcov:
	@echo "----- Running tests with coverage -----"
	@poetry run coverage run --source=dcumiddleware -m unittest discover tests "*_tests.py"
	@poetry run coverage xml
	@poetry run coverage report

dist/requirements.txt: poetry.lock pyproject.toml
	@mkdir -p dist/
	@poetry export -f requirements.txt --output dist/requirements.txt --with-credentials

prep: dist/requirements.txt lint unit-test
	@mkdir -p dist/
	@rm dist/*.whl 2> /dev/null || :
	@poetry build -f wheel

image: prep
	@docker build -t $(DOCKERREPO):local .

.PHONY: dev-deploy
dev-deploy: prep
	@echo "----- deploying $(REPONAME) to dev -----"
	$(call deploy_k3s,dev,dev)

.PHONY: ote-deploy
ote-deploy: prep
	@echo "----- deploying $(REPONAME) to ote -----"
	$(call deploy_k3s,ote,ote)

.PHONY: test-deploy
test-deploy: prep
	@echo "----- deploying $(REPONAME) to test -----"
	$(call deploy_k3s,test,test)

.PHONY: prod-deploy
prod-deploy: prep
	@echo "----- building $(REPONAME) prod -----"
	read -p "About to deploy a production image. Are you sure? (Y/N): " response ; \
	if [[ $$response == 'N' || $$response == 'n' ]] ; then exit 1 ; fi
	if [[ `git status --porcelain | wc -l` -gt 0 ]] ; then echo "You must stash your changes before proceeding" ; exit 1 ; fi
	$(eval COMMIT:=$(shell git rev-parse --short HEAD))
	$(call deploy_k3s,prod,$(COMMIT))

.PHONY: clean
clean:
	@rm -rf dist/
