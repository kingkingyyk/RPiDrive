import React from "react";
import PropTypes from "prop-types";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { ajax } from "../../utils/generics";

const EditDialog = (props) => {
  const { playlistId, onClose } = props;
  const [name, setName] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorLoading, setErrorLoading] = React.useState("");

  const loadData = () => {
    setIsLoading(true);
    ajax
      .get(`/drive/ui-api/playlists/${playlistId}`)
      .then((response) => setName(response.data.name))
      .catch(() => onClose(null))
      .finally(() => setIsLoading(false));
  };

  React.useEffect(() => {
    if (playlistId !== -1) loadData();
  }, [playlistId]);

  const handleSave = (event) => {
    event.preventDefault();

    const data = {
      action: "rename",
      name: name.trim(),
    };
    const url =
      playlistId === -1
        ? "/drive/ui-api/playlists/create"
        : `/drive/ui-api/playlists/${playlistId}`;

    ajax
      .post(url, data)
      .then((response) =>
        onClose({
          id: playlistId !== -1 ? playlistId : response.data.id,
          name: name.trim(),
        })
      )
      .catch((reason) => setErrorLoading(reason.response.data.error))
      .finally(() => setIsLoading(false));
  };

  return (
    <Dialog open={true} maxWidth="xl" fullWidth>
      <form onSubmit={handleSave}>
        <DialogTitle>
          {playlistId === -1 ? "Create" : "Rename"} playlist
        </DialogTitle>
        <DialogContent>
          <TextField
            sx={{ mt: 1 }}
            value={name}
            onChange={(event) => setName(event.target.value)}
            label="Name"
            error={!name || !name.trim()}
            helperText={
              !name || !name.trim() ? "Name must not be empty!" : null
            }
            disabled={isLoading}
            size="small"
          />
        </DialogContent>
        <DialogActions>
          <Typography color="error" variant="caption">
            {errorLoading}
          </Typography>
          <Button
            type="submit"
            onClick={handleSave}
            disabled={isLoading || !name || !name.trim()}
          >
            Save
          </Button>
          <Button onClick={() => onClose(null)} disabled={isLoading}>
            Cancel
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

EditDialog.propTypes = {
  playlistId: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default EditDialog;
