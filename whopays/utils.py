from .models import validate_single_emoji

import string
import random

def generate_group_code(length):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))
