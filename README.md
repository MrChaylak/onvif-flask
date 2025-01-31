# Flask Onvif Camera Control API

With this **Flask** API you can discover and control the Onvif Cameras in your network. To test it with a UI check out my **[Vue](https://github.com/MrChaylak/vue-screen-app.git)** app also.

## Table of Contents

- [Used Technologies](#used-technologies)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Running the Application](#-running-the-application)

---

## Used Technologies

- 🟣 [Vuetify](https://vuetifyjs.com/) for styling.
- 🟢 [Vue](https://vuejs.org/) for frontend framework.
- 🔴 [Flask](https://flask.palletsprojects.com/) for backend API to control onvif cameras

## 📌 Prerequisites

Before setting up the project, ensure you have the following tools installed on your machine:

- [Python (version 3.8 or higher)](https://www.python.org/downloads/)
- pip (Python package manager) installed by default with Python
- [Git](https://git-scm.com/)


To verify the installation, run the following commands:

```bash
python --version
pip --version
git --version
```

Ensure you see version numbers for each.

**My Versions**:

- Python 3.12.4
- pip 23.2.1
- Git 2.46.0.windows.1

## 💿 Installation

To set up the project, follow these steps:

- **Clone the Repository**: 

```bash
git clone https://github.com/MrChaylak/onvif-flask.git
cd onvif-flask
```

- **Setup Virtual Environment (recommended for Python projects)**:

```bash
python -m venv .venv
# Activate the virtual environment:
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

- **Install Dependencies**: 

```bash
pip install -r requirements.txt
```

This command installs all required dependencies listed in requirements.txt.

Note: if needed you can ensure your dependencies are always up-to-date by running:

```bash
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

## 💡 Running the Application

Activate the virtual environment (if not already activated).
To run the application use the following command:

```bash
python run.py
```

This will run the Flask app and it will be served on [http://127.0.0.1:5000](http://127.0.0.1:5000). You should see the message "Flask is running!".

Note: This command starts only the Flask app, you can use my **Vue** frontend display repository to display and control the onvif cameras. You can find the link to the repository here:
- [Vue](https://github.com/MrChaylak/vue-screen-app.git) - The frontend framework used to display the discovered onvif cameras on network and control PTZ movement. Navigate to '/onvif-camera'.
