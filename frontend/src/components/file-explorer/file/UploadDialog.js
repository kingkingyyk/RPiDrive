import React from "react";
import PropTypes from "prop-types";
import useMediaQuery from "@mui/material/useMediaQuery";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import IconButton from "@mui/material/IconButton";
import CancelIcon from "@mui/icons-material/Cancel";
import Tooltip from "@mui/material/Tooltip";
import LinearProgress from "@mui/material/LinearProgress";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

import { ajax } from "../../../utils/generics";

const UploadEntry = (props) => {
  const { folderId, file, onCompleted, onCancelled, onFailed } = props;
  const displayName = file.webkitRelativePath
    ? file.webkitRelativePath
    : file.name;
  const uploadUrl = `/drive/ui-api/files/${folderId}/upload`;
  const queued = "Queued";
  const uploading = "Uploading";
  const done = "Done";

  const [progress, setProgress] = React.useState(0);
  const [status, setStatus] = React.useState(queued);
  const [ajaxCtrl, setAjaxCtrl] = React.useState(null);

  React.useEffect(() => {
    if (status !== queued) return;

    const formData = new FormData();
    formData.append("files", file);
    formData.append("paths", file.webkitRelativePath);

    const ctrl = new AbortController();
    setStatus(uploading);
    setAjaxCtrl(ctrl);
    ajax
      .post(uploadUrl, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (event) => {
          const progress = Math.round((event.loaded / event.total) * 100);
          setProgress(progress);
        },
        signal: ctrl.signal,
      })
      .then(() => {
        setStatus(done);
        onCompleted();
      })
      .catch((error) => {
        setStatus(error);
        onFailed();
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file]);

  const handleCancel = () => {
    ajaxCtrl.abort();
    onCancelled();
  };

  return (
    <ListItem
      disablePadding
      secondaryAction={
        status === uploading && (
          <Tooltip title="Cancel">
            <IconButton
              edge="end"
              size="small"
              color="error"
              onClick={() => handleCancel()}
            >
              <CancelIcon />
            </IconButton>
          </Tooltip>
        )
      }
    >
      <ListItemText
        inset
        primary={displayName}
        secondary={
          status === uploading ? (
            <Box sx={{ width: "200px" }}>
              <LinearProgress variant="determinate" value={progress} />
              <Typography variant="caption">{progress} %</Typography>
            </Box>
          ) : (
            <span>{status}</span>
          )
        }
      />
    </ListItem>
  );
};

UploadEntry.propTypes = {
  folderId: PropTypes.string.isRequired,
  file: PropTypes.object.isRequired,
  onCompleted: PropTypes.func.isRequired,
  onCancelled: PropTypes.func.isRequired,
  onFailed: PropTypes.func.isRequired,
};

const UploadDialog = (props) => {
  const { open, fileOnly, folderId, onClose } = props;
  const wideView = useMediaQuery("(min-width:600px)");
  const [entries, setEntries] = React.useState([]);
  const [activeCount, setActiveCount] = React.useState(0);

  React.useEffect(() => {
    setEntries([]);
    setActiveCount(0);
  }, [open]);

  const handleUpload = (event) => {
    if (!event.target.files) return;

    console.log(event.target.files);
    let newEntries = [...entries];
    for (let file of event.target.files) newEntries.push(file);
    setEntries(newEntries);
    setActiveCount((prev) => prev + 1);
  };

  const handleUpdate = () => {
    setActiveCount((prev) => prev - 1);
  };

  return (
    <Dialog open={open} fullScreen={!wideView} fullWidth>
      <DialogTitle
        color="primary"
        sx={{
          display: "flex",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        Upload {fileOnly ? "files" : "folders"}
      </DialogTitle>
      <DialogContent>
        <List dense>
          {entries.map((entry) => (
            <UploadEntry
              folderId={folderId}
              file={entry}
              key={entry.name}
              onCompleted={handleUpdate}
              onCancelled={handleUpdate}
              onFailed={handleUpdate}
            />
          ))}
        </List>
      </DialogContent>
      <DialogActions>
        <Button
          component="label"
          size="small"
          onChange={handleUpload}
          disabled={activeCount > 0}
        >
          Select {fileOnly ? "file(s)" : "folder(s)"}
          {fileOnly ? (
            <input style={{ width: 0, height: 0 }} type="file" multiple />
          ) : (
            <input
              style={{ width: 0, height: 0 }}
              type="file"
              multiple
              webkitdirectory=""
              mozdirectory=""
              msdirectory=""
              odirectory=""
              directory=""
            />
          )}
        </Button>
        <Button size="small" onClick={onClose} disabled={activeCount > 0}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

UploadDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  fileOnly: PropTypes.bool.isRequired,
  folderId: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default UploadDialog;
