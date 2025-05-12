import React from "react";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

const ErrorPage = () => {
  return (
    <Stack
      sx={{ p: 2, mt: "20vh", textAlign: "center", width: "100%" }}
      spacing={2}
    >
      <Typography variant="h3">😵‍💫 404 Page not found</Typography>
      <Typography>RPi Drive</Typography>
    </Stack>
  );
};

export default ErrorPage;
