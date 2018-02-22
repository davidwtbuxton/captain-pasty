import jsonschema


paste_schema = {
    '$schema': 'http://json-schema.org/schema#',
    'type': 'object',
    'properties': {
        'description': {'type': 'string'},
        'files': {
            'type': 'array',
            'minItems': 1,
            'items': {
                'type': 'object',
                'properties': {
                    'filename': {'type': 'string'},
                    'content': {'type': 'string'},
                },
                'required': ['filename', 'content'],
            },
        },
        'fork': {'type': 'string'},
    },
    'required': ['description', 'files'],
}
paste_validator = jsonschema.Draft4Validator(paste_schema)
