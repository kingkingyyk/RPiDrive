import React from "react";
import PropTypes from "prop-types";
import useMediaQuery from "@mui/material/useMediaQuery";

import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import CompressIcon from "@mui/icons-material/Compress";
import TextField from "@mui/material/TextField";
import MiniExplorer from "../mini-explorer";
import Typography from "@mui/material/Typography";

import { ajax } from "../../../utils/generics";

const CompressDialog = (props) => {
  const { volumeId, initialName, files, onClose } = props;
  const wideView = useMediaQuery("(min-width:600px)");
  const [folderId, setFolderId] = React.useState(null);
  const [name, setName] = React.useState(initialName);
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorText, setErrorText] = React.useState("");

  const handleCompress = () => {
    const data = {
      files: files,
      compress_dir: folderId,
      compress_name: name,
    };

    setIsLoading(true);
    setErrorText("");
    ajax
      .post(`/drive/ui-api/files/compress`, data)
      .then(() => {
        onClose(true);
      })
      .catch((reason) => setErrorText(reason.response.data.error))
      .finally(() => setIsLoading(false));
  };

  return (
    <Dialog open fullScreen={!wideView} fullWidth>
      <DialogTitle
        color="primary"
        sx={{ display: "flex", alignItems: "center", flexWrap: "wrap" }}
      >
        <CompressIcon size="small" />
        Compress files
      </DialogTitle>
      <DialogContent>
        <MiniExplorer
          volumeId={volumeId}
          blockedFolders={[]}
          onSelect={(folderId) => setFolderId(folderId)}
          onError={onClose}
        />
        <TextField
          value={name}
          onChange={(event) => setName(event.target.value)}
          fullWidth
          size="small"
          error={!name}
          sx={{ mt: 1 }}
          label="Archive name"
        />
      </DialogContent>
      <DialogActions>
        <Typography variant="subtitle2" color="error">
          {errorText}
        </Typography>
        <Button
          size="small"
          disabled={!name || !folderId || isLoading}
          onClick={handleCompress}
        >
          Compress
        </Button>
        <Button
          size="small"
          disabled={isLoading}
          onClick={() => onClose(false)}
        >
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

CompressDialog.propTypes = {
  volumeId: PropTypes.string.isRequired,
  initialName: PropTypes.string.isRequired,
  files: PropTypes.arrayOf(PropTypes.string).isRequired,
  onClose: PropTypes.func.isRequired,
};

export default CompressDialog;
