import re
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.views import Response
from rest_framework import status
import jwt
import os

class CustomPasswordValidator:
    def validate(self, password):
        # Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(pattern, password):
            raise serializers.ValidationError({
                'detail':'Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character'
            })

    def get_help_text(self):
        return 'Your password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character.'
    
def validate_email(email):
    response = {"status": True, "detail": ""}

    email_pattern = "^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"

    if re.match(email_pattern, email) is None:
        response["detail"] = "Email is not valid"
        response["status"] = False
        return response
    
    return response

def validate_string(*args):
    response = {"status": True, "detail": ""}
    numbers_pattern = "(?=.*?[0-9])"
    specialletters_pattern ='(?=.*?[#@$%^&*])'
    for arg in args:
        if not arg.strip():
            response["status"] = False
            response["detail"] = f'{arg} is required'
            return response
        if re.match(numbers_pattern, arg):
            response["status"] = False
            response["detail"] = f'{arg} should not contain numbers'
            return response
        if re.match(specialletters_pattern, arg):
            response["status"] = False
            response["detail"] = f'{arg} should not contain special characters'
            return response
    return response


def validate_input(email, full_name):
    validation_errors = []
    
    if not validate_email(email)["status"]:
        validation_errors.append(validate_email(email)["detail"])
        
    if not validate_string(full_name)["status"]:
        validation_errors.append(validate_string(full_name)["detail"])
    
    if validation_errors:
        error_message = ", ".join(validation_errors)
        response = {"detail": error_message}
        print(response)
        return response
    else:
        return None
    


