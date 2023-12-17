# Student Enrollment
A back-end Web Service to manage course enrollment and waiting lists with functionality similar to TitanOnline.

### Prerequisites
Operating system: Debian-based Linux (Ubuntu, etc.) 

## Installation steps
Follow these steps to install all the required packages:
#### Step 1: Clone the Repository

#### Step 2: Run the Installation Script
Navigate to the project directory and execute the install.sh script:
```bash
sh ./bin/install.sh
```
The script will automatically download and install all the required packages for the project.

Including: AWS CLI, DynamoDB Local, Redis, SQlite3, foreman, KrakenD

## Start the services
Navigate to the project directory and execute the run.sh script:
```bash
sh run.sh
```

## Run Unit Tests
Execute the following command to run the unit tests:
```bash
python3 -m unittest -v
```

## Microservice Diagram
<img src="https://github.com/NLTN/Assets/blob/main/StudentEnrollment/HighLevelDiagramV3.png?raw=true">

## Database Diagram

#### Enrollment Service
<img src="https://github.com/NLTN/Assets/blob/main/StudentEnrollment/EnrollmentNoSQLDiagram.png?raw=true">

#### User Service
<img src="https://github.com/NLTN/Assets/blob/main/StudentEnrollment/UserERDiagram.png?raw=true">

## API Gateway endpoints
#### User Service >>[Show Examples](../../wiki/Examples-‐-User-Endpoints)
| Method | Route            | Description                   |
|--------|------------------|-------------------------------|
|POST    | /api/register/	| Register a new user account.	|
|POST    | /api/login/		| User login.                   |

#### Enrollment Service - Endpoints for Registrars >>[Show Examples](../../wiki/Examples-‐-Registrar-Endpoints)
| Method | Route                    | Description                               |
|--------|--------------------------|-------------------------------------------|
|PUT     | /api/auto-enrollment/    | Enable or disable auto enrollment         |
|POST    | /api/courses/            | Creates a new course.                     |
|POST    | /api/classes/            | Creates a new class.                      |
|DELETE  | /api/classes/{class_id}  | Deletes a specific class.                 |
|PATCH   | /api/classes/{class_id}  | Updates specific details of a class.      |


#### Enrollment Service - Endpoints for Students >>[Show Examples](../../wiki/Examples-‐-Student-Endpoints)
| Method | Route                                | Description                                |
|--------|--------------------------------------|--------------------------------------------|
|GET     | /api/classes/available/              | Retreive all available classes.            |
|GET     | /api/waitlist/{class_id}/position/   | Get current waitlist position.             |
|POST    | /api/enrollment/                     | Student enrolls in a class.                |
|DELETE  | /api/enrollment/{class_id}           | Students drop themselves from a class.     |
|DELETE  | /api/waitlist/{class_id}             | Students remove themselves from a waitlist.|

#### Enrollment Service - Endpoints for Instructors >>[Show Examples](../../wiki/Examples-‐-Instructor-Endpoints)
| Method | Route                                | Description                               |
|--------|--------------------------------------|-------------------------------------------|
|GET     | /api/classes/{class_id}/students/    | Retreive current enrollment for the classes.  |
|GET     | /api/classes/{class_id}/droplist/    | Retreive students who have dropped the class  |
|GET     | /api/classes/{class_id}/waitlist/    | Retreive students in the waiting list        |
|DELETE  | /api/enrollment/{class_id}/{student_id}/administratively/   | Instructors drop students administratively. |

#### Notification Subscription Service
| Method | Route                                | Description                               |
|--------|--------------------------------------|-------------------------------------------|
|GET     | /api/subscriptions                   | List subscriptions. |
|POST    | /api/class/{class_id}/subscribe      | Subscribe to notifications for a new course.  |
|POST    | /api/class/{class_id}/unsubscribe    | Unsubscribe from a course. |
