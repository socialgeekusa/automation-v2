# Automation V2

This project provides a PyQt5 based interface for managing automation tasks across connected mobile devices. It relies on Appium for device control and stores configuration in JSON files inside the `Config/` directory.

## Setup

1. Create and activate a Python virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Launching the GUI

Run the main application using Python:

```bash
python main.py
```

The GUI allows you to manage devices, accounts and start automation workflows. Configuration files will be created automatically in the `Config/` folder on first launch.

## Running Tests

Basic tests for the `ConfigManager` class are provided using `pytest`. Running
`pip install -r requirements.txt` installs all dependencies, including
`pytest` and `PyQt5`. If you only need the GUI test dependencies you can
manually install PyQt5 with:

```bash
pip install PyQt5
```

GUI tests expect an X11 backend. In headless environments use the offscreen
platform by setting `QT_QPA_PLATFORM=offscreen`.

To execute the tests:

```bash
pytest
```
