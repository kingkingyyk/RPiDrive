import React from "react";
import PropTypes from "prop-types";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import Typography from "@mui/material/Typography";

import { ajax } from "../../../utils/generics";

const EditDialog = (props) => {
  const unChangedPassword = "DON'T ChANG3 MY pAssw0rd";
  const { userId, selfId, onClose } = props;
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [passwordError, setPasswordError] = React.useState(null);
  const [confirmPw, setConfirmPw] = React.useState("");
  const [firstName, setFirstName] = React.useState("");
  const [lastName, setLastName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [emailError, setEmailError] = React.useState(null);
  const [isActive, setIsActive] = React.useState(true);
  const [isAdmin, setIsAdmin] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorLoading, setErrorLoading] = React.useState("");
  const emailRegex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i;

  const loadUser = () => {
    setIsLoading(true);
    ajax
      .get(`/drive/ui-api/users/${userId}`)
      .then((response) => {
        const data = response.data;
        setUsername(data.username);
        setPassword(unChangedPassword);
        setConfirmPw(unChangedPassword);
        setFirstName(data.first_name);
        setLastName(data.last_name);
        setEmail(data.email);
        setIsActive(data.is_active);
        setIsAdmin(data.is_superuser);
      })
      .catch(() => onClose(false))
      .finally(() => setIsLoading(false));
  };

  React.useEffect(() => {
    if (userId !== -1) {
      loadUser();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  React.useEffect(() => {
    if (!email) {
      setEmailError("Email must be filled.");
    } else if (!emailRegex.test(email)) {
      setEmailError("Invalid email.");
    } else {
      setEmailError(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [email]);

  React.useEffect(() => {
    if (!password) {
      setPasswordError("Password must be filled.");
    } else if (password.length < 8) {
      setPasswordError("Password length must be at least 8 characters.");
    } else {
      setPasswordError(null);
    }
  }, [password]);

  const handleSave = () => {
    const url =
      userId !== -1
        ? `/drive/ui-api/users/${userId}`
        : "/drive/ui-api/users/create";

    let data = {
      username: username,
      first_name: firstName,
      last_name: lastName,
      email: email,
      is_active: isActive,
      is_superuser: isAdmin,
    };
    if (password !== unChangedPassword) data["password"] = password;

    setIsLoading(true);
    setErrorLoading("");
    ajax
      .post(url, data)
      .then(() => {
        onClose(true);
      })
      .catch((reason) => setErrorLoading(reason.response.data.error))
      .finally(() => setIsLoading(false));
  };

  return (
    <Dialog open={true}>
      <DialogTitle>{userId === -1 ? "Create" : "Edit"} user</DialogTitle>
      <DialogContent>
        <Stack spacing={1} sx={{ mt: 1 }}>
          <TextField
            label="Username"
            required
            size="small"
            fullWidth
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            disabled={isLoading}
            error={!username}
            helperText={!username ? "Username must be filled." : null}
          />
          <TextField
            label="Password"
            required
            size="small"
            fullWidth
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            disabled={isLoading}
            onFocus={() => {
              if (password === unChangedPassword) {
                setPassword("");
              }
            }}
            error={passwordError}
            helperText={passwordError}
          />
          <TextField
            label="Confirm Password"
            required
            size="small"
            fullWidth
            value={confirmPw}
            onChange={(event) => setConfirmPw(event.target.value)}
            type="password"
            disabled={isLoading}
            onFocus={() => {
              if (confirmPw === unChangedPassword) {
                setConfirmPw("");
              }
            }}
            error={password !== confirmPw}
            helperText={
              password !== confirmPw
                ? "Password must be filled and matches."
                : null
            }
          />
          <TextField
            label="First Name"
            size="small"
            fullWidth
            value={firstName}
            onChange={(event) => setFirstName(event.target.value)}
            disabled={isLoading}
          />
          <TextField
            label="Last Name"
            size="small"
            fullWidth
            value={lastName}
            onChange={(event) => setLastName(event.target.value)}
            disabled={isLoading}
          />
          <TextField
            label="Email"
            required
            size="small"
            fullWidth
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            disabled={isLoading}
            error={emailError}
            helperText={emailError}
          />
          <FormControlLabel
            control={
              <Checkbox
                size="small"
                checked={isActive}
                onChange={(event) => setIsActive(event.target.value)}
                disabled={isLoading || userId === selfId}
              />
            }
            label="Active"
            size="small"
          />
          <FormControlLabel
            control={
              <Checkbox
                size="small"
                checked={isAdmin}
                onChange={(event) => setIsAdmin(event.target.value)}
                disabled={isLoading || userId === selfId}
              />
            }
            label="Admin"
            size="small"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Typography variant="caption" color="error">
          {errorLoading}
        </Typography>
        <Button
          onClick={handleSave}
          disabled={
            isLoading ||
            !username ||
            passwordError ||
            password !== confirmPw ||
            emailError
          }
        >
          Save
        </Button>
        <Button onClick={() => onClose(false)} disabled={isLoading}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

EditDialog.propTypes = {
  userId: PropTypes.number.isRequired,
  selfId: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default EditDialog;
