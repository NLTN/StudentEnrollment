# Student Enrollment
A back-end Web Service to manage course enrollment and waiting lists with functionality similar to TitanOnline.

### Prerequisites
Operating system: Debian-based Linux (Ubuntu, etc.) 

### Installation
Run `sh ./bin/install.sh`.

### How to run
- Run `sh run.sh` to start the services.

## Microservice Diagram
<img src="https://raw.githubusercontent.com/NLTN/Assets/main/StudentEnrollment/APIGateway.svg" height="230">

## Database ER Diagram
#### User Service
<img src="https://github.com/NLTN/Assets/blob/main/StudentEnrollment/UserERDiagram.png?raw=true">

#### Enrollment Service
<img src="https://github.com/NLTN/Assets/blob/main/StudentEnrollment/EnrollmentERDiagram.png?raw=true">

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
