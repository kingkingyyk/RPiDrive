import React from "react";
import PropTypes from "prop-types";
import { useNavigate } from "react-router-dom";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import EditIcon from "@mui/icons-material/Edit";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";

import { ajax } from "../../../utils/generics";

const NewFolderDialog = (props) => {
  const { open, folderId, onClose } = props;
  const navigate = useNavigate();
  const [name, setName] = React.useState("New folder");
  const [isCreating, setIsCreating] = React.useState(false);
  const [createError, setCreateError] = React.useState("");

  const handleClickCreate = (event) => {
    setIsCreating(true);
    setCreateError("");

    ajax
      .post(`/drive/ui-api/files/${folderId}/new-folder`, { name: name })
      .then((response) => {
        onClose(true);
        navigate(`/drive/folder/${response.data.id}`);
      })
      .catch((reason) => {
        setCreateError(reason.response.data.error);
      })
      .finally(() => setIsCreating(false));
  };

  React.useEffect(() => setName("New folder"), [open]);

  return (
    <Dialog open={open} fullWidth maxWidth="xl">
      <DialogTitle
        color="primary"
        sx={{ display: "flex", alignItems: "center", flexWrap: "wrap" }}
      >
        <EditIcon size="small" />
        Create new folder
      </DialogTitle>
      <DialogContent>
        <TextField
          sx={{ mt: 1 }}
          label="Name"
          size="small"
          value={name}
          onChange={(event) => setName(event.target.value)}
          disabled={isCreating}
          fullWidth
          inputRef={(input) => input?.focus()}
          onFocus={(e) =>
            e.currentTarget.setSelectionRange(
              e.currentTarget.value.length,
              e.currentTarget.value.length
            )
          }
          focused
        />
      </DialogContent>
      <DialogActions>
        <Typography color="error" variant="subtitle2">
          {createError}
        </Typography>
        <Button disabled={isCreating} size="small" onClick={handleClickCreate}>
          Create
        </Button>
        <Button
          disabled={isCreating}
          size="small"
          onClick={() => onClose(false)}
        >
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

NewFolderDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  folderId: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default NewFolderDialog;
