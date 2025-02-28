# Logistics Management System 

The LMS will facilitate order processing, shipment tracking, inventory management, and reporting for logistics companies. It will support both web and mobile platforms.


## Features 
- User [**Authentication**](#user-authentication) and role management 
- [**Order**](#order-management) processing and tracking 
- [**Inventory**](#inventory-management) management 
- [**Route**](#route-optimzation) optimizaiton 
- Reporting and **analytics**

## LMS UML & Screen Ketches 

Our [UML](UML%20&%20Sketches/lms_uml.PNG) class diagrams will help us create our *Django Models* and we've also included an **initial** [screen ketch](UML%20&%20Sketches/lms_sketch.png) that maps out our *Django Templates* 

## LMS Flowchart & User Story 

Our [Flowchart](flowchart_&_usecase/TekBasic_-_Flowchart.jpg) and [User Story](flowchart_&_usecase/tek_basic_LMS_spreadsheet.png) helps us map out the workflow of our logistic management system 

## Update Logs 
- 02/27
  - Authentication System 
  - Media & Static [Files](https://dev.to/emiloju/how-to-handle-media-uploads-in-django-1kpc) 
  - [Bootstrap5](https://www.w3schools.com/django/django_add_bootstrap5.php) Integration 
    - `pip install django-bootstrap-v5` 
  - [Side](https://dev.to/codeply/bootstrap-5-sidebar-examples-38pb) Nav & Base HTML 
  - MySQL Database 
    - `pip install mysqlclient` 
  - Envrionmental Variables
    - `pip install python-dotenv` 
    - Be sure to add a `.env` with: *DEBUG_LOCAL*, *MYSQL_LOCAL_CONNECTION*, *SECRET_LOCAL_KEY*
      - **MYSQL_LOCAL_CONNECTION** should follow: `"NAME USER PASSWORD HOST PORT"`
  - Tasks to Consider:
    - Profile Page & Uploading / Display Profile Image 
    - Login/Register Display Succes/Error Message
    - Replace Home Icons 
    - Start working on the Different Management Pages 


## User Authentication 
- [x] [Custom](https://dev.to/earthcomfy/getting-started-custom-user-model-5hc) LMS User
  - Role Field (default to "Worker") Updated by **ADMINS**
  - Depending on each role, they'll be granted certain access     
- [x] Register & Login Page (Error/Success Message)
- [ ] Sign Out (Error/Success Message)
- [ ] Updating Profile Information 


## Order Management 

## Inventory Management 

## Route Optimzation 