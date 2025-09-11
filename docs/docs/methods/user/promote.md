# `users/promote` method

## Facts

---
- **Description**: Promote a multi-channel guest to a full member
- **Method Access**: `POST https://charon.hackclub.com/users/promote`
- **Authentication**: Bearer Token in `Authorization` header
- **Content-Type**: `application/json`

---
## Arguments

### Required arguments
---
| Argument      | Type   | Description                          |
|---------------|--------|--------------------------------------|
| `id`       | String | The Slack ID of the user to promote |

### Optional arguments
---
| Argument      | Type   | Description                          |
|---------------|--------|--------------------------------------|
| `channels`  | Array | An array of channel IDs to invite the user to. This will override the channels specified in Charon's settings. |

---
## Usage info
This endpoint is used to promote a mulit-channel guest to a full member. They'll also be added to the channels specified in the `channels` argument or in Charon's settings (default).

## Response
A successful response will return a JSON object with the following structure:

```json
{
  "ok": true,
  "message": "promotion_success",
  "signup": {
    "id": "U12345678",
    "email": "charon@hackclub.com",
    "status": "invited",
    "program_id": 1
  }
}
```

An error response will return a JSON object with the following structure:

```json
{
  "ok": false,
  "message": "email_not_found"
}
```

### Success Messages

| Message            | Description                                      |
|--------------------|--------------------------------------------------|
| `promotion_success`     | The user has been successfully promoted.          |
| `already_in_time` | The user is already in Slack, Charon has added them to the channels.           |


### Error Messages

| Error Code          | Description                                      |
|---------------------|--------------------------------------------------|
| `email_not_found`   | Could not find the user's email                  |
| `adult`             | The user is an adult and cannot be promoted.     |
| `verificaiton_failed` | The user hasn't got an eligible verification.  |
| `signup_not_found`  | User not found in Charon's database.             |
| `promotion_fail`    | Something went wrong somewhere :0                |
| `unknown_error`     | An unknown error occurred.                       |
