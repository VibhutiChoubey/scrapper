# steps to do after cloning the repository
python3 -m venv env
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
