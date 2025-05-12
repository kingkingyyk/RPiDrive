import React from "react";
import { useOutletContext, useParams } from "react-router-dom";
import useMediaQuery from "@mui/material/useMediaQuery";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Drawer from "@mui/material/Drawer";
import FormControl from "@mui/material/FormControl";
import IconButton from "@mui/material/IconButton";
import InputLabel from "@mui/material/InputLabel";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Select from "@mui/material/Select";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import DeleteIcon from "@mui/icons-material/Delete";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import FolderIcon from "@mui/icons-material/Folder";
import AudiotrackIcon from "@mui/icons-material/Audiotrack";
import CloseIcon from "@mui/icons-material/Close";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import Snackbar from "@mui/material/Snackbar";
import MuiAlert from "@mui/material/Alert";
import Tooltip from "@mui/material/Tooltip";
import { purple, green } from "@mui/material/colors";

import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";
import { ajax } from "../../utils/generics";
import EditDialog from "./EditDialog";
import DeleteDialog from "../../utils/DeleteDialog";

const Alert = React.forwardRef(function Alert(props, ref) {
  return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

const reorderFile = (list, startIdx, endIdx) => {
  const result = Array.from(list);
  const [removed] = result.splice(startIdx, 1);
  result.splice(endIdx, 0, removed);
  return result;
};

const getListItemStyle = (isDragging, draggableStyle) => ({
  ...draggableStyle,

  ...(isDragging && {
    background: "rgb(235,235,235)",
  }),
});

const Playlist = () => {
  const { playlistId } = useParams();
  const { onPlaylistUpdated, onPlaylistDeleted } = useOutletContext();
  const wideView = useMediaQuery("(min-width:600px)");
  const [playlist, setPlaylist] = React.useState(null);
  const [errorLoading, setErrorLoading] = React.useState("");
  const [anchorEl, setAnchorEl] = React.useState(null);
  const [openEditDialog, setOpenEditDialog] = React.useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [deleteError, setDeleteError] = React.useState("");
  const [openExplorer, setOpenExplorer] = React.useState(false);
  const [volumes, setVolumes] = React.useState([]);
  const [selectedVolume, setSelectedVolume] = React.useState({});
  const [isLoadingVol, setIsLoadingVol] = React.useState(false);
  const [currFolder, setCurrFolder] = React.useState(null);
  const [snackbar, setSnackbar] = React.useState({ open: false });
  const [playingFile, setPlayingFile] = React.useState(null);
  const playerRef = React.useRef();
  const [playerState, setPlayerState] = React.useState(true);

  const loadData = () => {
    ajax
      .get(`/drive/ui-api/playlists/${playlistId}`)
      .then((response) => {
        let rPlaylist = response.data;
        document.title = `${rPlaylist.name} - Media Player - RPi Drive`;
        for (let file of rPlaylist.files) {
          if (!file.metadata) {
            file.metadata = {};
          }
        }
        setPlaylist(rPlaylist);
        if (rPlaylist.files.length > 0) {
          setPlayingFile(rPlaylist.files[0]);
        }
      })
      .catch((reason) => {
        console.log(reason);
        setErrorLoading(reason.response.data.error)
      });
  };

  const loadVolumes = () => {
    setIsLoadingVol(true);
    ajax
      .get(`/drive/ui-api/volumes/`)
      .then((response) => {
        const vol = response.data.values;
        setVolumes(vol);
        if (vol.length > 0) setSelectedVolume(vol[0]);
      })
      .catch(() => setOpenExplorer(false))
      .finally(() => setIsLoadingVol(false));
  };

  React.useEffect(() => {
    setPlayingFile(null);
    loadData();
  }, [playlistId]);

  const handleClickMore = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleCloseMore = () => {
    setAnchorEl(null);
  };

  const handleDelete = () => {
    setIsDeleting(true);
    setDeleteError("");
    ajax
      .delete(`/drive/ui-api/playlists/${playlistId}`)
      .then(() => {
        setOpenDeleteDialog(false);
        onPlaylistDeleted(playlist);
      })
      .catch((reason) => setDeleteError(reason.response.value.error))
      .finally(() => setOpenDeleteDialog(false));
  };

  const handleDeleteCancel = () => {
    setOpenDeleteDialog(false);
  };

  const handleCloseDialog = (data) => {
    setOpenEditDialog(false);
    if (data) {
      loadData();
      onPlaylistUpdated(data);
    }
  };

  const handleSelectFolder = (folderId) => {
    setCurrFolder(null);
    ajax
      .get(`/drive/ui-api/files/${folderId}`, {
        params: { fields: "volume,path,children" },
      })
      .then((response) => {
        response.data.children = response.data.children.filter(
          (x) =>
            x.kind === "folder" ||
            (x.media_type && x.media_type.startsWith("audio/"))
        );
        for (let path of response.data.path) path.kind = "folder";
        response.data.path.push({ name: response.data.name, kind: "folder" });
        setCurrFolder(response.data);
      })
      .catch(() => setOpenExplorer(false));
  };

  React.useEffect(() => {
    if (selectedVolume && selectedVolume.id) {
      ajax
        .get(`/drive/ui-api/volumes/${selectedVolume.id}`)
        .then((response) => {
          handleSelectFolder(response.data.root_file);
        })
        .catch(() => setOpenExplorer(false));
    }
  }, [selectedVolume]);

  const handleSelectFile = (file) => {
    if (file.kind === "folder") {
      handleSelectFolder(file.id);
    } else {
      const data = {
        action: "add-file",
        file_id: file.id,
      };
      ajax
        .post(`/drive/ui-api/playlists/${playlistId}`, data)
        .then(() => {
          loadData();
          setSnackbar({
            open: true,
            severity: "success",
            message: "File added successfully.",
          });
        })
        .catch((reason) => {
          setSnackbar({
            open: true,
            severity: "error",
            message: reason.response.data.error,
          });
        });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ open: false });
  };

  const renderAddFile = () => {
    return (
      <Drawer
        anchor="right"
        open={openExplorer}
        onClose={() => setOpenExplorer(false)}
      >
        <Stack sx={{ p: 2, width: "500px" }} spacing={2}>
          <Stack direction="row">
            <Typography variant="h6" color="primary" sx={{ flexGrow: 1 }}>
              Add media file
            </Typography>
            <IconButton size="small" onClick={() => setOpenExplorer(false)}>
              <CloseIcon fontSize="small" />
            </IconButton>
          </Stack>

          <FormControl fullWidth size="small" sx={{ mt: 2 }}>
            <InputLabel id="volume-label">Volume</InputLabel>
            <Select
              labelId="volume-label"
              value={selectedVolume}
              label="Volume"
              onChange={(event) => setSelectedVolume(event.target.value)}
              MenuProps={{
                slotProps: {
                  list: {
                    dense: true
                  }
                }
              }}
              disabled={isLoadingVol}
            >
              {volumes.map((volume) => (
                <MenuItem key={volume.id} value={volume}>
                  {volume.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <IconButton
              size="small"
              onClick={() =>
                handleSelectFile(currFolder.path[currFolder.path.length - 2])
              }
              disabled={!currFolder || currFolder.path.length < 2}
            >
              <KeyboardArrowUpIcon fontSize="small" />
            </IconButton>
            {currFolder ? (
              <Typography variant="subtitle2">
                {selectedVolume.path}
                {currFolder.path.map((x) => x.name).join("/")}
              </Typography>
            ) : (
              <Skeleton width="50px" height="20px" />
            )}
          </Stack>
          {currFolder && (
            <List dense disablePadding>
              {currFolder.children.map((child) => (
                <ListItem key={child.id} disableGutters disablePadding>
                  <ListItemButton onClick={() => handleSelectFile(child)}>
                    <ListItemIcon>
                      {child.kind === "folder" ? (
                        <FolderIcon fontSize="small" />
                      ) : (
                        <AudiotrackIcon
                          fontSize="small"
                          style={{ color: purple[500] }}
                        />
                      )}
                    </ListItemIcon>
                    <ListItemText primary={child.name} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </Stack>
      </Drawer>
    );
  };

  const handlePlayFile = (file) => {
    if (file === playingFile) {
      if (playerState) {
        setPlayerState(false);
        playerRef.current.pause();
      } else {
        setPlayerState(true);
        playerRef.current.play();
      }
    } else {
      setPlayingFile(file);
      setPlayerState(true);
      playerRef.current.play();
    }
  };

  navigator.mediaSession.setActionHandler("play", () => {
    setPlayerState(true);
    playerRef.current.play();
  });

  navigator.mediaSession.setActionHandler("pause", () => {
    setPlayerState(false);
    playerRef.current.pause();
  });

  navigator.mediaSession.setActionHandler("previoustrack", () => {
    playNext(-1);
  });

  navigator.mediaSession.setActionHandler("nexttrack", () => {
    playNext(1);
  });

  const playNext = (delta) => {
    if (playlist.files.length === 0) {
      setPlayingFile(null);
      return;
    }

    let idx = playlist.files.indexOf(playingFile);
    idx = (idx + delta + playlist.files.length) % playlist.files.length;
    setPlayingFile(playlist.files[idx]);
  };

  React.useEffect(() => {
    if (!playingFile) {
      if (playlist) {
        document.title = `${playlist.name} - Media Player - RPi Drive`;
      } else {
        document.title = "Media Player - RPi Drive";
      }
      if ("mediaSession" in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({});
      }
    } else {
      let mMetadata = playingFile.metadata || {};
      if (!mMetadata.title) {
        mMetadata.title = playingFile.name;
      }
      document.title = `${mMetadata.title} - RPi Drive`;
      if ("mediaSession" in navigator) {
        mMetadata["artwork"] = [
          { src: `/drive/ui-api/files/${playingFile.source_id}/thumbnail` },
        ];
        navigator.mediaSession.metadata = new MediaMetadata(mMetadata);
      }
    }
  }, [playingFile]);

  const handleRemoveFile = (file) => {
    const data = {
      action: "remove-file",
      file_id: file.id,
    };

    ajax
      .post(`/drive/ui-api/playlists/${playlistId}`, data)
      .then(() => {
        let nPlaylist = { ...playlist };
        nPlaylist.files = nPlaylist.files.filter((x) => x.id !== file.id);
        setPlaylist(nPlaylist);

        if (playingFile && file.id === playingFile.id) {
          playNext(1);
        }
        setSnackbar({
          open: true,
          severity: "success",
          message: "File removed from playlist successfully.",
        });
      })
      .catch((reason) =>
        setSnackbar({
          open: true,
          severity: "error",
          message: reason.response.data.error,
        })
      );
  };

  const onDragEnd = (result) => {
    if (!result.destination) {
      return;
    }
    if (result.destination.index === result.source.index) {
      return;
    }
    const oPlaylist = { ...playlist };
    const nPlaylist = { ...playlist };
    nPlaylist.files = reorderFile(
      playlist.files,
      result.source.index,
      result.destination.index
    );
    setPlaylist(nPlaylist);

    const data = {
      action: "reorder",
      files: nPlaylist.files.map((x) => x.id),
    };
    ajax
      .post(`/drive/ui-api/playlists/${playlistId}`, data)
      .then(() => {})
      .catch((reason) => {
        console.error(reason);
        setPlaylist(oPlaylist);
      });
  };

  const renderPlaylist = () => {
    return (
      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId="droppable" direction="vertical">
          {(droppableProvided) => (
            <List
              dense
              disablePadding
              disableGutters
              ref={droppableProvided.innerRef}
              {...droppableProvided.droppableProps}
              sx={{
                overflow: "auto",
                maxHeight: wideView
                  ? "calc(100vh - 200px)"
                  : "calc(100vh - 240px)",
              }}
            >
              {playlist.files.map((file, index) => (
                <Draggable
                  key={file.id}
                  draggableId={`x-${file.id}`}
                  index={index}
                >
                  {(draggableProvided, snapshot) => (
                    <ListItem
                      ref={draggableProvided.innerRef}
                      {...draggableProvided.draggableProps}
                      {...draggableProvided.dragHandleProps}
                      style={getListItemStyle(
                        snapshot.isDragging,
                        draggableProvided.draggableProps.style
                      )}
                      disablePadding
                      secondaryAction={
                        <Tooltip title="Remove from playlist">
                          <IconButton
                            edge="end"
                            onClick={() => handleRemoveFile(file)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      }
                    >
                      <ListItemButton
                        onClick={() => handlePlayFile(file)}
                        selected={playingFile && file.id === playingFile.id}
                      >
                        <ListItemIcon>
                          {(!playingFile || file.id !== playingFile.id) && (
                            <AudiotrackIcon style={{ color: purple[500] }} />
                          )}
                          {playingFile &&
                            file.id === playingFile.id &&
                            (playerState ? (
                              <PauseIcon color="action" />
                            ) : (
                              <PlayArrowIcon style={{ color: green[500] }} />
                            ))}
                        </ListItemIcon>
                        <ListItemText
                          primary={file.metadata.title || file.name}
                          secondary={`${file.metadata.artist || ""} - ${
                            file.metadata.album || ""
                          }`}
                          slotProps={{
                            primary: {
                              sx: {
                                whiteSpace: "nowrap",
                                textOverflow: "ellipsis",
                                overflow: "hidden",
                              },
                            },
                            secondary: {
                              sx: {
                                whiteSpace: "nowrap",
                                textOverflow: "ellipsis",
                                overflow: "hidden",
                              },
                            }
                          }}
                        />
                      </ListItemButton>
                    </ListItem>
                  )}
                </Draggable>
              ))}
              {droppableProvided.placeholder}
            </List>
          )}
        </Droppable>
      </DragDropContext>
    );
  };
  return (
    <Box sx={{ p: 2 }}>
      {errorLoading && (
        <Typography color="red" variant="body2">
          {errorLoading}
        </Typography>
      )}
      {!playlist ? (
        <Skeleton width="200" height="50" />
      ) : (
        <React.Fragment>
          <Stack direction="row" spacing={2}>
            <Typography variant="h5" color="primary">
              {playlist.name}
            </Typography>
            <IconButton size="small" onClick={handleClickMore}>
              <KeyboardArrowDownIcon />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={anchorEl !== null}
              onClose={handleCloseMore}
              slotProps={{
                list: {
                  dense: true
                }
              }}
            >
              <MenuItem
                onClick={(event) => {
                  handleCloseMore(event);
                  loadVolumes();
                  setOpenExplorer(true);
                }}
              >
                <ListItemIcon>
                  <AddIcon fontSize="small" />
                </ListItemIcon>
                Add
              </MenuItem>
              <MenuItem
                onClick={() => {
                  handleCloseMore();
                  setOpenEditDialog(true);
                }}
              >
                <ListItemIcon>
                  <EditIcon fontSize="small" />
                </ListItemIcon>
                Rename
              </MenuItem>
              <MenuItem
                onClick={() => {
                  handleCloseMore();
                  setOpenDeleteDialog(true);
                }}
              >
                <ListItemIcon>
                  <DeleteForeverIcon fontSize="small" color="error" />
                </ListItemIcon>
                Delete
              </MenuItem>
            </Menu>
            {openEditDialog && (
              <EditDialog playlistId={playlistId} onClose={handleCloseDialog} />
            )}
            {openDeleteDialog && (
              <DeleteDialog
                title={`Delete playlist ${playlist.name}?`}
                message=""
                validateText=""
                onApply={handleDelete}
                onCancel={handleDeleteCancel}
                loading={isDeleting}
                errorMsg={deleteError}
              />
            )}
          </Stack>
          <Divider sx={{ mt: 1 }} />
          {renderAddFile()}
          {playlist && renderPlaylist()}
          <Drawer
            open={true}
            variant="persistent"
            anchor="bottom"
            slotProps={{
              paper: {
                elevation: 3,
              }
            }}
          >
            {playingFile ? (
              <Stack direction={wideView ? "row" : "column"} spacing={0}>
                <Stack direction="row" spacing={1}>
                  <img
                    src={`/drive/ui-api/files/${playingFile.source_id}/thumbnail`}
                    style={{ height: "60px", width: "auto" }}
                    onLoad={(event) => (event.target.style.display = "unset")}
                    onError={(event) => (event.target.style.display = "none")}
                    loading="lazy"
                    alt="Album art"
                  />
                  <Box
                    sx={{
                      width: wideView ? "250px" : "100%",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    <Typography variant="subtitle1" noWrap>
                      {playingFile.metadata.title || playingFile.name}
                    </Typography>
                    <Typography variant="subtitle1" noWrap>
                      {playingFile.metadata.artist || "Unknown artist"} {" - "}
                      {playingFile.metadata.album || "Unknown album"}
                    </Typography>
                  </Box>
                </Stack>
                <audio
                  key={playingFile.id}
                  controls
                  /* eslint-disable-next-line react/no-unknown-property */
                  autoplay=""
                  style={{ flexGrow: 1, height: "60px", width: "100%" }}
                  loop={playlist && playlist.files.length === 1}
                  onEnded={() => playNext(1)}
                  ref={playerRef}
                >
                  <source
                    src={`/drive/download/${playingFile.source_id}`}
                    type={playingFile.media_type}
                  />
                </audio>
              </Stack>
            ) : (
              <Typography>Select a file to play.</Typography>
            )}
          </Drawer>
        </React.Fragment>
      )}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Playlist;
