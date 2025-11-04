# `user/invite` method

## Facts

---
- **Description**: Invite a user to the workspace
- **Method Access**: `POST https://charon.hackclub.com/user/invite`
- **Authentication**: Bearer Token in `Authorization` header
- **Content-Type**: `application/json`

---
## Arguments

### Required arguments
---
| Argument      | Type   | Description                          |
|---------------|--------|--------------------------------------|
| `email`       | String | The email address of the user to invite |
| `ip`          | String | The IP address of the user to invite  |

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
  "message": "",
}
```

### Success Messages

| Message            | Description                                      |
|--------------------|--------------------------------------------------|
| `user_invited`     | The user has been successfully invited.          |
| `already_in_time` | The user is already in Slack, Charon has added them to the channels.           |


### Error Messages

| Error Code          | Description                                      |
|---------------------|--------------------------------------------------|
| `invalid_email`     | The provided email address is not valid.         |
| `already_invited`   | The user has already been invited.               |
| `unknown_error`     | An unknown error occurred.                       |

Other error codes could be returned if they are given by Slack. Do not use this as a comprehensive list of errors.

