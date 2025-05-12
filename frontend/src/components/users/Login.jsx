import React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import InputAdornment from "@mui/material/InputAdornment";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import IconButton from "@mui/material/IconButton";
import OutlinedInput from "@mui/material/OutlinedInput";
import InputLabel from "@mui/material/InputLabel";
import FormControl from "@mui/material/FormControl";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";

import { ajax } from "../../utils/generics";

const Login = () => {
  const navigate = useNavigate();
  const wideView = useMediaQuery("(min-width:500px)");
  // eslint-disable-next-line no-unused-vars
  const [searchParams, setSearchParams] = useSearchParams();
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState("");

  document.title = "RPi Drive - Login";

  React.useEffect(() => {
    ajax.get("/drive/ui-api/users/check")
    .then((response) => {
      if (response.data.flag) {
        const nextUrl = searchParams.get("next");
        navigate(nextUrl ? nextUrl : "/drive");
      }
    })
    .catch(() => {});
  }, []);

  const handleUsernameChange = (event) => {
    setUsername(event.target.value);
  };

  const handlePasswordChange = (event) => {
    setPassword(event.target.value);
  };

  const handleClickShowPassword = () => setShowPassword((show) => !show);

  const handleMouseDownPassword = (event) => {
    event.preventDefault();
  };

  const login = (event) => {
    event.preventDefault();
    const loginData = {
      username: username,
      password: password,
    };

    setIsLoading(true);
    setErrorMsg("");
    ajax
      .post("/drive/ui-api/users/login", loginData)
      .then(() => {
        const nextUrl = searchParams.get("next");
        navigate(nextUrl ? nextUrl : "/drive");
      })
      .catch((reason) => {
        if (reason?.response?.data?.error) {
          setErrorMsg(reason.response.data.error);
        } else {
          setErrorMsg(reason.response.statusText);
        }
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  return (
    <React.Fragment>
      <Box className="background" />
      <form autoComplete="off" onSubmit={login}>
        <Box
          noValidate
          sx={wideView ? {
            width: "70%",
            maxWidth: "500px",
            position: "fixed",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
          }: {
            top: "calc(50% - 100px)",
            width: "100%",
            position: "fixed",
            zIndex: 2,
          }}
        >
          <Paper sx={{ p: 2, backgroundColor: "rgba(150,150,150,0.7)" }}>
            <Stack spacing={2}>
              <Typography color="primary" variant="h6">
                RPi Drive
              </Typography>
              <FormControl size="small">
                <InputLabel htmlFor="username">Username</InputLabel>
                <OutlinedInput
                  id="username"
                  type="text"
                  label="username"
                  value={username}
                  onChange={handleUsernameChange}
                  error={username.length === 0}
                  autoFocus
                />
              </FormControl>
              <FormControl size="small">
                <InputLabel htmlFor="password">Password</InputLabel>
                <OutlinedInput
                  id="password"
                  type={showPassword ? "text" : "password"}
                  endAdornment={
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={handleClickShowPassword}
                        onMouseDown={handleMouseDownPassword}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  }
                  label="password"
                  value={password}
                  onChange={handlePasswordChange}
                  error={password.length === 0}
                />
              </FormControl>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "end",
                  alignItems: "center",
                }}
              >
                <Typography variant="subtitle2" color="error">
                  {errorMsg}
                </Typography>
                <Button
                  variant="contained"
                  size="small"
                  type="submit"
                  disabled={isLoading || !username || !password}
                >
                  Login
                </Button>
              </Box>
            </Stack>
          </Paper>
        </Box>
      </form>
    </React.Fragment>
  );
};

export default Login;
