REPONAME=infosec-dcu/dcumiddleware
BUILDROOT=$(HOME)/dockerbuild/$(REPONAME)
DOCKERREPO=artifactory.secureserver.net:10014/docker-dcu-local/dcumiddleware

# libraries we need to stage for pip to install inside Docker build
PRIVATE_PIPS=git@github.secureserver.net:ITSecurity/dcdatabase.git \
git@github.secureserver.net:ITSecurity/blindAl.git

.PHONY: prep dev stage prod clean

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

prod: prep
	@echo "----- building $(REPONAME) prod -----"
	DOCKERTAG=prod
	docker build -t $(DOCKERREPO):prod $(BUILDROOT)

stage: prep
	@echo "----- building $(REPONAME) stage -----"
	DOCKERTAG=stage
	docker build -t $(DOCKERREPO):stage $(BUILDROOT)

dev: prep
	@echo "----- building $(REPONAME) dev -----"
	DOCKERTAG=dev
	docker build -t $(DOCKERREPO):dev $(BUILDROOT)

ote: prep
	@echo "----- building $(REPONAME) ote -----"
	DOCKERTAG=ote
	docker build -t $(DOCKERREPO):ote $(BUILDROOT)

dev-k8s: prep
	@echo "----- building $(REPONAME) dev-k8s -----"
	docker build -t $(DOCKERREPO):dev-k8s $(BUILDROOT)

ote-k8s: prep
	@echo "----- building $(REPONAME) ote-k8s -----"
	docker build -t $(DOCKERREPO):ote-k8s $(BUILDROOT)

prod-k8s: prep
	@echo "----- building $(REPONAME) prod-k8s -----"
	docker build -t $(DOCKERREPO):prod-k8s $(BUILDROOT)


clean:
	@echo "----- cleaning $(REPONAME) app -----"
	rm -rf $(BUILDROOT)
