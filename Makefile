.PHONY: backend run

backend:
	# put backend build/setup commands here, if any
	@echo "Backend target: nothing to do"

run:
	uvicorn main:app --reload
