import React from "react";
import PropTypes from "prop-types";
import useMediaQuery from "@mui/material/useMediaQuery";

import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import { ajax } from "../../../utils/generics";

const DeleteDialog = (props) => {
  const { files, onClose } = props;
  const wideView = useMediaQuery("(min-width:600px)");
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [deleteError, setDeleteError] = React.useState("");

  const handleClickDelete = () => {
    setIsDeleting(true);
    setDeleteError("");

    const fileIds = files.map((file) => file.id);
    ajax
      .post(`/drive/ui-api/files/delete`, { files: fileIds })
      .then((response) => {
        onClose(true);
      })
      .catch((reason) => {
        setDeleteError(reason.response.data.error);
      })
      .finally(() => setIsDeleting(false));
  };

  return (
    <Dialog open={true} fullScreen={!wideView}>
      <DialogTitle
        color="error"
        sx={{ display: "flex", alignItems: "center", flexWrap: "wrap" }}
      >
        <DeleteForeverIcon size="small" />
        Delete files
      </DialogTitle>
      <DialogContent>
        <Typography variant="subtitle1" color="inherit">
          Confirm to delete the following files?
        </Typography>
        <List dense>
          {files.map((file) => (
            <ListItem key={file.id}>
              <ListItemText primary={file.name} />
            </ListItem>
          ))}
        </List>
      </DialogContent>
      <DialogActions>
        <Typography color="error" variant="subtitle2">
          {deleteError}
        </Typography>
        <Button disabled={isDeleting} onClick={handleClickDelete}>
          Delete
        </Button>
        <Button disabled={isDeleting} onClick={() => onClose(false)}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

DeleteDialog.propTypes = {
  files: PropTypes.arrayOf(PropTypes.object).isRequired,
  onClose: PropTypes.func.isRequired,
};

export default DeleteDialog;
