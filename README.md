For creating virtual environment -> python -m venv venv 
For Acivate the Script -> venv\Scripts\activate 
Creating requirement.txt -> pip install -r requirements.txt 
Creating superuser -> python manage.py createsuperuser
Useful Commands ->
 pip install Django==4.2.15 
 pip install django-allauth==0.61.1
 pip install djangorestframework==3.15.2
 pip install google-api-python-client==2.130.0
 pip install mysqlclient==2.2.4
 pip install pillow==10.4.0
 pip install redis==5.0.3
 pip install requests==2.32.0
 pip install social-auth-app-django==5.4.1
 pip install virtualenv==20.26.3
 pip install pandas==2.2.2
 pip install openpyxl==3.1.5
 pip install numpy==2.0.1
 pip install python-dotenv==1.0.1

 Excel Sheet Commands ->
     Note -[Add Path from your actual local]
    - For Job Portal Type Choices -  python manage.py import_job_titles "C:\Users\peddarapu sai kumar\Downloads\job_title.xlsx" "C:\Users\peddarapu sai kumar\Downloads\job_type.xlsx" "C:\Users\peddarapu sai kumar\Downloads\exp_type.xlsx" "C:\Users\peddarapu sai kumar\Downloads\category_type.xlsx" "C:\Users\peddarapu sai kumar\Downloads\workplace_types.xlsx" "C:\Users\peddarapu sai kumar\Downloads\location_types.xlsx" "C:\Users\peddarapu sai kumar\Downloads\sector_type.xlsx" "C:\Users\peddarapu sai kumar\Downloads\country_type.xlsx" "C:\Users\peddarapu sai kumar\Downloads\application_status.xlsx" 
    - For Test Series Type Choices - python manage.py import_event_types --event_type "C:\Users\peddarapu sai kumar\Downloads\event_type.xlsx" --question_status "C:\Users\peddarapu sai kumar\Downloads\question_status.xlsx" --question_section_type "C:\Users\peddarapu sai kumar\Downloads\question_section_type.xlsx" --session_id 1 --exam_id 1 

Create a database by this line -> CREATE DATABASE mydatabase1(your database name) CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;

For Applying migrations use this lines -> python manage.py makemigrations and  python manage.py migrate

For programming purpose -> we are using python langauage and the version- Python (version= 3.12)

For database purpose -> we are using MySQL

For cache storing purpose -> we are using django

For framework purpose -> we are using djangorestframework




