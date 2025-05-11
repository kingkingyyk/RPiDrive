import React from "react";
import {
  Link as RouterLink,
  Outlet,
  useNavigate,
  useParams,
} from "react-router-dom";
import { styled } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Tooltip from "@mui/material/Tooltip";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";
import Drawer from "@mui/material/Drawer";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import MenuIcon from "@mui/icons-material/Menu";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import ListSubheader from "@mui/material/ListSubheader";
import Skeleton from "@mui/material/Skeleton";
import PlaylistAddIcon from "@mui/icons-material/PlaylistAdd";

import { ajax } from "../../utils/generics";
import EditDialog from "./EditDialog";
import IsLoggedIn from "../users/IsLoggedIn";

const drawerWidth = 250;
const DrawerHeader = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
}));

const MediaPlayer = () => {
  const { playlistId } = useParams();
  const navigate = useNavigate();
  const wideView = useMediaQuery("(min-width:600px)");
  const [openDrawer, setOpenDrawer] = React.useState(wideView);
  const [playlists, setPlaylists] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [errorLoading, setErrorLoading] = React.useState("");
  const [openCreateDialog, setOpenCreateDialog] = React.useState(false);

  const loadData = () => {
    setIsLoading(true);
    setErrorLoading("");
    ajax
      .get("/drive/ui-api/playlists/")
      .then((response) => setPlaylists(response.data.values))
      .catch((reason) => setErrorLoading(reason.response.data.error))
      .finally(() => setIsLoading(false));
  };

  React.useEffect(() => {
    document.title = "Media Player - RPi Drive";
    loadData();
  }, []);

  const handleEditDialogClose = (data) => {
    setOpenCreateDialog(false);
    if (data) {
      loadData();
      navigate(`/drive/media-player/${data.id}`);
    }
  };

  const openPlaylist = (playlist) => {
    navigate(`/drive/media-player/${playlist.id}`);
    if (!wideView) {
      setOpenDrawer(false);
    }
  };

  const onPlaylistUpdated = (playlist) => {
    const newList = [...playlists];
    for (let pl of newList) {
      if (pl.id === playlist.id) pl.name = playlist.name;
    }
    setPlaylists(newList);
  };

  const onPlaylistDeleted = (playlist) => {
    let idx = 0;
    for (let i = 0; i < playlists.length; i++) {
      if (playlists[i].id === playlist.id) {
        idx = i;
        break;
      }
    }
    const newList = playlists.filter((pl) => pl.id !== playlist.id);
    setPlaylists(newList);
    if (idx < newList.length) {
      openPlaylist(newList[idx]);
    } else if (newList.length > 0) {
      openPlaylist(newList[idx - 1]);
    } else {
      navigate("/drive/media-player");
    }
  };

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
            Media Player
          </Typography>
          <Tooltip title="Close">
            <IconButton color="inherit" component={RouterLink} to="/drive">
              <CloseIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
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
            <Box sx={{ flexGrow: 1 }}>
              <Button
                variant="contained"
                startIcon={<PlaylistAddIcon />}
                onClick={() => setOpenCreateDialog(true)}
              >
                Create New
              </Button>
            </Box>
            <IconButton onClick={() => setOpenDrawer(false)} size="small">
              <ChevronLeftIcon />
            </IconButton>
          </DrawerHeader>
          <Divider />
          <List
            dense
            subheader={<ListSubheader component="div">Playlists</ListSubheader>}
          >
            {isLoading && (
              <ListItem disablePadding>
                <Skeleton width="100%" height="60px" />
              </ListItem>
            )}
            {errorLoading && (
              <ListItem disablePadding>
                <Typography variant="subtitle2" color="error">
                  {errorLoading}
                </Typography>
              </ListItem>
            )}
            {playlists.map((playlist) => (
              <ListItem key={playlist.id} disablePadding>
                <ListItemButton
                  selected={playlist.id === playlistId}
                  onClick={() => openPlaylist(playlist)}
                >
                  <ListItemText primary={playlist.name} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Drawer>
      </AppBar>
      <Box
        component="main"
        sx={openDrawer && wideView && { ml: `${drawerWidth}px`, p: 1 }}
      >
        <Toolbar />
        <Outlet context={{ onPlaylistUpdated, onPlaylistDeleted }} />
      </Box>
      {openCreateDialog && (
        <EditDialog playlistId={-1} onClose={handleEditDialogClose} />
      )}
      <IsLoggedIn />
    </Box>
  );
};

export default MediaPlayer;
