REPONAME=infosec-dcu/dcumiddleware
BUILDROOT=$(HOME)/dockerbuild/$(REPONAME)
DOCKERREPO=docker-dcu-local.artifactory.secureserver.net/dcumiddleware
DATE=$(shell date)

# libraries we need to stage for pip to install inside Docker build
PRIVATE_PIPS=git@github.secureserver.net:ITSecurity/dcdatabase.git

.PHONY: prep dev stage prod ote clean prod-deploy ote-deploy dev-deploy

all: prep dev

prep:
	@echo "----- preparing $(REPONAME) build -----"
	# stage pips we will need to install in Docker build
	mkdir -p $(BUILDROOT)/private_pips && rm -rf $(BUILDROOT)/private_pips/*
	for entry in $(PRIVATE_PIPS) ; do \
		cd $(BUILDROOT)/private_pips && git clone $$entry ; \
	done

	# copy the app code to the build root
	cp -rp ./* $(BUILDROOT)

stage: prep
	@echo "----- building $(REPONAME) stage -----"
	DOCKERTAG=stage
	docker build -t $(DOCKERREPO):stage $(BUILDROOT)

dev: prep
	@echo "----- building $(REPONAME) dev -----"
	sed -ie 's/THIS_STRING_IS_REPLACED_DURING_BUILD/$(DATE)/g' $(BUILDROOT)/k8s/dev/middleware.deployment.yml
	docker build -t $(DOCKERREPO):dev $(BUILDROOT)

ote: prep
	@echo "----- building $(REPONAME) ote -----"
	sed -ie 's/THIS_STRING_IS_REPLACED_DURING_BUILD/$(DATE)/g' $(BUILDROOT)/k8s/ote/middleware.deployment.yml
	docker build -t $(DOCKERREPO):ote $(BUILDROOT)

prod: prep
	@echo "----- building $(REPONAME) prod -----"
	sed -ie 's/THIS_STRING_IS_REPLACED_DURING_BUILD/$(DATE)/g' $(BUILDROOT)/k8s/prod/middleware.deployment.yml
	docker build -t $(DOCKERREPO):prod $(BUILDROOT)

dev-deploy: dev
	@echo "----- deploying $(REPONAME) to dev -----"
	docker push $(DOCKERREPO):dev
	kubectl --context dev apply -f $(BUILDROOT)/k8s/dev/middleware.deployment.yml --record

ote-deploy: ote
	@echo "----- deploying $(REPONAME) to ote -----"
	docker push $(DOCKERREPO):ote
	kubectl --context ote apply -f $(BUILDROOT)/k8s/ote/middleware.deployment.yml --record

prod-deploy: prod
	@echo "----- deploying $(REPONAME) to prod -----"
	docker push $(DOCKERREPO):prod
	kubectl --context prod apply -f $(BUILDROOT)/k8s/prod/middleware.deployment.yml --record

clean:
	@echo "----- cleaning $(REPONAME) app -----"
	rm -rf $(BUILDROOT)
