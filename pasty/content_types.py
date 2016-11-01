import mimetypes

# This module is used by PastyAppConfig.ready().


EXTRA_TYPES = {
    '.yaml': 'application/x-yaml',
    '.json': 'application/json',    # App Engine: text/plain
    '.js': 'application/javascript',    # App Engine: application/x-javascript
}


def add_content_types():
    """Load extra content types for classifying pastes."""
    for ext in EXTRA_TYPES:
        mimetypes.add_type(EXTRA_TYPES[ext], ext)
