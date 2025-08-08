from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import MultipleObjectsReturned

class EmailBackEnd(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Get the first user with matching email (safe for duplicates)
            user = UserModel.objects.filter(email=username).first()
            
            # Check password if user exists
            if user and user.check_password(password):
                return user
            return None
            
        except MultipleObjectsReturned:
            # Handle case where multiple users exist (log the issue)
            import logging
            logging.warning(f"Multiple users with email: {username}")
            
            # Return the first valid user as fallback
            for user in UserModel.objects.filter(email=username):
                if user.check_password(password):
                    return user
            return None
            
        except Exception as e:
            # Log any other errors
            import logging
            logging.error(f"Authentication error: {str(e)}")
            return None