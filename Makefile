.DEFAULT_GOAL := help

.PHONY: build-contract

build-contract:                         ## Build the Oracle smart contract.
	opshin build spending contract.py
	@cat build/contract/testnet.addr
	@echo "";

lint-contract:                          ## Lint the smart contract
	opshin lint spending contract.py

deploy-contract:                        ## Deploy the Oracle smart contract.
	python 01.deploy.py

undeploy-contract: undeploy-contract    ## Un-deploy the Oracle smart contract.
	python 04.undeploy.py

help:   ## Print this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
