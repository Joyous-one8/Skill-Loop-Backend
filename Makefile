.PHONY: backend run

backend:
	# put backend build/setup commands here, if any
	@echo "Backend target: nothing to do"

run:
	. .venv/bin/activate && uvicorn main:app --reload

