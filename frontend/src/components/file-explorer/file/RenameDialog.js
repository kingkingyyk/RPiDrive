import React from "react";
import PropTypes from "prop-types";

import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import EditIcon from "@mui/icons-material/Edit";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";

import { ajax } from "../../../utils/generics";

const RenameDialog = (props) => {
  const { file, onClose } = props;
  const [name, setName] = React.useState(file.name);
  const [isRenaming, setIsRenaming] = React.useState(false);
  const [renameError, setRenameError] = React.useState("");

  const handleClickRename = (event) => {
    if (file.name === name) {
      onClose(true);
      return;
    }

    setIsRenaming(true);
    setRenameError("");

    ajax
      .post(`/drive/ui-api/files/${file.id}/rename`, { name: name })
      .then((response) => {
        onClose(true);
      })
      .catch((reason) => {
        setRenameError(reason.response.data.error);
      })
      .finally(() => setIsRenaming(false));
  };

  return (
    <Dialog open={true} fullWidth maxWidth="xl">
      <DialogTitle
        color="primary"
        sx={{ display: "flex", alignItems: "center", flexWrap: "wrap" }}
      >
        <EditIcon size="small" />
        Rename file
      </DialogTitle>
      <DialogContent>
        <TextField
          sx={{ mt: 1 }}
          label="Name"
          size="small"
          value={name}
          onChange={(event) => setName(event.target.value)}
          disabled={isRenaming}
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
          {renameError}
        </Typography>
        <Button disabled={isRenaming} size="small" onClick={handleClickRename}>
          Rename
        </Button>
        <Button
          disabled={isRenaming}
          size="small"
          onClick={() => onClose(false)}
        >
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

RenameDialog.propTypes = {
  file: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default RenameDialog;
