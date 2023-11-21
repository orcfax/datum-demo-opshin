.DEFAULT_GOAL := help

.PHONY: build-contract

get-minting-policy:                     ## Get the minting policy
	@echo "";
	@cat build/contract/script.policy_id
	@echo "";
	@echo "paste the above id into ../datum-demo-opshin/config.py replacing the current POLICY_ID";
	@echo "";

help:   ## Print this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
