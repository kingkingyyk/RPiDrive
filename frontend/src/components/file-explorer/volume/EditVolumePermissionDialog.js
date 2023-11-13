import React from "react";
import PropTypes from "prop-types";
import useMediaQuery from "@mui/material/useMediaQuery";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Box from "@mui/material/Box";
import Select from "@mui/material/Select";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import Typography from "@mui/material/Typography";
import Tooltip from "@mui/material/Tooltip";

import { MaterialReactTable } from "material-react-table";
import { ajax, formatUsername } from "../../../utils/generics";

const EditVolumePermissionDialog = (props) => {
  const wideView = useMediaQuery("(min-width:600px)");
  const [isLoading, setIsLoading] = React.useState(false);
  const [volName, setVolName] = React.useState("");
  const [volPerms, setVolPerms] = React.useState([]);
  const [users, setUsers] = React.useState([]);
  const [userMap, setUserMap] = React.useState({});
  const [userChoices, setUserChoices] = React.useState([]);
  const [permissions, setPermissions] = React.useState([]);
  const [isApplying, setIsApplying] = React.useState(false);
  const [applyError, setApplyError] = React.useState("");
  const [selectedUser, setSelectedUser] = React.useState(-1);
  const columns = React.useMemo(
    () => [
      {
        accessorKey: "user",
        header: "User",
        Cell: ({ cell }) => formatUsername(userMap[cell.getValue()]),
      },
      {
        accessorKey: "permission",
        header: "Permission",
        Cell: ({ cell }) => {
          return (
            <FormControl variant="outlined" size="small">
              <InputLabel id="set-permission-label">Permission</InputLabel>
              <Select
                labelId="set-permission-label"
                value={cell.getValue()}
                onChange={(event) => {
                  cell.row.original.permission = event.target.value;
                  setVolPerms([...volPerms]);
                }}
                label="Permission"
                MenuProps={{
                  MenuListProps: { dense: true },
                }}
              >
                {permissions.map((permission) => (
                  <MenuItem value={permission.value} key={permission.value}>
                    {permission.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          );
        },
      },
    ],
    [userMap, volPerms, permissions]
  );

  const loadUsers = () => {
    ajax
      .get("/drive/ui-api/users")
      .then((response) => {
        const rUsers = response.data.values;
        setUsers(rUsers);

        const rUserMap = {};
        for (let user of rUsers) {
          rUserMap[user.id] = user;
        }
        setUserMap(rUserMap);
      })
      .catch(() => {
        handleClose();
      });
  };

  const loadPermissions = () => {
    ajax
      .get("/drive/ui-api/volumes/permissions")
      .then((response) => {
        const rPerms = response.data.values;
        setPermissions(rPerms);
      })
      .catch(() => {
        handleClose();
      });
  };

  const loadVolume = () => {
    if (!props.id) return;

    setIsLoading(true);
    ajax
      .get(`/drive/ui-api/volumes/${props.id}`)
      .then((response) => {
        let volume = response.data;
        setVolName(volume.name);
        setVolPerms(volume.permissions);
      })
      .catch(() => {
        handleClose();
      })
      .finally(() => setIsLoading(false));
  };

  React.useEffect(() => {
    loadUsers();
    loadPermissions();
    loadVolume();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.id]);

  React.useEffect(() => {
    const usersInList = new Set(volPerms.map((x) => x.user));
    setUserChoices(users.filter((x) => !usersInList.has(x.id)));
  }, [volPerms, users]);

  const handleApply = () => {
    const postData = {
      permissions: volPerms,
    };
    setIsApplying(true);
    setApplyError("");

    ajax
      .post(`/drive/ui-api/volumes/${props.id}?fields=permissions`, postData)
      .then(() => {
        props.onClose(true);
      })
      .catch((reason) => {
        setApplyError(reason.response.data.error);
      })
      .finally(() => setIsApplying(false));
  };

  const handleSelectUser = (event) => {
    setSelectedUser(event.target.value);
  };

  const handleAddUser = () => {
    setSelectedUser(-1);
    let newData = [...volPerms];
    newData.push({
      user: selectedUser,
      permission: permissions[0].value,
    });
    setVolPerms(newData);
  };

  const handleRemoveUser = (row) => {
    let newData = volPerms.filter((x) => x.user !== row.user);
    setVolPerms(newData);
  };

  const handleClose = () => {
    props.onClose(false);
  };

  return (
    <Dialog open={props.open} fullScreen={!wideView} fullWidth>
      <DialogTitle>Set permissions for {volName}</DialogTitle>
      <DialogContent>
        <Box sx={{ m: 1, display: "flex" }}>
          <FormControl fullWidth size="small">
            <InputLabel id="user-select-label">User</InputLabel>
            <Select
              labelId="user-select-label"
              value={selectedUser}
              label="User"
              onChange={handleSelectUser}
              MenuProps={{
                MenuListProps: { dense: true },
              }}
            >
              {userChoices.map((user) => (
                <MenuItem key={user.id} value={user.id}>
                  {formatUsername(user)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Tooltip title="Add user">
            <IconButton
              color="primary"
              disabled={selectedUser === -1}
              onClick={handleAddUser}
            >
              <AddIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Divider />
        <Box sx={{ p: 1, width: "100%" }}>
          <MaterialReactTable
            columns={columns}
            data={volPerms}
            enableTopToolbar={false}
            enableBottomToolbar={false}
            enableColumnActions={false}
            enablePagination={false}
            enableRowActions
            renderRowActions={({ row }) => (
              <Box>
                <Tooltip title="Delete">
                  <IconButton
                    color="error"
                    onClick={() => handleRemoveUser(row.original)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            )}
            positionActionsColumn="last"
            enableRowVirtualization
            initialState={{
              density: "compact",
            }}
            muiTablePaperProps={{
              elevation: 0,
            }}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Typography variant="subtitle2" color="error">
          {applyError}
        </Typography>
        <Button onClick={handleApply} disabled={isApplying || isLoading}>
          Save
        </Button>
        <Button
          onClick={handleClose}
          disabled={isApplying || isLoading}
          autoFocus
        >
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

EditVolumePermissionDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  id: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default EditVolumePermissionDialog;
