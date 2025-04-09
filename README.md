# EVA - Elemental Visual Analysis
EVA is a data analysis and visualisation tool to be used with MuX at ISIS. Documentation can be found [here](https://isismuon.github.io/EVA/index.html).

### Installing on Windows 64-bit systems
Download the zip file under the "releases" panel on GitHub. Extract to a destination of choice, and start by running `main/EVA.exe` Note: Do not move the executable out of the `main` folder. If you would like quick access you can set up a shortcut instead.

### Installing on other systems
To run EVA on other systems you will have to build it from source. Download the source code and unzip to a destination of your choice. Make sure you have C++ build tools installed. It is highly recommended you setup a python virtual environment (see [venv](https://docs.python.org/3/library/venv.html)) before running EVA.

Once in your virtual environment, install all requirements:
```
pip install -r "requirements.txt"
```

After this, you can start the program by running `src/EVA/main.py`. If this fails to run, you may need to run

```
pip install -e .
```
