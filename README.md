# Übersicht der Befehle
```
git init
git remote add origin https://github.com/dan-chem/eidiv.git
git add .

python3 -m venv env
source env/bin/activate

python -m pip install Django
pip install --upgrade pip setuptools wheel
sudo apt-get install -y libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info fonts-dejavu fonts-liberation libpangoft2-1.0-0
pip install weasyprint

python manage.py createsuperuser
```