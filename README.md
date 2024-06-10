# CustChurnAnalysis-Website
This is a simple website to perform Cust Churn Analysis.

## Tools and Skills Used
[![My Skills](https://skillicons.dev/icons?i=py,sqlite,html,css,flask,vscode,git)](https://skillicons.dev)  

## Contributors
1. Sample Contributor [`Email`](pechimuthumithil@iitgn.ac.in)
2. Complications that's why sample

## Website flowchart
![Website flow](https://github.com/PechimuthuMithil/CustChurnAnalysis-Website/assets/119656326/fe7049bc-e4e5-407d-9592-d9dae8c3846f)

## Database Schema
![ER-Diagram](https://github.com/PechimuthuMithil/CustChurnAnalysis-Website/assets/119656326/2d174da6-2b4d-4933-8a20-f9d4cb7f0734)  
### Basic Idea:  
We have two entities namely user and files. We will store the file on the server (file handling) rather than in the database. In the database (sqlite) we will store where the file stored on the server and it was uploaded by which user. The file metadata can be used to tell more about the file that can be used to select a few files from the existing for analysis.

## Deploy the server
Fist clone this repository and move into the cloned directory.
```bash
git clone https://github.com/PechimuthuMithil/CustChurnAnalysis-Website.git
cd CustChurnAnalysis-Website
```
### Setup Dataabse
To set up the database, run the following command
```bash
pip install -r requirements.txt
```  

### Run the Flask Application
Run the flask application however necessary. I created a venv and did the following
```bash
export FLASK_APP=app.py
flask run
```



