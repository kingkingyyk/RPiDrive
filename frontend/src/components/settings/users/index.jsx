import React from "react";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import DoneIcon from "@mui/icons-material/Done";
import CloseIcon from "@mui/icons-material/Close";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import EditIcon from "@mui/icons-material/Edit";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import AddIcon from "@mui/icons-material/Add";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";

import { MaterialReactTable } from "material-react-table";
import Timestamp from "react-timestamp";
import { ajax } from "../../../utils/generics";
import EditDialog from "./EditDialog";
import DeleteDialog from "../../../utils/DeleteDialog";
import { UserContext } from "../../../utils/contexts";

const Users = () => {
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorLoading, setErrorLoading] = React.useState("");
  const [users, setUsers] = React.useState([]);
  const columns = React.useMemo(
    () => [
      {
        accessorKey: "id",
        header: "ID",
        enableColumnActions: false,
        size: 50,
        maxSize: 50,
      },
      {
        accessorKey: "username",
        header: "Username",
      },
      {
        accessorKey: "is_active",
        header: "Active",
        Cell: ({ cell }) =>
          cell.getValue() ? (
            <DoneIcon color="success" />
          ) : (
            <CloseIcon color="error" />
          ),
        enableColumnActions: false,
        size: 70,
        maxSize: 70,
      },
      {
        accessorKey: "is_superuser",
        header: "Admin",
        Cell: ({ cell }) =>
          cell.getValue() ? (
            <DoneIcon color="success" size="small" />
          ) : (
            <CloseIcon color="error" size="small" />
          ),
        enableColumnActions: false,
        size: 70,
        maxSize: 70,
      },
      {
        accessorKey: "last_login",
        header: "Last login",
        Cell: ({ cell }) => (
          <Tooltip title={<Timestamp date={cell.getValue()} />}>
            <span>
              <Timestamp relative date={cell.getValue()} autoUpdate />
            </span>
          </Tooltip>
        ),
        enableColumnFilter: false,
        size: 100,
        maxSize: 100,
      },
    ],
    []
  );
  const userContext = React.useContext(UserContext);
  const [selfId, setSelfId] = React.useState(-1);
  const [openEditDialog, setOpenEditDialog] = React.useState(false);
  const [userIdToEdit, setUserIdToEdit] = React.useState(-1);
  const [openDeleteDialog, setOpenDeleteDialog] = React.useState(false);
  const [userIdToDelete, setUserIdToDelete] = React.useState(-1);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [deleteError, setDeleteError] = React.useState("");
  const [contextMenu, setContextMenu] = React.useState(null);

  const loadData = () => {
    setIsLoading(true);
    ajax
      .get("/drive/ui-api/users/")
      .then((response) => {
        setUsers(response.data.values);
      })
      .catch((reason) => setErrorLoading(reason.response.data.error))
      .finally(() => setIsLoading(false));
  };

  React.useEffect(() => {
    document.title = "Users - RPi Drive";
    if (userContext) {
      setSelfId(userContext.id);
    }
    loadData();
  }, [userContext]);

  const handleContextMenuOpen = (event, user) => {
    event.preventDefault();
    setContextMenu(
      contextMenu === null
        ? {
            mouseX: event.clientX + 2,
            mouseY: event.clientY - 6,
            userId: user.id,
          }
        : null
    );
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
          list: {
            dense: true
          }
        }}
      >
        <MenuItem
          disabled={!contextMenu}
          onClick={() => {
            handleContextMenuClose();
            setUserIdToEdit(contextMenu.userId);
            setOpenEditDialog(true);
          }}
        >
          <ListItemIcon>
            <EditIcon />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem
          disabled={!contextMenu}
          onClick={() => {
            handleContextMenuClose();
            setUserIdToDelete(contextMenu.userId);
            setOpenDeleteDialog(true);
          }}
        >
          <ListItemIcon>
            <DeleteForeverIcon color="error" />
          </ListItemIcon>
          <ListItemText color="error">Delete</ListItemText>
        </MenuItem>
      </Menu>
    );
  };

  const handleContextMenuClose = () => {
    setContextMenu(null);
  };

  const handleEditDialogClose = (flag) => {
    setOpenEditDialog(false);
    if (flag) {
      loadData();
    }
  };

  const handleDelete = () => {
    setIsDeleting(true);
    ajax
      .delete(`/drive/ui-api/users/${userIdToDelete}`)
      .then(() => {
        setOpenDeleteDialog(false);
        setUserIdToDelete(-1);
        loadData();
      })
      .catch((reason) => setDeleteError(reason.response.data.error))
      .finally(() => setIsDeleting(false));
  };

  const handleDeleteCancel = () => {
    setOpenDeleteDialog(false);
    setUserIdToDelete(-1);
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" color="primary">
        Users
      </Typography>
      <Divider sx={{ mt: 1 }} />
      <MaterialReactTable
        data={users}
        columns={columns}
        initialState={{
          density: "compact",
        }}
        enableRowActions
        enablePagination={false}
        enableDensityToggle={false}
        enableHiding={false}
        enableFullScreenToggle={false}
        enableRowVirtualization
        positionActionsColumn="last"
        getRowId={(row) => row.id}
        muiTablePaperProps={{
          elevation: 0,
        }}
        muiTableContainerProps={{ sx: { maxHeight: "calc(100vh - 240px)" } }}
        muiToolbarAlertBannerProps={
          errorLoading
            ? {
                color: "error",
                children: errorLoading || "Error loading data",
              }
            : {
                color: "info",
                children: `${users.length} item(s)`,
              }
        }
        muiTableBodyCellProps={({ cell }) => ({
          onContextMenu: (event) =>
            handleContextMenuOpen(event, cell.row.original),
        })}
        state={{
          isLoading: isLoading,
          showAlertBanner: true,
        }}
        positionToolbarAlertBanner="bottom"
        displayColumnDefOptions={{
          "mrt-row-actions": { size: 80, maxSize: 80 },
        }}
        layoutMode="grid"
        renderTopToolbarCustomActions={() => (
          <Button
            size="small"
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setUserIdToEdit(-1);
              setOpenEditDialog(true);
            }}
          >
            Create
          </Button>
        )}
        renderRowActions={({ row }) => (
          <Box>
            <Tooltip
              title="Edit"
              onClick={() => {
                setOpenEditDialog(true);
                setUserIdToEdit(row.id);
              }}
            >
              <IconButton>
                <EditIcon />
              </IconButton>
            </Tooltip>
            {row.id !== selfId && (
              <Tooltip
                title="Delete"
                onClick={() => {
                  setOpenDeleteDialog(true);
                  setUserIdToDelete(row.id);
                }}
              >
                <IconButton color="error">
                  <DeleteForeverIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        )}
        enableColumnResizing
      />
      {renderContextMenu()}
      {openEditDialog && (
        <EditDialog
          userId={userIdToEdit}
          selfId={selfId}
          onClose={handleEditDialogClose}
        />
      )}
      {openDeleteDialog && (
        <DeleteDialog
          title={`Confirm to delete user #${userIdToDelete}?`}
          validateText=""
          onApply={handleDelete}
          onCancel={handleDeleteCancel}
          loading={isDeleting}
          errorMsg={deleteError}
        />
      )}
    </Box>
  );
};

export default Users;
