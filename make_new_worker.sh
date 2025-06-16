screen -S worker6
mkdir worker6
cd worker6
git clone git@github.com:tnc-ca-geo/python-flow-calculator.git
cd python-flow-calculator
git checkout parquet-processing
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mv filenames6.txt filenames.txt
python upstream_main.py