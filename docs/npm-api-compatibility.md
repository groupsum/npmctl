# NPM API compatibility

npmctl reads the NPM OpenAPI schema and detects CRUD support for:

- `/nginx/proxy-hosts`
- `/nginx/certificates`
- `/nginx/access-lists`

The controller fails closed. If an endpoint is not advertised by the schema, npmctl refuses the corresponding operation instead of guessing.
