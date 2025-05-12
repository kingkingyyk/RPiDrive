import React from "react";
import { Link as RouterLink } from "react-router-dom";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Tooltip from "@mui/material/Tooltip";
import Select from "@mui/material/Select";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";

const Profile = () => {
  const [theme, setTheme] = React.useState(
    localStorage.getItem("theme") || "system"
  );

  const handleChangeTheme = (event) => {
    setTheme(event.target.value);
    localStorage.setItem("theme", event.target.value);
    window.location.reload();
  };

  return (
    <Box sx={{ flexGow: 1 }}>
      <AppBar position="fixed" enableColorOnDark>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Profile
          </Typography>
          <Tooltip title="Close">
            <IconButton color="inherit" component={RouterLink} to="/drive">
              <CloseIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <Box component="main" sx={{ p: 2 }}>
        <Toolbar />
        <Typography variant="h5" color="primary">
          Options
        </Typography>
        <FormControl sx={{ width: "250px", mt: 3 }} size="small">
          <InputLabel id="theme-label">Theme</InputLabel>
          <Select
            labelId="theme-label"
            value={theme}
            label="Theme"
            onChange={handleChangeTheme}
            MenuProps={{
              slotProps: {
                list: {
                  dense: true
                }
              }
            }}
          >
            <MenuItem value="system">System</MenuItem>
            <MenuItem value="light">Light</MenuItem>
            <MenuItem value="dark">Dark</MenuItem>
          </Select>
        </FormControl>
      </Box>
    </Box>
  );
};

export default Profile;
