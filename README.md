# GregTech or Other Chinese Modpack Quest Translator

## Instructions

### 1. Install Python 3.10
- Download from: [Python 3.10.9] (https://www.python.org/downloads/release/python-3109) (I'm using this :) )
- During installation, **make sure to check "Add Python to PATH**.
### 2. Install pip (if not already installed)
1. Download the pip installer:
   ```bash
   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
2. Run the installer:
   ```bash
   python get-pip.py
3. Check if pip is installed:
   ```bash
   python -m pip --version
### 3. Install required Python libraries:
  ```bash
  pip install googletrans==4.0.0-rc1 tqdm nbtlib
  ```
### 4. Download the translator script
   1. Download `translate.py` from this repository.
   2. Place it somewhere easy to find (e.g., Desktop)
### 5. Set your modpack folder
   1. Open `translate.py` with Notepad or any text editor.
   2. Find this line near the bottom:
      ```python
      modpack_folder = r"C:\Users\Name\curseforge\minecraft\Instances\GregTech Quantum Transition"
      ```
   3. Replace the path with the location of **your** modpack instance folder.
      Example:
      ```python
      modpack_folder = r"C:\Users\YourName\curseforge\minecraft\Instances\GregTech Quantum Transition"
      ```
   4. Save and close the file.
### 6. Run the script
   1. Open Command Prompt (CMD). (Done by entering cmd into windows search.)
   2. Navigate to where you placed `translate.py` (e.g., Desktop)
      ```bash
      cd desktop
      ```
   3. Run the script:
      ```bash
      python translate.py
      ```
   4. Wait until it finishes. You will see a summary like:
      ```yaml
      Files translated: 12
      Strings translated: 346
      ```
### Requirements
- Python 3.10 (You can try using other versions just make sure it's compatible with googletrans)
- pip (latest version)
- Libraries: `googletrans==4.0.0-rc1`, `tqdm`, `nbtlib`
