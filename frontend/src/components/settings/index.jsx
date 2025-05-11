import React from "react";
import { styled } from "@mui/material/styles";
import {
  Link as RouterLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";
import useMediaQuery from "@mui/material/useMediaQuery";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Drawer from "@mui/material/Drawer";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Tooltip from "@mui/material/Tooltip";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";
import GroupIcon from "@mui/icons-material/Group";
import PodcastsIcon from "@mui/icons-material/Podcasts";
import DnsIcon from "@mui/icons-material/Dns";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import MenuIcon from "@mui/icons-material/Menu";

import { ajax } from "../../utils/generics";
import IsLoggedIn from "../users/IsLoggedIn";

const drawerWidth = 160;
const usersUrl = "/drive/settings/users";
const networkUrl = "/drive/settings/network";
const systemUrl = "/drive/settings/system";
const DrawerHeader = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
  justifyContent: "flex-end",
}));

const Settings = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const wideView = useMediaQuery("(min-width:600px)");
  const [self, setSelf] = React.useState(null);
  const links = React.useMemo(
    () => [
      {
        name: "Users",
        url: usersUrl,
        icon: <GroupIcon />,
        selected: location.pathname === usersUrl,
      },
      {
        name: "Network",
        url: networkUrl,
        icon: <PodcastsIcon />,
        selected: location.pathname === networkUrl,
      },
      {
        name: "System",
        url: systemUrl,
        icon: <DnsIcon />,
        selected: location.pathname === systemUrl,
      },
    ],
    [location]
  );
  const [openDrawer, setOpenDrawer] = React.useState(true);

  React.useEffect(() => {
    document.title = "RPi Drive";
    ajax
      .get("/drive/ui-api/users/self")
      .then((response) => {
        setSelf(response.data);
      })
      .catch(() => {});
  }, []);

  return (
    <Box sx={{ flexGow: 1 }}>
      <AppBar
        position="fixed"
        sx={
          openDrawer && {
            width: wideView ? `calc(100% - ${drawerWidth}px)` : "100%",
            ml: wideView ? "0px" : `${drawerWidth}px`,
          }
        }
        enableColorOnDark
      >
        <Toolbar>
          <IconButton
            color="inherit"
            onClick={() => setOpenDrawer(true)}
            edge="start"
            sx={{ mr: 2, ...(openDrawer && { display: "none" }) }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Settings
          </Typography>
          <Tooltip title="Close">
            <IconButton color="inherit" component={RouterLink} to="/drive">
              <CloseIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
          },
        }}
        variant={wideView ? "persistent" : "temporary"}
        anchor="left"
        open={openDrawer}
        onClose={() => setOpenDrawer(false)}
      >
        <DrawerHeader>
          <IconButton onClick={() => setOpenDrawer(false)} size="small">
            <ChevronLeftIcon />
          </IconButton>
        </DrawerHeader>
        <Divider />
        {self && self.is_superuser && (
          <List dense>
            {links.map((link) => (
              <ListItem key={link.name} disablePadding>
                <ListItemButton
                  onClick={() => {
                    navigate(link.url);
                    if (!wideView) {
                      setOpenDrawer(false);
                    }
                  }}
                  selected={link.selected}
                >
                  <ListItemIcon>{link.icon}</ListItemIcon>
                  <ListItemText primary={link.name} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Drawer>
      <Box
        component="main"
        sx={openDrawer && wideView && { ml: `${drawerWidth}px`, p: 1 }}
      >
        <Toolbar />
        {self &&
          (self.is_superuser ? (
            <Outlet />
          ) : (
            <Box sx={{ width: "100%", textAlign: "center", mt: 10 }}>
              <Typography color="red" variant="h6">
                You don&apos;t have permission to view this page.
              </Typography>
            </Box>
          ))}
      </Box>
      <IsLoggedIn />
    </Box>
  );
};

export default Settings;
