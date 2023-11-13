import React from "react";
import {
  Link as RouterLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { styled } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import Drawer from "@mui/material/Drawer";
import LinearProgress from "@mui/material/LinearProgress";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Skeleton from "@mui/material/Skeleton";
import Typography from "@mui/material/Typography";
import Toolbar from "@mui/material/Toolbar";
import Tooltip from "@mui/material/Tooltip";
import AppBar from "@mui/material/AppBar";
import Divider from "@mui/material/Divider";
import CloseIcon from "@mui/icons-material/Close";
import MenuIcon from "@mui/icons-material/Menu";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import StorageIcon from "@mui/icons-material/Storage";
import ListItemIcon from "@mui/material/ListItemIcon";
import AddIcon from "@mui/icons-material/Add";
import CreateNewFolderOutlinedIcon from "@mui/icons-material/CreateNewFolderOutlined";
import UploadFileOutlinedIcon from "@mui/icons-material/UploadFileOutlined";
import DriveFolderUploadOutlinedIcon from "@mui/icons-material/DriveFolderUploadOutlined";
import CompressIcon from "@mui/icons-material/Compress";
import TextField from "@mui/material/TextField";
import SearchIcon from "@mui/icons-material/Search";
import InputAdornment from "@mui/material/InputAdornment";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";

import prettyBytes from "pretty-bytes";
import { debounce } from "lodash";
import { ajax } from "../../utils/generics";
import IsLoggedIn from "../users/IsLoggedIn";
import EditVolumeDialog from "./volume/EditVolumeDialog";
import NewFolderDialog from "./file/NewFolderDialog";
import UploadDialog from "./file/UploadDialog";

const drawerWidth = 250;
const DrawerHeader = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
}));

const FileExplorerRoot = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const wideView = useMediaQuery("(min-width:600px)");
  const [openDrawer, setOpenDrawer] = React.useState(false);
  const [volumes, setVolumes] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState("");
  const [jobs, setJobs] = React.useState(null);
  const [anchorEl, setAnchorEl] = React.useState(null);
  const openNewMenu = Boolean(anchorEl);
  const [openNewVolDialog, setOpenNewVolDialog] = React.useState(false);
  const [openNewFolderDialog, setOpenNewFolderDialog] = React.useState(false);
  const volumeUrl = "/drive/my-drive";
  const [currFolder, setCurrFolder] = React.useState(null);
  const [triggerLoad, setTriggerLoad] = React.useState(false);
  const [openUploadDialog, setOpenUploadDialog] = React.useState(false);
  const [isUploadFile, setIsUploadFile] = React.useState(true);
  const [searchText, setSearchText] = React.useState("");

  const loadVolumes = () => {
    setIsLoading(true);
    setErrorMsg("");
    ajax
      .get("/drive/ui-api/volumes")
      .then((response) => {
        setVolumes(response.data.values);
      })
      .catch((reason) => setErrorMsg(reason.response.data.error))
      .finally(() => setIsLoading(false));
  };

  const loadJobs = () => {
    ajax
      .get("/drive/ui-api/jobs")
      .then((response) => {
        setJobs(response.data.values);
      })
      .catch((reason) => setErrorMsg(reason.response.data.error));
  };

  React.useEffect(() => {
    loadVolumes();
    loadJobs();
  }, [triggerLoad]);

  React.useEffect(() => {
    const interval = setInterval(() => {
      loadVolumes();
      loadJobs();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  React.useEffect(() => {
    if (location.pathname.startsWith("/drive/folder/search")) {
      const params = new URLSearchParams(location.search);
      const keyword = params.get("keyword") || "";
      setSearchText(keyword);
    } else if (location.pathname.startsWith("/drive/folder/")) {
      const paths = location.pathname.split("/");
      setCurrFolder(paths[paths.length - 1]);
    } else {
      setCurrFolder(null);
    }
  }, [location]);

  const handleClickNewButton = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleCloseNewMenu = () => {
    setAnchorEl(null);
  };

  const handleOpenNewVolDialog = () => {
    setAnchorEl(null);
    setOpenNewVolDialog(true);
  };

  const handleClickVolume = (volume) => {
    setIsLoading(true);
    ajax
      .get(`/drive/ui-api/volumes/${volume.id}`)
      .then((response) => {
        navigate(`/drive/folder/${response.data.root_file}`);
        if (!wideView) {
          setOpenDrawer(false);
        }
      })
      .finally(() => setIsLoading(false));
  };

  const renderNewMenu = () => {
    return (
      <Menu
        anchorEl={anchorEl}
        open={openNewMenu}
        onClose={handleCloseNewMenu}
        MenuListProps={{ dense: true }}
      >
        {window.location.pathname === volumeUrl
          ? [
              <MenuItem key="new-volume" onClick={handleOpenNewVolDialog}>
                <ListItemIcon>
                  <StorageIcon fontSize="small" />
                </ListItemIcon>
                <Typography variant="inherit">Volume</Typography>
              </MenuItem>,
            ]
          : [
              <MenuItem
                key="new-folder"
                onClick={() => {
                  handleCloseNewMenu(false);
                  setOpenNewFolderDialog(true);
                }}
              >
                <ListItemIcon>
                  <CreateNewFolderOutlinedIcon fontSize="small" />
                </ListItemIcon>
                <Typography variant="inherit">New folder</Typography>
              </MenuItem>,
              <Divider />,
              <MenuItem
                key="file-upload"
                onClick={() => {
                  handleCloseNewMenu(false);
                  setIsUploadFile(true);
                  setOpenUploadDialog(true);
                }}
              >
                <ListItemIcon>
                  <UploadFileOutlinedIcon fontSize="small" />
                </ListItemIcon>
                <Typography variant="inherit">File upload</Typography>
              </MenuItem>,
              <MenuItem
                key="folder-upload"
                onClick={() => {
                  handleCloseNewMenu(false);
                  setIsUploadFile(false);
                  setOpenUploadDialog(true);
                }}
              >
                <ListItemIcon>
                  <DriveFolderUploadOutlinedIcon fontSize="small" />
                </ListItemIcon>
                <Typography variant="inherit">Folder upload</Typography>
              </MenuItem>,
            ]}
      </Menu>
    );
  };

  const setSearchUrl = (value) => {
    navigate(`/drive/folder/search?keyword=${value}`);
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debounceSetSearchUrl = React.useCallback(
    debounce((value) => setSearchUrl(value), 500),
    []
  );

  const handleChangeSearchText = (event) => {
    setSearchText(event.target.value);
    debounceSetSearchUrl(event.target.value);
  };

  const handleNewVolDialogClose = (result) => {
    setOpenNewVolDialog(false);
    if (result) {
      setTriggerLoad(!triggerLoad);
    }
  };

  const handleNewFolderDialogClose = () => {
    setOpenNewFolderDialog(false);
  };

  const handleUploadDialogClose = (result) => {
    setOpenUploadDialog(false);
    if (result) {
      setTriggerLoad(!triggerLoad);
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
            File Explorer
          </Typography>
          <TextField
            label="Search"
            size="small"
            margin="dense"
            variant="filled"
            InputLabelProps={{
              style: { color: "inherit" },
            }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ mr: 1, width: wideView ? "300px" : "150px" }}
            value={searchText}
            onChange={(event) => handleChangeSearchText(event)}
          />
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
          <Box sx={{ flexGrow: 1 }}>
            <Button
              variant="contained"
              size="large"
              sx={{ m: 1 }}
              onClick={handleClickNewButton}
              startIcon={<AddIcon />}
            >
              New
            </Button>
            {renderNewMenu()}
          </Box>
          {!wideView && (
            <IconButton onClick={() => setOpenDrawer(false)} size="small">
              <ChevronLeftIcon />
            </IconButton>
          )}
        </DrawerHeader>
        <List
          sx={{ pl: 1, pr: 1 }}
          subheader={
            <ListItemButton
              disableGutters
              component={RouterLink}
              to="/drive/my-drive"
              sx={{ mb: 1, p: 1 }}
            >
              <Typography variant="subtitle2">Volumes</Typography>
            </ListItemButton>
          }
          dense
        >
          {isLoading && !volumes && (
            <Skeleton variant="rectangular" height={60} />
          )}
          <Typography variant="caption" color="error">
            {errorMsg}
          </Typography>
          {volumes &&
            volumes.map((volume) => (
              <ListItemButton
                key={volume.id}
                onClick={() => handleClickVolume(volume)}
                disableGutters
                sx={{ pl: 1, pr: 1 }}
              >
                <ListItemText
                  primary={
                    <Typography variant="subtitle2">{volume.name}</Typography>
                  }
                  secondary={
                    <React.Fragment>
                      <Typography
                        sx={{ display: "inline" }}
                        variant="body2"
                        color="text.primary"
                      >
                        {volume.path}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={
                          volume.total_space === 0
                            ? 0
                            : Math.floor(
                                (volume.used_space * 100) / volume.total_space
                              )
                        }
                      />
                      <Typography variant="caption">
                        {prettyBytes(volume.used_space)} (
                        {volume.total_space === 0
                          ? 0
                          : Math.floor(
                              (volume.used_space * 100) / volume.total_space
                            )}
                        %) used of {prettyBytes(volume.total_space)}
                      </Typography>
                    </React.Fragment>
                  }
                />
              </ListItemButton>
            ))}
        </List>
        <Divider />
        <List
          sx={{ pl: 1, pr: 1 }}
          subheader={
            <Typography variant="subtitle2" sx={{ m: 1 }}>
              Jobs
            </Typography>
          }
          dense
        >
          {jobs &&
            jobs.map((job) => (
              <ListItem key={job.id} disableGutters sx={{ pl: 1, pr: 1 }}>
                <ListItemText
                  primary={
                    <React.Fragment>
                      <ListItemIcon sx={{ minWidth: "inherit" }}>
                        <CompressIcon sx={{ fontSize: 16 }} />
                      </ListItemIcon>
                      <Typography variant="caption">
                        {job.description}
                      </Typography>
                    </React.Fragment>
                  }
                  secondary={
                    <React.Fragment>
                      {job.status === "Running" && (
                        <LinearProgress
                          variant="determinate"
                          value={job.progress}
                        />
                      )}
                      <Typography variant="caption">
                        {job.status} ({job.progress}%)
                      </Typography>
                    </React.Fragment>
                  }
                />
              </ListItem>
            ))}
        </List>
      </Drawer>
      <Box
        component="main"
        sx={openDrawer && wideView && { ml: `${drawerWidth}px`, p: 1 }}
      >
        <Toolbar />
        <Outlet context={[triggerLoad, setTriggerLoad]} />
      </Box>
      <EditVolumeDialog
        open={openNewVolDialog}
        onClose={handleNewVolDialogClose}
      />
      <NewFolderDialog
        open={openNewFolderDialog}
        folderId={currFolder}
        onClose={handleNewFolderDialogClose}
      />
      <UploadDialog
        open={openUploadDialog}
        fileOnly={isUploadFile}
        folderId={currFolder}
        onClose={handleUploadDialogClose}
      />
      <IsLoggedIn />
    </Box>
  );
};

export default FileExplorerRoot;
