# Clips Backend
REST API service for Clips website.

### Details
The design of this API is inspired by [HATEOAS](https://en.wikipedia.org/wiki/HATEOAS). Though not abiding 100%, the goal is for each endpoint to return limited data along with links to related media to promote client-server decoupling. This contrasts to having object representations returned with related keys, requiring the client to have to manually build the URI using those keys to make future requests.

#### Current Endpoints (will add a full OpenAPI doc soon)
| Endpoints                                      | Authentication Required  | Methods                         | Write Body Fields                                 | Status       |
| ---------------------------------------------- | -------------------------| --------------------------------| --------------------------------------------------| -------------|
| api/auth/                                      | No                       | POST                            | {'username': str, 'password': str}                | Complete     |
| api/users/                                     | Yes                      | GET, POST                       | {'username': str, 'password': str, 'email': str}  | Complete     |
| api/users/<user_id>/                           | Yes                      | GET, PUT, PATCH, DELETE         | {'username': str, 'password': str, 'email': str}  | Complete     |
| api/users/<user_id>/friends/                   | Yes                      | GET, POST                       | {'to': User}                                      | Complete     |
| api/users/<user_id>/friends/incoming-requests/ | Yes                      | GET                             | N/A                                               | Complete     |
| api/users/<user_id>/friends/outgoing-requests/ | Yes                      | GET                             | N/A                                               | Complete     |
| api/users/<user_id>/private-groups/            | Yes                      | GET, POST                       | {'group_name': str, 'members': list[User]}        | Complete (*) |
| api/users/<user_id>/videos/                    | Yes                      | GET, POST                       | {'video_name': str, 'video': file}                | Complete     |
| api/videos/<video_id>/                         | Yes                      | GET, PATCH, DELETE              | {'video_name': str}                               | Complete     |
| api/private-groups/<group_id>/                 | Yes                      | GET, PUT, PATCH, DELETE         | {'group_name': str, 'members': list[User]}        | Complete     |
| api/friendships/<friendship_id>/               | Yes                      | GET, PATCH, DELETE              | N/A                                               | Complete     |
| api/feed/                                      | Yes                      | GET                             | N/A                                               | Incomplete   |

\* = Revisit due to status code 403/404 discrepancy when the resource doesn't exist, but the user also doesn't have access. Need a consistent solution.
