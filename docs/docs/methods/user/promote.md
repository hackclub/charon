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
This endpoint is used to invite a user to the Slack workspace as a multi-channel guest. If the user is already a member of the workspace, they will be added to the programs channels.

## Response
A successful response will return a JSON object with the following structure:

```json
{
  "ok": true,
  "msg": "",
}
```

### Success Messages

| Message            | Description                                      |
|--------------------|--------------------------------------------------|
| `user_invited`     | The user has been successfully invited.          |
| `already_in_time` | The user is already in Slack, Charon has added them to the channels.           |


### Errors

| Error Code          | Description                                      |
|---------------------|--------------------------------------------------|
| `invalid_email`     | The provided email address is not valid.         |
| `already_invited`   | The user has already been invited.               |
| `unknown_error`     | An unknown error occurred.                       |

Other error codes could be returned if they are given by Slack. Do not use this as a comprehensive list of errors.

