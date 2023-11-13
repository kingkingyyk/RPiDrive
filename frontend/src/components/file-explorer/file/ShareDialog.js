import React from "react";
import PropTypes from "prop-types";

import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import ShareIcon from "@mui/icons-material/Share";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import Snackbar from "@mui/material/Snackbar";
import MuiAlert from "@mui/material/Alert";

import { ajax } from "../../../utils/generics";

const Alert = React.forwardRef(function Alert(props, ref) {
  return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

const ShareDialog = (props) => {
  const { fileId, onClose } = props;
  const permalink = `${window.location.origin}/drive/download/${fileId}`;
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [publicLink, setPublicLink] = React.useState(null);
  const [openSnackbar, setOpenSnackbar] = React.useState(false);

  const getPublicLink = () => {
    setIsGenerating(true);
    ajax
      .post(`/drive/ui-api/files/${fileId}/share`)
      .then((response) => {
        setPublicLink(
          `${window.location.origin}/drive/quick-access?key=${response.data.id}`
        );
      })
      .finally(() => setIsGenerating(false));
  };

  const handleSnackbarClose = () => {
    setOpenSnackbar(false);
  };

  const handleCopyPermalink = () => {
    navigator.clipboard.writeText(permalink);
    setOpenSnackbar(true);
  };

  const handleCopyPublicLink = () => {
    navigator.clipboard.writeText(publicLink);
    setOpenSnackbar(true);
  };

  return (
    <Dialog open={true} fullWidth>
      <DialogTitle
        color="primary"
        sx={{
          display: "flex",
          alignItems: "center",
          flexWrap: "wrap",
          width: "600px",
        }}
      >
        <ShareIcon size="small" />
        Share file
      </DialogTitle>
      <DialogContent>
        <Typography variant="subtitle1">Permalink</Typography>
        <TextField
          value={permalink}
          fullWidth
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <Tooltip title="Copy to clipboard">
                  <IconButton size="small" onClick={handleCopyPermalink}>
                    <ContentCopyIcon />
                  </IconButton>
                </Tooltip>
              </InputAdornment>
            ),
          }}
          size="small"
          spellCheck={false}
        />
        <Divider />
        <Typography variant="subtitle1">Timed Public Access</Typography>
        {!publicLink ? (
          <Button
            onClick={getPublicLink}
            variant="contained"
            disabled={isGenerating}
          >
            Generate
          </Button>
        ) : (
          <TextField
            value={publicLink}
            fullWidth
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <Tooltip title="Copy to clipboard">
                    <IconButton size="small" onClick={handleCopyPublicLink}>
                      <ContentCopyIcon />
                    </IconButton>
                  </Tooltip>
                </InputAdornment>
              ),
            }}
            size="small"
            spellCheck={false}
          />
        )}
      </DialogContent>
      <DialogActions>
        <Button size="small" onClick={onClose}>
          Close
        </Button>
      </DialogActions>
      <Snackbar
        open={openSnackbar}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
      >
        <Alert onClose={handleSnackbarClose} severity="success">
          Link copied to clipboard!
        </Alert>
      </Snackbar>
    </Dialog>
  );
};

ShareDialog.propTypes = {
  fileId: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default ShareDialog;
