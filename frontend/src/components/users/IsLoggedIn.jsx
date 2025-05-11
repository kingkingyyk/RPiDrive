import React from "react";
import { useNavigate } from "react-router-dom";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import Typography from "@mui/material/Typography";

import { ajax } from "../../utils/generics";

const IsLoggedIn = () => {
  const navigate = useNavigate();
  const [showPrompt, setShowPrompt] = React.useState(false);

  const check = () => {
    if (showPrompt) return;

    ajax.get("/drive/ui-api/users/check").catch((error) => {
      if (error.response.data.flag === false) {
        setShowPrompt(true);
      }
    });
  };

  React.useEffect(() => {
    check();
    const interval = setInterval(() => check(), 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <React.Fragment>
      {showPrompt && (
        <Dialog open>
          <DialogContent>
            <Typography>You are not logged in.</Typography>
          </DialogContent>
          <DialogActions>
            <Button
              variant="contained"
              size="small"
              onClick={() => {
                navigate({
                  pathname: "/drive/login",
                  search: "?next=" + window.location.pathname,
                });
              }}
            >
              Login
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </React.Fragment>
  );
};

export default IsLoggedIn;
