import React from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import Divider from "@mui/material/Divider";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import HourglassEmptyIcon from "@mui/icons-material/HourglassEmpty";
import SyncIcon from "@mui/icons-material/Sync";
import TrackChangesIcon from "@mui/icons-material/TrackChanges";
import GroupIcon from "@mui/icons-material/Group";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";

import { MaterialReactTable } from "material-react-table";
import prettyBytes from "pretty-bytes";
import { ajax } from "../../../utils/generics";
import EditVolumeDialog from "./EditVolumeDialog";
import DeleteDialog from "../../../utils/DeleteDialog";
import EditVolumePermissionDialog from "./EditVolumePermissionDialog";
import Snackbar from "@mui/material/Snackbar";
import MuiAlert from "@mui/material/Alert";

const Alert = React.forwardRef(function Alert(props, ref) {
  return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

const Volume = () => {
  const navigate = useNavigate();
  const [volumes, setVolumes] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState("");
  const columns = React.useMemo(
    () => [
      {
        accessorKey: "name",
        header: "Name",
      },
      {
        accessorKey: "path",
        header: "Path",
      },
      {
        accessorKey: "used_space",
        header: "Used Space",
        Cell: ({ cell }) => {
          return prettyBytes(cell.getValue());
        },
        minSize: 150,
        maxSize: 150,
      },
      {
        accessorKey: "total_space",
        header: "Total Space",
        Cell: ({ cell }) => {
          return prettyBytes(cell.getValue());
        },
        minSize: 150,
        maxSize: 150,
      },
      {
        accessorKey: "indexing",
        header: "Indexing",
        Cell: ({ cell }) =>
          cell.getValue() ? (
            <Tooltip title="Running">
              <SyncIcon size="small" color="primary" />
            </Tooltip>
          ) : (
            <Tooltip title="Idle">
              <HourglassEmptyIcon size="small" color="primary" />
            </Tooltip>
          ),
        minSize: 120,
        maxSize: 120,
      },
    ],
    []
  );
  const [openEditVolDialog, setOpenEditVolDialog] = React.useState(false);
  const [openEditVolPermDialog, setOpenEditVolPermDialog] =
    React.useState(false);
  const [volumeIdToEdit, setVolumeIdToEdit] = React.useState(null);
  const [openDeleteVolDialog, setOpenDeleteVolDialog] = React.useState(false);
  const [volumeToDelete, setVolumeToDelete] = React.useState(null);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [deleteError, setDeleteError] = React.useState("");
  const [triggerLoad, setTriggerLoad] = useOutletContext();
  const [openSnackbar, setOpenSnackbar] = React.useState(false);
  const [contextMenu, setContextMenu] = React.useState(null);

  const loadData = () => {
    setIsLoading(true);
    setErrorMsg("");
    ajax
      .get("/drive/ui-api/volumes/")
      .then((response) => {
        setVolumes(response.data.values);
      })
      .catch((reason) => setErrorMsg(reason.response.data.error))
      .finally(() => setIsLoading(false));
  };

  React.useEffect(() => {
    document.title = "Volumes - RPi Drive";
    loadData();
  }, [triggerLoad]);

  const handleClickRow = (row) => {
    setIsLoading(true);
    ajax
      .get(`/drive/ui-api/volumes/${row.id}`)
      .then((response) => {
        navigate(`/drive/folder/${response.data.root_file}`);
      })
      .finally(() => setIsLoading(false));
  };

  const handlePerformIndex = (row) => {
    ajax.post(`/drive/ui-api/volumes/${row.id}/index`).then(() => {
      setTriggerLoad(!triggerLoad);
      setOpenSnackbar(true);
    });
  };

  const handleManage = (row) => {
    setVolumeIdToEdit(row.id);
    setOpenEditVolDialog(true);
  };

  const handleEditVolDialogClose = (result) => {
    setOpenEditVolDialog(false);
    if (result) {
      setTriggerLoad(!triggerLoad);
      setOpenSnackbar(true);
    }
  };

  const handleSetPermissions = (row) => {
    setVolumeIdToEdit(row.id);
    setOpenEditVolPermDialog(true);
  };

  const handleEditVolPermDialogClose = (result) => {
    setOpenEditVolPermDialog(false);
    if (result) {
      setOpenSnackbar(true);
    }
  };

  const handleOpenDeleteVolDialog = (row) => {
    setOpenDeleteVolDialog(true);
    setVolumeToDelete(row);
  };

  const handleDeleteVolume = () => {
    setIsDeleting(true);
    ajax
      .delete(`/drive/ui-api/volumes/${volumeToDelete.id}`)
      .then(() => {
        handleDeleteVolDialogClose(true);
        setVolumeToDelete(null);
        setTriggerLoad(!triggerLoad);
        setOpenSnackbar(true);
      })
      .catch((reason) => {
        setDeleteError(reason.response.data.error);
      })
      .finally(() => setIsDeleting(false));
  };

  const handleDeleteVolDialogClose = () => {
    setOpenDeleteVolDialog(false);
  };

  const renderContextMenu = () => {
    return (
      <Menu
        open={contextMenu !== null}
        onClose={handleContextMenuClose}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
        slotProps={{
          list: { dense: true}
        }}
      >
        {contextMenu && <MenuItem disabled>{contextMenu.volume.name}</MenuItem>}
        <Divider />
        <MenuItem
          onClick={() => {
            handleContextMenuClose();
            handlePerformIndex(contextMenu.volume);
          }}
        >
          <ListItemIcon>
            <TrackChangesIcon />
          </ListItemIcon>
          <ListItemText>Perform index</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            handleContextMenuClose();
            handleManage(contextMenu.volume);
          }}
        >
          <ListItemIcon>
            <EditIcon />
          </ListItemIcon>
          <ListItemText>Manage</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            handleContextMenuClose();
            handleSetPermissions(contextMenu.volume);
          }}
        >
          <ListItemIcon>
            <GroupIcon />
          </ListItemIcon>
          <ListItemText>Set permissions</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            handleContextMenuClose();
            handleOpenDeleteVolDialog(contextMenu.volume);
          }}
        >
          <ListItemIcon>
            <DeleteIcon color="error" />
          </ListItemIcon>
          <ListItemText color="error">Delete</ListItemText>
        </MenuItem>
      </Menu>
    );
  };

  const handleContextMenuOpen = (event, volume) => {
    event.preventDefault();

    setContextMenu(
      contextMenu === null
        ? {
            mouseX: event.clientX + 2,
            mouseY: event.clientY - 6,
            volume: volume,
          }
        : null
    );
  };

  const handleContextMenuClose = () => {
    setContextMenu(null);
  };

  return (
    <Stack
      sx={{
        p: 2,
      }}
      spacing={2}
    >
      <Typography variant="h5" color="primary">
        Volumes
      </Typography>
      <MaterialReactTable
        columns={columns}
        data={volumes}
        enablePagination={false}
        enableDensityToggle={false}
        enableGlobalFilter={false}
        enableHiding={false}
        enableFullScreenToggle={false}
        enableTopToolbar={false}
        enableColumnFilters={false}
        enableColumnResizing
        positionActionsColumn="last"
        initialState={{
          density: "compact",
        }}
        getRowId={(row) => row.id}
        muiTableBodyCellProps={({ cell }) => ({
          onClick: () => handleClickRow(cell.row.original),
          onContextMenu: (event) =>
            handleContextMenuOpen(event, cell.row.original),
          style: { cursor: "pointer" },
        })}
        muiTablePaperProps={{
          elevation: 0,
        }}
        muiTableContainerProps={{ sx: { maxHeight: "calc(100vh - 240px)" } }}
        enableRowVirtualization
        rowVirtualizerProps={{ overscan: 5 }}
        state={{ isLoading: isLoading, showAlertBanner: errorMsg }}
        muiToolbarAlertBannerProps={
          errorMsg
            ? {
                color: "error",
                children: errorMsg || "Error loading data",
              }
            : undefined
        }
        layoutMode="grid"
      />
      {renderContextMenu()}
      {openEditVolDialog && (
        <EditVolumeDialog
          id={volumeIdToEdit}
          open={openEditVolDialog}
          onClose={handleEditVolDialogClose}
        />
      )}
      {openEditVolPermDialog && (
        <EditVolumePermissionDialog
          id={volumeIdToEdit}
          open={openEditVolPermDialog}
          onClose={handleEditVolPermDialogClose}
        />
      )}
      {openDeleteVolDialog && volumeToDelete && (
        <DeleteDialog
          title="Delete volume"
          message={
            <React.Fragment>
              <Typography variant="inherit">
                Confirm to delete volume <b>{volumeToDelete.name}</b>?
              </Typography>
              <br />
              <Typography variant="inherit">
                Index data will be removed, but physical files will be kept in
                tact.
              </Typography>
            </React.Fragment>
          }
          validateText={volumeToDelete.name}
          loading={isDeleting}
          errorMsg={deleteError}
          onApply={handleDeleteVolume}
          onCancel={handleDeleteVolDialogClose}
        />
      )}
      <Snackbar
        open={openSnackbar}
        autoHideDuration={6000}
        onClose={() => setOpenSnackbar(false)}
      >
        <Alert onClose={() => setOpenSnackbar(false)} severity="success">
          Operation was successful.
        </Alert>
      </Snackbar>
    </Stack>
  );
};

export default Volume;
