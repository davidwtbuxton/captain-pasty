import mimetypes

# This module is used by PastyAppConfig.ready().


EXTRA_TYPES = {
    '.yaml': 'application/x-yaml',
}


def add_content_types():
    """Load extra content types for classifying pastes."""
    for ext in EXTRA_TYPES:
        mimetypes.add_type(EXTRA_TYPES[ext], ext)
