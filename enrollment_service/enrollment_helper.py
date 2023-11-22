import sqlite3
from http import HTTPStatus
from fastapi import HTTPException, status
from botocore.exceptions import ClientError
from .dynamoclient import DynamoClient
from .db_connection import get_dynamodb, get_redisdb, TableNames

def is_auto_enroll_enabled(db: sqlite3.Connection):
    """
    Check if automatic enrollment is enabled

    Parameters:
        db (sqlite3.Connection): Database connection.

    Returns:
        bool: True if automatic enrollment is enabled. Otherwise, False.
    """
    
    cursor = db.execute("SELECT automatic_enrollment FROM configs")
    result = cursor.fetchone()
    return result[0] == 1

def get_available_classes_within_first_2weeks(db: sqlite3.Connection):
    """
    Get classes which have available seats

    Parameters:
        db (sqlite3.Connection): Database connection.

    Returns:
        list[int]: A list of class_id.
    """

    cursor = db.execute(
        """
        SELECT id 
        FROM class 
        WHERE course_start_date >= datetime('now', '-14 days')
            AND room_capacity > (SELECT COUNT(student_id)
                            FROM enrollment
                            WHERE class_id = id
                            )
        """)
    rows = cursor.fetchall()
    return [row[0] for row in rows]

def enroll_students_from_waitlist(db: sqlite3.Connection, class_id_list: list[int]):
    """
    This function checks the waitlist for available spots in the classes
    and enrolls students accordingly.

    Parameters:
        db (sqlite3.Connection): Database connection.

    Returns:
        int: The number of success enrollments.
    """
    
    enrollment_count = 0

    try:
        for e in class_id_list:
            cursor = db.execute(
            """
            INSERT INTO enrollment (class_id, student_id, enrollment_date)
                SELECT class_id, student_id, datetime('now')
                FROM waitlist
                WHERE class_id=$0
                ORDER BY waitlist_date ASC
                LIMIT (
                        (SELECT room_capacity 
                        FROM class
                        WHERE id=$0) - (SELECT COUNT(student_id)
                                        FROM enrollment
                                        WHERE class_id=$0
                                        )
                    );
            """, [e])

            cursor = db.execute(
            """
            DELETE FROM waitlist
            WHERE student_id IN (
                SELECT student_id
                FROM waitlist
                ORDER BY waitlist_date
                LIMIT $0
            );
            """, [cursor.rowcount])

            enrollment_count += cursor.rowcount
        
        db.commit()
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    
    return enrollment_count


def add_to_waitlist(class_id, student_id, member_name: str, score: int):
    try:
        redisdb = get_redisdb()
        dynamodb = get_dynamodb()

        # Insert into Redis DB
        redisdb.zadd(class_id, {member_name: score})

        # Update Personnel table: add class_id to waitlist attribute
        update_kwargs = {
            "Key": {
                "cwid": student_id
            },
            "ConditionExpression": "attribute_exists(cwid)",
            "UpdateExpression": "SET waitlists = list_append(if_not_exists(waitlists, :empty_list), :new_item)",
            "ExpressionAttributeValues": {
                ":new_item": [class_id],
                ':empty_list': []
            },
            "ReturnValues": "UPDATED_NEW"
        }

        dynamodb.update_item(TableNames.PERSONNEL, update_kwargs)

    except Exception as e:
        raise Exception(f"AddToWaitlistFailed: {e}")

def drop_from_enrollment(class_id, student_id, administrative:bool, dynamodb: DynamoClient):
    try:
        TransactItems = [
            {
                # ---------------------------------------------------------------------
                # DELETE FROM enrollment table
                # ---------------------------------------------------------------------
                "Delete": {
                    "TableName": TableNames.ENROLLMENTS,
                    "Key": {
                        "class_id": class_id,
                        "student_cwid": student_id
                    },
                    "ConditionExpression": "attribute_exists(class_id) AND attribute_exists(student_cwid)"
                }
            },
            {
                # ---------------------------------------------------------------------
                # INSERT INTO droplist table
                # ---------------------------------------------------------------------
                "Put": {
                    "TableName": TableNames.DROPLIST,
                    "Item": {
                        "class_id": class_id,
                        "student_cwid": student_id,
                        "administrative": administrative
                    }
                }
            },
            {
                # ---------------------------------------------------------------------
                # UPDATE Class available status
                # ---------------------------------------------------------------------
                "Update": {
                    "TableName": TableNames.CLASSES,
                    "Key": {
                        "id": class_id
                    },
                    "UpdateExpression": "SET available = :new_value",
                    "ExpressionAttributeValues": {
                        ":new_value": "true"
                    }
                }
            }
        ]

        dynamodb.transact_write_items(TransactItems)

        # ---------------------------------------------------------------------
        # Trigger auto enrollment
        # ---------------------------------------------------------------------
        # TODO: Call the function auto_enrollment_from_waitlist()

    except ClientError as e:
        if e.response["Error"]["Code"] == "TransactionCanceledException":
            cancellation_reasons = e.response["CancellationReasons"]
            if cancellation_reasons[0]["Code"] == "ConditionalCheckFailed":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail="Transaction Canceled")
            else:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Conflict occurs")
        else:
            raise Exception(e.response)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail="INTERNAL SERVER ERROR")
    else:
        return {"detail": "Item deleted successfully"}